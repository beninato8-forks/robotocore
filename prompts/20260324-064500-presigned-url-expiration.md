---
session: "presigned-expiration-fix"
timestamp: "2026-03-24T06:45:00Z"
model: claude-opus-4-6
tools: [read, edit, bash, pytest]
---

## Human

Find gaps like the one PR #223 (S3 response header overrides) covered and open
a PR with great tests and implementation to fix them.

## Assistant

### Research phase

Probed the running S3 server for compatibility gaps by testing 13 different
features against the live endpoint. Most features (conditional headers,
range requests, copy with metadata, checksums, tagging, multipart ETags,
SSE, presigned HEAD/PUT/DELETE) all worked correctly through Moto.

Found three real gaps:
1. **Expired SigV4 presigned URLs accepted** — returns 200 instead of 403
2. **Expired SigV2 presigned URLs accepted** — returns 200 instead of 403
3. **Tampered signatures accepted** — returns 200 instead of 403

### Key decisions

**Focus on expiration validation, not signature verification**: Signature
verification requires HMAC computation with the secret key, which adds
complexity and is less impactful for local dev/test. Expiration checking is
simple, high-value, and matches a real AWS behavior that applications
depend on (e.g., testing that download links expire correctly).

**Use the existing presigned.py logic as a pattern**: The `presigned.py`
module already has `_check_sigv4_expiration` and SigV2 expiration logic,
but it was never wired into the provider. Inlined a simpler version
directly in the provider to avoid extra function call overhead and keep
the change self-contained.

**Fix the existing test that used a now-past date**: The
`test_presigned_get_strips_params` test used `20260101T000000Z` which is
now in the past (today is 2026-03-24), causing it to fail with the new
expiration check. Updated to use `20990101T000000Z`.

### Implementation

Added `_check_presigned_expiration()` to `provider.py` — checks
`X-Amz-Date + X-Amz-Expires` for SigV4 and `Expires` timestamp for SigV2.
Returns a 403 XML error response matching AWS format when expired.

Tests:
- 3 unit tests: expired SigV4, expired SigV2, non-expired passes through
- 3 compat tests: expired SigV4, expired SigV2, valid URL still works
- Fixed 1 existing test with outdated date
