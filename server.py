import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class ConferenceHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; "
            "script-src 'self'; connect-src 'self'; form-action 'self' https://formsubmit.co; frame-ancestors 'none'",
        )
        super().end_headers()

    def do_GET(self):
        public_paths = {
            "/", "/index.html", "/registration.html", "/thank-you",
            "/styles.css", "/app.js",
            "/assets/world/diabetes-in-focus-transparent.png",
            "/assets/asl/WhatsApp%20Image%202026-10-13%20at%204.04.34%20PM.jpeg",
            "/assets/topics/cardiovascular.jpeg",
            "/assets/topics/kidney.jpeg",
            "/assets/topics/preventing-complications.jpeg",
            "/assets/topics/insulin-therapy.jpeg",
            "/assets/topics/sglt2-inhibitors.jpeg",
            "/assets/topics/glp1-agonists.jpeg",
            "/assets/topics/new-medications.jpeg",
            "/assets/topics/dyslipidemia.jpeg",
            "/assets/topics/hypertension.jpeg",
            "/assets/topics/diabetic-foot.jpeg",
            "/assets/topics/eye-health.jpeg",
            "/assets/topics/obesity.jpeg",
            "/assets/topics/diabetes-prevention.jpeg",
            "/assets/topics/future-care.jpeg",
            "/assets/topics/diabetes-2026.jpeg",
            "/assets/lo2/s.png",
            "/assets/lo2/n-cropped.png",
            "/assets/wdd-logo/WhatsApp%20Image%202026-10-13%20at%203.55.57%20PM.jpeg",
        }
        if self.path.partition("?")[0] not in public_paths:
            self.send_error(404)
            return
        if self.path.partition("?")[0] == "/thank-you":
            self.path = "/thank-you.html" + self.path[len("/thank-you"):]
        super().do_GET()

    def log_message(self, format, *args):
        super().log_message(format, *args)


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), ConferenceHandler)
    print(f"World Diabetes Day static site running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()