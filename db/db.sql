CREATE TABLE IF NOT EXISTS logs (
  id BIGSERIAL PRIMARY KEY,
  document_id VARCHAR(40) NOT NULL,
  event_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  channel VARCHAR(32) NOT NULL, -- web, mobile, teller, kiosk
  action VARCHAR(64) NOT NULL, -- login, logout, transfer, failed_otp, etc.
  ip INET,
  branch_code VARCHAR(16),
  device_id VARCHAR(64),
  meta JSONB
);


-- Sample data
-- Usuario 12345678
INSERT INTO logs (document_id, event_at, channel, action, ip, branch_code, device_id, meta) VALUES
('12345678', now() - interval '2 days', 'web', 'login', '200.1.2.3', NULL, 'web-abc', '{"ok":true}'),
('12345678', now() - interval '1 days', 'mobile', 'failed_otp', '200.1.2.3', NULL, 'ios-xyz', '{"retries":1}'),
('12345678', now() - interval '1 hours', 'teller', 'identity_check', '10.0.0.5', 'BR001', 'desk-22', '{"match":0.62}')

-- Usuario 87654321
('87654321', now() - interval '5 days', 'mobile', 'login', '201.44.3.22', NULL, 'android-001', '{"ok":true}'),
('87654321', now() - interval '4 days', 'mobile', 'transfer', '201.44.3.22', NULL, 'android-001', '{"amount":500000,"currency":"COP"}'),
('87654321', now() - interval '3 days', 'web', 'failed_otp', '201.44.3.22', NULL, 'web-xyz', '{"retries":3}'),
('87654321', now() - interval '2 days', 'api', 'account_update', '201.44.3.22', NULL, 'api-123', '{"field":"email"}'),

-- Usuario 44556677
('44556677', now() - interval '7 days', 'kiosk', 'identity_check', '10.10.10.5', 'BR002', 'kiosk-45', '{"match":0.88}'),
('44556677', now() - interval '6 days', 'kiosk', 'failed_otp', '10.10.10.5', 'BR002', 'kiosk-45', '{"retries":2}'),
('44556677', now() - interval '3 days', 'teller', 'transfer', '10.10.10.10', 'BR002', 'desk-11', '{"amount":1500000}'),
('44556677', now() - interval '1 days', 'mobile', 'logout', '190.10.10.20', NULL, 'ios-44', '{"session_duration":800}'),

-- Usuario 99887766
('99887766', now() - interval '10 days', 'web', 'login', '180.2.2.2', NULL, 'web-555', '{"ok":true}'),
('99887766', now() - interval '9 days', 'web', 'failed_otp', '180.2.2.2', NULL, 'web-555', '{"retries":2}'),
('99887766', now() - interval '8 days', 'api', 'token_refresh', '180.2.2.2', NULL, 'api-444', '{"token_age":3600}'),
('99887766', now() - interval '1 days', 'mobile', 'transfer', '180.2.2.2', NULL, 'android-777', '{"amount":320000,"currency":"COP"}'),

-- Usuario 11223344
('11223344', now() - interval '2 days', 'teller', 'identity_check', '172.16.1.5', 'BR003', 'desk-02', '{"match":0.72}'),
('11223344', now() - interval '1 days', 'mobile', 'login', '172.16.1.6', NULL, 'ios-222', '{"ok":true}'),
('11223344', now() - interval '6 hours', 'mobile', 'transfer', '172.16.1.6', NULL, 'ios-222', '{"amount":900000,"currency":"COP"}'),
('11223344', now() - interval '3 hours', 'web', 'logout', '172.16.1.6', NULL, 'web-222', '{"session_duration":600}');