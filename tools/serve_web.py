import functools
import http.client
import json
import mimetypes
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

mimetypes.add_type('application/wasm', '.wasm')
mimetypes.add_type('application/javascript', '.js')


class NoCacheHandler(SimpleHTTPRequestHandler):
    """Serve the app with no caching, and proxy ACEsi AI chat on same origin."""

    def end_headers(self):
        self.send_header('Cache-Control',
                         'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def _proxy_ai_chat(self):
        length = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(length) if length else b''
        conn = http.client.HTTPConnection('127.0.0.1', 5000, timeout=90)
        try:
            conn.request(
                'POST', '/api/ai/chat', body=body,
                headers={
                    'Content-Type': 'application/json',
                    'Content-Length': str(len(body)),
                },
            )
            resp = conn.getresponse()
            self.send_response(resp.status)
            self.send_header('Content-Type',
                             resp.getheader('Content-Type') or 'text/event-stream')
            self.end_headers()
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        except Exception as exc:
            payload = ('data: ' + json.dumps({'error': str(exc)}) + '\n\n').encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.end_headers()
            self.wfile.write(payload)
        finally:
            conn.close()

    def do_POST(self):
        if self.path.split('?')[0] == '/api/ai/chat':
            self._proxy_ai_chat()
            return
        super().do_POST()

    def do_OPTIONS(self):
        if self.path.split('?')[0] == '/api/ai/chat':
            self.send_response(204)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            return
        super().do_OPTIONS()


handler = functools.partial(
    NoCacheHandler,
    directory=r'C:\Users\gabri\Documents\LibSyncStudent\build\web',
)

ThreadingHTTPServer(('0.0.0.0', 8080), handler).serve_forever()
