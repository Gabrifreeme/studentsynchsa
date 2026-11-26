import functools, mimetypes
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

mimetypes.add_type('application/wasm', '.wasm')
mimetypes.add_type('application/javascript', '.js')


class NoCacheHandler(SimpleHTTPRequestHandler):
    """Never let the phone keep an old main.dart.js after a new build."""

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()


handler = functools.partial(
    NoCacheHandler,
    directory=r'C:\Users\gabri\Documents\LibSyncStudent\build\web',
)

ThreadingHTTPServer(('0.0.0.0', 8080), handler).serve_forever()
