#!/bin/bash

# Check for available port from a list of potential ports
for p in 8080 8081 9000 9001; do
  if ! nc -z localhost $p &>/dev/null; then
    PORT=$p
    echo "Using port $PORT for Postman documentation server."
    break
  fi
done

# If no port was found available, default to a random high port
if [ -z "$PORT" ]; then
  PORT=0  # This will use a random available port
  echo "All standard ports are in use, using a random available port."
fi

# Create a Python script to serve the Postman collection with CORS headers
cat > /tmp/serve_postman.py << EOF
import http.server
import socketserver
import os

PORT = $PORT

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json')
        http.server.SimpleHTTPRequestHandler.end_headers(self)

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

os.chdir('postman')
handler = CORSRequestHandler
httpd = socketserver.TCPServer(("", PORT), handler)

# Get the actual port (useful if we used 0)
actual_port = httpd.server_address[1]
print(f"Serving Postman collection on port {actual_port}")
print("Access the following files:")
print(f"  - Collection: http://localhost:{actual_port}/tool_registry_api_collection.json")
print(f"  - Environment: http://localhost:{actual_port}/tool_registry_environment.json")
print(f"  - Documentation: http://localhost:{actual_port}/README.md")
httpd.serve_forever()
EOF

# Run the server in the background
python3 /tmp/serve_postman.py &

echo "Postman documentation server started."
echo "Use 'ps aux | grep serve_postman.py' and 'kill <PID>' to stop the server when done." 