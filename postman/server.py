import http.server
import socketserver
import os

# Get port from environment variable with fallback to 8080
PORT = int(os.environ.get("PORT", 8080))
DESCRIPTION = os.environ.get("SERVER_DESCRIPTION", "Postman Collection with CRUD and Cross-Entity Tests")

class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        http.server.SimpleHTTPRequestHandler.end_headers(self)

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

print(f"\n{DESCRIPTION}")
print(f"Serving Postman files on port {PORT}")
print("Available files:")
print(f"  - Collection: http://localhost:{PORT}/tool_registry_api_collection.json")
print(f"  - Environment: http://localhost:{PORT}/tool_registry_environment.json")
print(f"  - Documentation: http://localhost:{PORT}/README.md")
print("\nPress Ctrl+C to stop the server\n")

httpd = socketserver.TCPServer(("0.0.0.0", PORT), CORSHandler)
httpd.serve_forever()
