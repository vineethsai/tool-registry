import http.server, socketserver, os
PORT = 8080
class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        http.server.SimpleHTTPRequestHandler.end_headers(self)

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

httpd = socketserver.TCPServer(("0.0.0.0", PORT), CORSHandler) print(f"Serving at port {PORT}") httpd.serve_forever()
