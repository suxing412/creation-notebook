"""Read-only static server for runtime load capture (GET/HEAD only, .mjs as JS)."""
import functools, http.server, sys
root, port = sys.argv[1], int(sys.argv[2])
class H(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      '.mjs': 'text/javascript', '.js': 'text/javascript', '.glb': 'model/gltf-binary',
                      '.json': 'application/json', '.webp': 'image/webp', '.woff2': 'font/woff2'}
    def log_message(self, fmt, *args):
        sys.stdout.write('%s\n' % (fmt % args)); sys.stdout.flush()
http.server.ThreadingHTTPServer(('127.0.0.1', port), functools.partial(H, directory=root)).serve_forever()
