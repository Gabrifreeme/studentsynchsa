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

    def _ai_ask(self):
        """Collect ACEsi's stream and return one plain JSON reply."""
        length = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(length) if length else b''
        reply = ''
        error = ''
        conn = http.client.HTTPConnection('127.0.0.1', 5000, timeout=120)
        try:
            conn.request(
                'POST', '/api/ai/chat', body=body,
                headers={
                    'Content-Type': 'application/json',
                    'Content-Length': str(len(body)),
                },
            )
            resp = conn.getresponse()
            for raw in resp:
                line = raw.decode('utf-8', 'replace').strip()
                if not line.startswith('data:'):
                    continue
                payload = line[5:].strip()
                if payload == '[DONE]':
                    break
                data = json.loads(payload)
                if 'token' in data:
                    reply += data['token']
                if 'error' in data:
                    error = data['error']
        except Exception as exc:
            error = str(exc)
        finally:
            conn.close()
        if not reply and not error:
            error = 'ACEsi returned an empty reply'
        result = json.dumps({
            'ok': not bool(error),
            'reply': reply,
            'error': error,
        }).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(result)))
        self.end_headers()
        self.wfile.write(result)

    def do_POST(self):
        path = self.path.split('?')[0]
        if path == '/api/ai/chat':
            self._proxy_ai_chat()
            return
        if path == '/api/ai/ask':
            self._ai_ask()
            return
        super().do_POST()

    def do_OPTIONS(self):
        if self.path.split('?')[0] in ('/api/ai/chat', '/api/ai/ask'):
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
