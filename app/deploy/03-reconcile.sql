-- Reconcile overdue deemed approvals per RTPS Act
-- Applications older than 15 days that remained pending due to cron failure
UPDATE applications
SET status = 'DEEMED_APPROVED',
    decided_at = submitted_at + INTERVAL '15 days',
    decided_by = 'RTPS-AUTO'
WHERE status = 'PENDING'
  AND submitted_at < NOW() - INTERVAL '15 days';

