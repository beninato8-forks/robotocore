---
session: "backup-config-gap-ops"
timestamp: "2026-03-20T08:00:00Z"
model: claude-sonnet-4-6
---

## Human

For backup (83.3%, 18 gaps) and config (91.8%, 8 gaps): probe gap operations,
implement Moto stubs for operations that return NotImplemented, and add compat tests.

## Assistant

## Key decisions

**Root cause of most backup 501s**: Discovered that the routing fix needed was in
`moto_bridge.py`, not in Moto itself. Werkzeug's `strict_slashes=False` on a `Rule`
object does not properly handle trailing-slash variants when the rule contains regex
converters (using the custom `_RegexConverter`). AWS boto3 clients append trailing
slashes to many REST paths (e.g. `/backup/plans/{id}/versions/`) but the Werkzeug
rules only had non-trailing-slash versions (e.g. `/backup/plans/{id}/versions`).
The fix: add an explicit trailing-slash variant for every URL rule that doesn't
already end in `/`.

**Operations fixed by routing fix** (were working in Moto, just not routing):
- backup: ListBackupPlanVersions, ListBackupSelections, ExportBackupPlanTemplate,
  GetBackupPlan, GetLegalHold, ListProtectedResourcesByBackupVault,
  ListRecoveryPointsByBackupVault

**start_report_job path parsing bug**: The existing moto implementation was splitting
on `/report-plans/` but the actual AWS URL for StartReportJob is
`POST /audit/report-jobs/{reportPlanName}` — not under `/report-plans/`. Fixed by
changing the split key.

**New stubs added to vendor/moto** (genuinely not implemented):
- backup: list_indexed_recovery_points, list_scan_job_summaries,
  list_restore_access_backup_vaults, get_restore_testing_inferred_metadata,
  get_recovery_point_index_details, update_recovery_point_index_settings
- config: delete_pending_aggregation_request, delete_service_linked_configuration_recorder,
  deliver_config_snapshot, get_organization_custom_rule_policy,
  put_service_linked_configuration_recorder, select_aggregate_resource_config,
  associate_resource_types, disassociate_resource_types

**Test approach**: All 20 new tests (12 backup + 8 config) contact the server and
assert on response keys. Stubs return minimal valid responses (empty lists, empty
strings) — sufficient for behavioral fidelity at this stage.
