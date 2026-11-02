# 010 independent JavaScript audit

Date: 2026-11-02. Inspector: independent child `audit_reader_state`.

Run:

```sh
node web-revisions/010/review/audit/test-reader.cjs
node web-revisions/010/review/audit/test-schema.cjs
```

`test-reader.cjs` executes the real production scripts in a controlled mock DOM, Image decoding, fetch and history environment. It is not browser/GPU/mobile validation. It checks race suppression, 3-image all-or-nothing loading, metadata refetch, decode failure, history exception containment, Back failure/retry intent, and unavailable cold initialization.

COLD-01 initially reproduced an unearned `committed=slot` claim when no initial image was available. Parent changed initial state to null and made pending/error copy depend on committed evidence. The regression now checks no selected variant before proof and successful retry restoration.

`test-schema.cjs` checks the metadata allowlist and rejects unsafe paths, missing required views and invalid route values. META-01 initially identified accepted empty strings in alt/caption/fact text. Parent hardened all four to trimmed nonempty strings; the regression rejects each blank field independently.

The JSON reports bind outcomes to the tested source hashes where supplied. Any later source change needs rerunning. No screenshots, visual fidelity, image identity, manufacturing or true-browser claims are covered here.

## Resource deadline hardening

Parent-authorized edit to app.js adds a 15,000 ms deadline **per resource stage**: metadata fetch plus JSON decoding/validation, then each image load plus decode. Thus a sequential cold request can take nearly 30 seconds (metadata then images), not a promised 15-second total. A settled success/failure clears its timer. Timeout unlocks the normal Retry path, releases the failed metadata cache, and ignores late work resolution. It does not claim to cancel the browser's underlying network operation.

Four additional actual-app mock tests use manually controlled timers (no 15-second real wait): never-settling fetch, never-settling JSON body, hanging third image preserving the prior full trio then retrying, and never-settling image decode. Late fetch/image success cannot replace the newer successful state. The full reader suite now has 12 groups; schema suite has 6 groups. Browser timer throttling/network cancellation are not verified by these mocks.
