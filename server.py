# put this at the very top of server.py
import sys, asyncio
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# server.py — FastMCP version
import os
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel, Field

import psycopg
from psycopg.rows import dict_row

from mcp.server.fastmcp import FastMCP  # <-- FastMCP

# -----------------------------
# Config & Template Engine
# -----------------------------
load_dotenv()
DB_DSN = os.getenv("DB_DSN", "postgresql://postgres:postgres@localhost:5432/mcp_logs")
print(DB_DSN)
TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", os.path.join(os.getcwd(), "templates"))

jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

# -----------------------------
# Pydantic Schemas
# -----------------------------
class GetUserLogsInput(BaseModel):
    document_id: str = Field(..., description="User national ID / document number")
    start_date: Optional[str] = Field(None, description="YYYY-MM-DD inclusive")
    end_date: Optional[str] = Field(None, description="YYYY-MM-DD inclusive")
    limit: int = Field(100, ge=1, le=500, description="Max rows to return")

class BuildReportInput(BaseModel):
    document_id: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    template_name: str = Field("report.md.j2", description="Template filename under templates/")

# -----------------------------
# DB Helpers
# -----------------------------
def _as_date(s: Optional[str], default: Optional[datetime] = None) -> Optional[datetime]:
    if not s:
        return default
    return datetime.strptime(s, "%Y-%m-%d")

async def fetch_logs(params: GetUserLogsInput) -> List[Dict[str, Any]]:
    sql = (
        """
        SELECT id, document_id, event_at, channel, action, ip, branch_code, device_id, meta
        FROM logs
        WHERE document_id = %s
          AND event_at >= %s
          AND event_at < %s
        ORDER BY event_at DESC
        LIMIT %s
        """
    )

    start = _as_date(params.start_date, default=(datetime.now() - timedelta(days=30)))
    end = _as_date(params.end_date, default=datetime.now())
    # end is exclusive upper bound -> +1 day at 00:00
    end = (end + timedelta(days=1)) if end else None

    async with await psycopg.AsyncConnection.connect(DB_DSN) as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(sql, (params.document_id, start, end, params.limit))
            rows = await cur.fetchall()
    return rows

# -----------------------------
# FastMCP app & tools
# -----------------------------
app = FastMCP("mcp-logs-reporter")

@app.tool()
async def get_user_logs(
    document_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
) -> dict:
    """
    Fetch logs for a user by document ID with an optional date range and limit.
    Returns JSON-serializable dict: {"count": n, "rows": [...]}
    """
    # Bound/check limit
    if limit < 1: limit = 1
    if limit > 500: limit = 500

    params = GetUserLogsInput(
        document_id=document_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    rows = await fetch_logs(params)
    # Ensure JSON serializable (timestamps -> str)
    def norm(r: Dict[str, Any]) -> Dict[str, Any]:
        rr = dict(r)
        if isinstance(rr.get("event_at"), (datetime,)):
            rr["event_at"] = rr["event_at"].isoformat()
        return rr

    return {"count": len(rows), "rows": [norm(r) for r in rows]}

@app.tool()
async def build_report(
    document_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    template_name: str = "report.md.j2",
) -> str:
    """
    Render a Markdown report for a user using a Jinja2 template.
    Returns a Markdown string.
    """
    rows = await fetch_logs(GetUserLogsInput(
        document_id=document_id,
        start_date=start_date,
        end_date=end_date,
        limit=500,
    ))

    summary = {
        "total": len(rows),
        "by_channel": {},
        "by_action": {},
        "first_event": rows[-1]["event_at"] if rows else None,
        "last_event": rows[0]["event_at"] if rows else None,
        "period": {"start": start_date, "end": end_date},
    }
    for r in rows:
        ch = r["channel"]
        ac = r["action"]
        summary["by_channel"][ch] = summary["by_channel"].get(ch, 0) + 1
        summary["by_action"][ac] = summary["by_action"].get(ac, 0) + 1

    template = jinja_env.get_template(template_name)
    md = template.render(
        document_id=document_id,
        generated_at=datetime.now().isoformat(timespec="seconds") + "Z",
        summary=summary,
        logs=rows,
    )
    return md

if __name__ == "__main__":
    # Ejecuta el servidor MCP por stdio
    app.run()
