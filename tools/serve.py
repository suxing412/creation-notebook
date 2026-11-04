import http.server, functools, sys
H = http.server.SimpleHTTPRequestHandler
H.extensions_map.update({'.mjs': 'text/javascript', '.js': 'text/javascript', '.glb': 'model/gltf-binary',
                         '.webp': 'image/webp', '.json': 'application/json', '.wasm': 'application/wasm'})
root, port = sys.argv[1], int(sys.argv[2])
http.server.ThreadingHTTPServer(('127.0.0.1', port), functools.partial(H, directory=root)).serve_forever()
