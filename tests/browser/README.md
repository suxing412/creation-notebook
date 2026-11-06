# Luoyang browser verification

The PR workflow builds the same slimmed artifact as the Pages workflow, then tests it with Chromium on an ephemeral GitHub runner. It uses a read-only token, persists no checkout credentials, consumes no secrets, and does not deploy.

Coverage: first real WebGL render of the complete placed city; unchanged model membership and no scene rebuild or new model requests across all 41 planning zones and complete camera framing; animated and reduced-motion navigation; left drag, wheel, WASD, key release and focus loss; ground focus and compass; rapid choices; delayed research requests cancelled by manual controls and by zone selection; failed initial model load with same-page retry; independent research return; browser history return; left sidebar at desktop and 375px touch layout and orientation changes. Reports include screenshots, tested revisions, errors and history-cache evidence. BFCache is reported as restored only when the same document instance receives `pageshow.persisted`; a normal reload is recorded separately.

This is Chromium with SwiftShader and mobile emulation. Physical phones, hardware GPU performance and production deployment are separate checks. No screenshot, model load, camera state or app module is mocked. Recovery tests delay or fail actual model requests, then retry them. The rendered node list is read from real instantiated meshes; independent research assets are excluded from the city.

To run in an environment that permits browser/server startup, install the pinned package lock and Chromium, build `_site` using `lab/tools/assemble_site.py`, then run `npm test` in this directory. Do not bypass environment restrictions to run locally.
