"""Read-only server that serves files exactly as committed at a git revision
(`git cat-file blob <rev>:docs/<path>`), so line endings match the repository / Pages
rather than the Windows autocrlf checkout.  GET/HEAD only."""
import http.server, mimetypes, subprocess, sys, urllib.parse
repo, rev, port = sys.argv[1], sys.argv[2], int(sys.argv[3])
TYPES = {'.mjs': 'text/javascript', '.js': 'text/javascript', '.glb': 'model/gltf-binary', '.json': 'application/json',
         '.webp': 'image/webp', '.png': 'image/png', '.css': 'text/css', '.html': 'text/html; charset=utf-8',
         '.woff2': 'font/woff2', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.md': 'text/plain; charset=utf-8'}
class H(http.server.BaseHTTPRequestHandler):
    def _blob(self):
        p = urllib.parse.unquote(urllib.parse.urlparse(self.path).path).lstrip('/')
        if p == '' or p.endswith('/'):
            p += 'index.html'
        r = subprocess.run(['git', '-C', repo, 'cat-file', 'blob', f'{rev}:docs/{p}'], capture_output=True)
        if r.returncode != 0:
            # directory without trailing slash
            r2 = subprocess.run(['git', '-C', repo, 'cat-file', '-t', f'{rev}:docs/{p}'], capture_output=True)
            if r2.stdout.strip() == b'tree':
                self.send_response(301); self.send_header('Location', '/' + p + '/'); self.end_headers(); return None, None
            self.send_error(404); return None, None
        ext = '.' + p.rsplit('.', 1)[-1] if '.' in p.rsplit('/', 1)[-1] else ''
        return r.stdout, TYPES.get(ext, mimetypes.guess_type(p)[0] or 'application/octet-stream')
    def do_GET(self):
        body, ctype = self._blob()
        if body is None: return
        self.send_response(200); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def do_HEAD(self):
        body, ctype = self._blob()
        if body is None: return
        self.send_response(200); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(body))); self.end_headers()
    def log_message(self, fmt, *args):
        sys.stdout.write('%s\n' % (fmt % args)); sys.stdout.flush()
http.server.ThreadingHTTPServer(('127.0.0.1', port), H).serve_forever()
