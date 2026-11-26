from http.server import BaseHTTPRequestHandler, HTTPServer

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'<h1 style="color:#ffa500;font-family:monospace">LibSyncStudent LAN test OK</h1>'
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass

HTTPServer(('0.0.0.0', 8080), H).serve_forever()
