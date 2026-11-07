# GLB audit contract

Run `python -I lab/tools/build_assets.py --check` before publishing. This command
writes generated `lab/data` and thumbnail files; use an isolated checkout.
Run focused regressions with `python -B -I tests/test_glb_audit.py`.

Raw GLBs use Python. `EXT_meshopt_compression` additionally requires an installed
Node.js runtime and the existing `docs/vendor/meshopt_decoder.module.js`.
The checker decodes each compressed buffer view before reading accessors, while
reporting the original transport bytes and SHA-256. It does not install tools,
fetch external buffers/images, rewrite a model, or substitute fallback data.
Missing dependencies, malformed streams, unsupported required extensions and
invalid geometry bounds are fatal; the CLI exits nonzero and omits completed
geometry statistics. Existing quality issues, including C17 degenerate triangles,
remain warnings and are not repaired by this tool.

Input limits include 64 MiB per GLB, 8 MiB JSON, 128 MiB decoded views, 16 million
accessor scalar values and bounded scene traversal. The decoder subprocess has a
30 second timeout. These are resource guards, not a complete process sandbox or
a total audit-time/memory guarantee.

This is an asset statistics auditor, not a full glTF conformance validator. Sparse
accessors, required extensions other than Meshopt and non-float POSITION inputs
are unsupported. Material/image/animation semantics and all optional attribute
values are not exhaustively validated. The runtime renderer has its own scope.

Cache keys bind current input content and the auditor/bridge/decoder sources.
Malformed summary structures are rebuilt. Compressed files are always decoded
again, including on warm runs. Raw summaries remain local performance hints:
well-typed altered statistics are not authenticated. CI explicitly discards the
cache before the full asset gate. Focused tests use a synthetic triangle and
fault injection confined to temporary directories, including a real timeout.

This tool change does not grant model placement, budget exceptions, lock changes
or LY-010 city admission.
