---
role: assistant
timestamp: 2026-03-26T06:01:48Z
session: werkzeug-raw-body-data-override
sequence: 1
---

# Follow-up: WerkzeugRawBodyRequest data/get_data overrides

## Human

Review PR #226 (S3 form-urlencoded raw upload fix by @Unlearn) and improve it
if possible. Open a new PR for any improvements.

## Assistant

## Key decisions

**Gap identified**: PR #226 correctly overrides `form` and `files` to raise
`AttributeError` (causing `hasattr()` to return `False`, preventing Moto from
overwriting the body with form-field contents). However, the `data` property
and `get_data()` method were left as Werkzeug defaults. For
`application/x-www-form-urlencoded`, Werkzeug's native `data` property returns
`b""` because the stream is consumed by form parsing. If any code path uses
`request.data` instead of `request.body` — including Moto's own Flask fallback
in `setup_class` (`self.body = request.data`) and the `normalize_request` path
used by `parse_parameters` — it would silently receive an empty body.

**Fix**: Override `data` (property) and `get_data()` to return `self.body`.
This makes `WerkzeugRawBodyRequest` fully self-consistent: all body-access
paths return the same raw bytes regardless of which Moto code path is taken.

**Docstring improvement**: Expanded the class docstring to explain:
- Both Moto body-access paths (Boto vs Flask fallback)
- Why `raise AttributeError` from a property causes `hasattr()` to return False
- How `data`/`get_data()` provide belt-and-suspenders coverage

**Test improvement**: Extended the existing unit test to assert that both
`werkzeug_request.data` and `werkzeug_request.get_data()` return the raw body,
and that `files` also raises `AttributeError` (in addition to `form`).

**Scope**: No behavior change for the passing tests in PR #226. The S3
path already worked because `setup_class` prefers the `body` attribute. The
`data`/`get_data()` fix is defensive — it guards against future Moto changes
and any current code paths not exercised by the existing tests.
