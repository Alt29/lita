import http.server
import socketserver

PORT = 8080

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Hello, world!')

# Créer un serveur qui écoute sur le port 8080
with socketserver.TCPServer(("", PORT), SimpleHTTPRequestHandler) as httpd:
    print("Serveur démarré sur le port", PORT)
    # Lancer le serveur et le maintenir en vie
    httpd.serve_forever()
