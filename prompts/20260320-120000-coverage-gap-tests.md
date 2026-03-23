---
role: user
timestamp: 2026-03-20T12:00:00Z
session: coverage-gaps-batch3
sequence: 1
---

# Prompt

Continue closing compat coverage gaps. The session picked up at 93.1% coverage.
Work done:
1. Probed ~40 operations across 20+ services to find which work on live server
2. Added 35 new compat tests covering gap operations in 14 services
3. Fixed compat_coverage.py to handle AWS acronyms (ACLs, CNAMEs, etc.) with
   case-insensitive comparison

## Operations verified working and tested

- neptune: RemoveRoleFromDBCluster, ResetDBClusterParameterGroup, ResetDBParameterGroup
- eks: DisassociateAccessPolicy, UpdateNodegroupVersion, UpdatePodIdentityAssociation  
- cloudformation: EstimateTemplateCost, ListGeneratedTemplates, DescribeGeneratedTemplate, ListResourceScanResources
- xray: UpdateIndexingRule
- rekognition: DistributeDatasetEntries
- logs: CancelImportTask, CreateImportTask
- rds: RestoreDBClusterFromS3, RestoreDBInstanceFromS3
- s3: RenameObject, SelectObjectContent
- lambda: CheckpointDurableExecution, GetDurableExecutionState, SendDurableExecutionCallback*
- workspaces: DeleteConnectClientAddIn, UpdateConnectClientAddIn
- mediapackage: RotateIngestEndpointCredentials
- organizations: Responsibility transfer ops (4), CreateGovCloudAccount
- transcribe: StartMedicalScribeJob, UpdateCallAnalyticsCategory, UpdateMedicalVocabulary

## Key finding

compat_coverage.py was doing case-sensitive comparison of PascalCase operation names,
causing false negatives for operations with acronyms (ListWebACLs shown as missing even
though list_web_acls was tested). Fixed by adding lowercase set comparison.

## Coverage delta

93.1% → 93.5% (8725/9336 tested)
