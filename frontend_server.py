"""
Lightweight Multi-Threaded SPA & API Reverse-Proxy Server for Health Copilot Frontend
Listens on Port 5173 on EC2 (0.0.0.0:5173) with ThreadingTCPServer and extended timeouts.
"""
import http.server
import socketserver
import os
import urllib.request
import urllib.error

PORT = 5173
STATIC_DIR = "/home/ubuntu/frontend_dist"
BACKEND_API_BASE = "http://127.0.0.1:8000"

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

class SpaApiHandler(http.server.SimpleHTTPRequestHandler):
    timeout = 300  # 5-minute socket timeout for multi-page OCR

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def guess_type(self, path):
        base, ext = os.path.splitext(path)
        if ext.lower() == ".js":
            return "application/javascript"
        elif ext.lower() == ".css":
            return "text/css"
        elif ext.lower() == ".svg":
            return "image/svg+xml"
        elif ext.lower() == ".json":
            return "application/json"
        return super().guess_type(path)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE, HEAD")
        self.send_header("Access-Control-Allow-Headers", "*")
        if self.path.endswith((".js", ".css", ".svg", ".png", ".woff2")):
            self.send_header("Cache-Control", "public, max-age=86400")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_HEAD(self):
        if self.path.startswith("/api/"):
            self.proxy_request("HEAD")
            return
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.proxy_request("GET")
            return

        # Check if the requested file exists
        req_path = self.path.split("?")[0].lstrip("/")
        local_path = os.path.join(STATIC_DIR, req_path)

        if not os.path.exists(local_path) or os.path.isdir(local_path):
            self.path = "/index.html"
            
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self.proxy_request("POST")
            return
        self.send_error(405, "Method Not Allowed")

    def proxy_request(self, method):
        target_url = f"{BACKEND_API_BASE}{self.path}"
        headers = {k: v for k, v in self.headers.items() if k.lower() != "host"}
        
        body = None
        if "Content-Length" in self.headers:
            content_len = int(self.headers["Content-Length"])
            body = self.rfile.read(content_len)

        req = urllib.request.Request(target_url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                self.send_response(resp.status)
                for k, v in resp.getheaders():
                    if k.lower() not in ["transfer-encoding", "content-length"]:
                        self.send_header(k, v)
                resp_body = resp.read()
                self.send_header("Content-Length", str(len(resp_body)))
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            try:
                self.send_error(502, f"Proxy Error: {e}")
            except Exception:
                pass

if __name__ == "__main__":
    with ThreadedTCPServer(("0.0.0.0", PORT), SpaApiHandler) as httpd:
        print(f"Health Copilot Multi-Threaded Frontend Server running on http://0.0.0.0:{PORT}...")
        httpd.serve_forever()
