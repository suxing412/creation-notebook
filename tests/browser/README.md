# Luoyang browser verification

The PR workflow builds the same slimmed artifact as the Pages workflow, then tests it with Chromium on an ephemeral GitHub runner. It uses a read-only token, persists no checkout credentials, consumes no secrets, and does not deploy.

Coverage: first real WebGL render; all 41 planning zones and complete camera framing; animated and reduced-motion navigation; left drag, wheel, WASD, key release and focus loss; ground focus and compass; rapid choices; delayed/failed model requests; independent research return; browser history return; 375px touch layout and orientation changes. Reports include screenshots, tested revisions, errors and history-cache evidence. BFCache is reported as restored only when the same document instance receives `pageshow.persisted`; a normal reload is recorded separately.

This is Chromium with SwiftShader and mobile emulation. Physical phones, hardware GPU performance and production deployment are separate checks. No screenshot, model load, camera state or app module is mocked. Two dedicated recovery tests delay or fail an actual model request, then retry it.

To run in an environment that permits browser/server startup, install the pinned package lock and Chromium, build `_site` using `lab/tools/assemble_site.py`, then run `npm test` in this directory. Do not bypass environment restrictions to run locally.
