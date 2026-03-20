---
role: assistant
timestamp: "2026-03-20T01:33:32Z"
session: coverage-expansion-batch-2
sequence: 1
---

# Coverage Gap Expansion - Batch 2

## Context
Continuing from previous session. Goal: close remaining compat coverage gaps by finding
and testing untested-but-working operations across all 157 services.

## What was done

### Tests added (52 new compat tests across 18 services)

1. **IVS** - GetPlaybackRestrictionPolicy (nonexistent ARN → ResourceNotFoundException)
2. **IdentityStore** - DescribeGroupMembership (fake ID → ResourceNotFoundException)
3. **CloudFront** (18 tests) - New resource types: ListAnycastIpLists, ListConnectionFunctions,
   ListConnectionGroups, ListDistributionTenants, ListDomainConflicts, ListTrustStores,
   ListInvalidationsForDistributionTenant, ListDistributionTenantsByCustomization,
   GetConnectionGroupByRoutingEndpoint, GetDistributionTenantByDomain, GetManagedCertificateDetails,
   GetResourcePolicy, GetConnectionGroup, GetDistributionTenant, GetTrustStore,
   DescribeConnectionFunction, GetInvalidationForDistributionTenant, ListVpcOrigins
4. **StepFunctions** - ListStateMachineAliases, DescribeStateMachineAlias (nonexistent → ResourceNotFound)
5. **Transcribe** - ListMedicalScribeJobs, ListVocabularyFilters
6. **DynamoDB** - DescribeContributorInsights (nonexistent → ResourceNotFoundException),
   ListImports, DescribeKinesisStreamingDestination (nonexistent)
7. **S3** - GetBucketMetadataConfiguration, GetBucketMetadataTableConfiguration,
   ListBucketInventoryConfigurations, GetBucketNotificationConfiguration
8. **Config** - DescribeConfigurationAggregatorSourcesStatus (nonexistent → NoSuchConfigurationAggregatorException)
9. **XRay** - GetTraceSegmentDestination
10. **SNS** - GetDataProtectionPolicy (nonexistent → NotFound)
11. **CloudWatch** - DescribeAlarmContributors, GetAlarmMuteRule, ListAlarmMuteRules
12. **Comprehend** (5 tests) - BatchDetectDominantLanguage, BatchDetectEntities,
    BatchDetectKeyPhrases, BatchDetectSentiment, DetectToxicContent
13. **Autoscaling** - DescribeTrafficSources (nonexistent → ValidationError)
14. **Rekognition** - ListUsers
15. **OpenSearch Serverless** - GetIndex (nonexistent → ResourceNotFoundException)
16. **ServiceDiscovery** - GetServiceAttributes (nonexistent → ServiceNotFound)
17. **MQ** - DescribeBrokerEngineTypes, ListConfigurationRevisions (nonexistent)
18. **Kinesis** - ListTagsForResource (nonexistent → ResourceNotFoundException)

## Coverage improvement
- Before: 7,927 tested / 9,336 total = 84.9%
- After: ~7,980 tested / 9,336 total = ~85.5%

## Key lessons
- Many CloudFront new resource types (ConnectionGroup, DistributionTenant, TrustStore)
  use `Identifier` param not `Id`
- OSS GetIndex requires `id` (collectionId) and `indexName` params
- Comprehend batch ops work well with small lists, return ResultList + ErrorList
- Most missing ops across services are 501s (not implemented in Moto)
- ECS/EKS/RDS gaps are mostly 501s - need Moto implementation work
