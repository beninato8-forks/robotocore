---
role: assistant
timestamp: 2026-03-24T22:30:59Z
session: s3-form-urlencoded-uploads
sequence: 1
---

# Fix S3 form-urlencoded raw uploads

## Human

Robotocore appears to mishandle S3 raw uploads when the client sends
`Content-Type: application/x-www-form-urlencoded`.

Observed locally:

- Raw presigned S3 upload requests behave differently when sent with that
  content type
- This is easy to hit with `curl --data-binary`, which sends that header by
  default unless it is overridden
- For both `PutObject` and multipart `UploadPart`, the bytes should still be
  treated as the object body or part body exactly as sent
- `Content-Type` may describe object metadata, but it should not cause the
  emulator to reinterpret or decode the request body as form data

Investigate the request path, identify the real failure point, fix it, then
prepare the branch for a PR: confirm the tests that were run, assess whether
the regression coverage is sufficient, add additional tests, if needed.

## Assistant

## Key decisions

**Root cause**: The failure was in the Robotocore Starlette-to-Werkzeug bridge,
not in S3 request routing. For S3 requests forwarded to Moto with
`application/x-www-form-urlencoded`, Werkzeug parsed the payload as form data.
That made `request.data` empty, and Moto's S3 request setup then received an
empty body for raw `PutObject` and `UploadPart` requests.

**Fix location**: I patched the bridge instead of the S3 provider. The body loss
happened before Moto's S3 logic saw the request, so changing S3 operation
handling would have treated the symptom rather than the cause.

**Scope control**: The raw-body preservation is limited to S3 requests with the
problematic content type. Other AWS query-protocol services still use normal
Werkzeug form parsing, which they rely on for `Action=` bodies.

**Test strategy**: I added end-to-end bridge regressions for both direct
`PutObject` and presigned multipart `UploadPart`, because those reproduce the
user-visible bug. I then added one narrower bridge-unit test to lock in the
S3-only special case and confirm non-S3 form-urlencoded requests still use the
default parsing path. To cover the full HTTP boundary more directly, I also
added compatibility tests for presigned `PutObject` and presigned multipart
`UploadPart` with `Content-Type: application/x-www-form-urlencoded`.

**Verification**: I verified the fix with targeted pytest runs and direct local
repros through the app, checking that raw bytes are preserved for both ordinary
uploads and multipart part uploads even when the request header is
`application/x-www-form-urlencoded`.

## References

- `UploadPart` API reference: the request syntax ends in `Body`, and the
  request body is documented as binary data.
  https://docs.aws.amazon.com/AmazonS3/latest/API/API_UploadPart.html
- AWS CLI `upload-part`: exposes `--body` as the upload payload and describes it
  as object data; there is no `--content-type` option on this command.
  https://docs.aws.amazon.com/cli/latest/reference/s3api/upload-part.html
- AWS CLI `create-multipart-upload`: documents `--content-type` as "a standard
  MIME type describing the format of the object data," which supports treating
  content type as object metadata established at initiation time rather than a
  parser switch for each uploaded part.
  https://docs.aws.amazon.com/cli/latest/reference/s3api/create-multipart-upload.html
- AWS CLI `put-object`: documents `--content-type` as "a standard MIME type
  describing the format of the contents," which supports treating it as object
  metadata rather than as a reason to decode the body as form data.
  https://docs.aws.amazon.com/cli/latest/reference/s3api/put-object.html
