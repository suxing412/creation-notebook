"""Local dev server for the lab: correct MIME types and no caching, so a refresh always shows the latest edit.

Usage (from anywhere):  python -I lab/tools/serve.py [port]
Serves the repo root, so the lab lives at http://localhost:<port>/lab/ and can reference ../docs/ assets.
"""
import http.server, functools, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8780


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      '.mjs': 'text/javascript', '.js': 'text/javascript', '.glb': 'model/gltf-binary',
                      '.webp': 'image/webp', '.json': 'application/json', '.wasm': 'application/wasm'}

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def log_message(self, *a):
        pass


print(f'serving {ROOT} at http://localhost:{PORT}/lab/', flush=True)
http.server.ThreadingHTTPServer(('127.0.0.1', PORT), functools.partial(Handler, directory=ROOT)).serve_forever()
