"""Serve the local website with browser-compatible module and font MIME types."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import json
import threading
import time


class PreviewHandler(SimpleHTTPRequestHandler):
    request_report = None
    report_lock = threading.Lock()
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        '.mjs': 'text/javascript',
        '.js': 'text/javascript',
        '.woff2': 'font/woff2',
        '.webp': 'image/webp',
        '.glb': 'model/gltf-binary',
    }

    def send_response(self, code, message=None):
        self.response_code = code
        self.response_bytes = 0
        super().send_response(code, message)

    def send_header(self, keyword, value):
        if keyword.lower() == 'content-length':
            self.response_bytes = int(value)
        super().send_header(keyword, value)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        if self.request_report:
            record = {
                'time': time.time(),
                'method': self.command,
                'path': self.path,
                'status': self.response_code,
                'body_bytes': self.response_bytes if self.command != 'HEAD' else 0,
                'header_bytes': sum(map(len, self._headers_buffer)) + 2,
            }
            with self.report_lock:
                with self.request_report.open('a', encoding='utf-8') as report:
                    report.write(json.dumps(record, ensure_ascii=False) + '\n')
        super().end_headers()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--report', type=Path, help='Append served response sizes to this JSONL file.')
    args = parser.parse_args()
    PreviewHandler.request_report = args.report
    site = Path(__file__).resolve().parents[2] / 'docs'
    handler = partial(PreviewHandler, directory=str(site))
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    print(f'Preview http://127.0.0.1:{args.port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
