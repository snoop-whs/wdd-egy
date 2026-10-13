import json
import os
import re
import smtplib
import sqlite3
import ssl
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("WDD_DATABASE", ROOT / "var" / "registrations.sqlite3"))
CONTACT_EMAIL = "wdd-egy@elmawy.com"
MAX_BODY_BYTES = 16_384
RATE_WINDOW_SECONDS = 600
RATE_LIMIT = 5
RATE_ATTEMPTS = {}
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
SPONSOR_INTERESTS = {
    "Pop-up Display",
    "Pop-up Display + Scientific Symposium",
    "Exhibition Booth",
    "Exhibition Booth + Scientific Symposium",
    "Other",
}


def initialize_database():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    try:
        DATABASE.parent.chmod(0o700)
    except OSError:
        pass
    with sqlite3.connect(DATABASE) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL CHECK (kind IN ('attendee', 'sponsor')),
                data_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS attendee_email_claims (
                normalized_email TEXT PRIMARY KEY
            )"""
        )
        attendees = connection.execute(
            "SELECT data_json FROM submissions WHERE kind = 'attendee'"
        ).fetchall()
        for (data_json,) in attendees:
            data = json.loads(data_json)
            email = data.get("email")
            if isinstance(email, str) and email.strip():
                connection.execute(
                    "INSERT OR IGNORE INTO attendee_email_claims (normalized_email) VALUES (?)",
                    (email.strip().casefold(),),
                )
    try:
        DATABASE.chmod(0o600)
    except OSError:
        pass


def validate_submission(payload):
    kind = payload.get("kind")
    if kind not in {"attendee", "sponsor"}:
        return None, {"kind": "Choose a valid registration type."}

    fields = (
        {
            "fullName": ("Full Name", 120),
            "specialty": ("Medical Specialty", 120),
            "role": ("Job Title", 120),
            "organization": ("Hospital Organization", 160),
            "email": ("Email address", 254),
            "phone": ("Mobile Number", 40),
        }
        if kind == "attendee"
        else {
            "company": ("Company or organization name", 160),
            "contactPerson": ("Contact person", 120),
            "title": ("Professional title", 120),
            "email": ("Business email", 254),
            "phone": ("Mobile Number", 40),
            "interest": ("Sponsorship interest", 100),
            "message": ("Additional message", 2000),
        }
    )
    errors = {}
    cleaned = {}
    for key, (label, limit) in fields.items():
        value = payload.get(key, "")
        if not isinstance(value, str):
            value = ""
        value = value.strip()
        if len(value) > limit:
            errors[key] = f"{label} must be {limit} characters or fewer."
        elif key != "message" and not value:
            errors[key] = f"Enter your {label.lower()}."
        else:
            cleaned[key] = value

    if cleaned.get("email"):
        cleaned["email"] = cleaned["email"].casefold()
        if not EMAIL_PATTERN.fullmatch(cleaned["email"]):
            errors["email"] = "Enter a valid email address."
    if cleaned.get("phone") and len(re.sub(r"[^0-9]", "", cleaned["phone"])) < 7:
        errors["phone"] = "Enter a phone number with at least 7 digits."
    if kind == "sponsor" and cleaned.get("interest") not in SPONSOR_INTERESTS:
        errors["interest"] = "Choose a valid sponsorship interest."
    if payload.get("privacyAccepted") is not True:
        errors["privacyAccepted"] = "Please confirm the privacy notice to continue."

    if errors:
        return None, errors
    return (kind, cleaned), {}


def send_notifications(kind, data):
    host = os.environ.get("SMTP_HOST")
    sender = os.environ.get("SMTP_FROM")
    if not host or not sender:
        return "not_configured"

    try:
        subject = "World Diabetes Day 2026 attendee registration" if kind == "attendee" else "World Diabetes Day 2026 sponsorship inquiry"
        lines = [f"World Diabetes Day – Diabetes in Focus | {kind.title()} submission", ""]
        lines.extend(f"{key}: {value}" for key, value in data.items() if value)
        organizer_message = EmailMessage()
        organizer_message["Subject"] = subject
        organizer_message["From"] = sender
        organizer_message["To"] = CONTACT_EMAIL
        organizer_message.set_content("\n".join(lines))

        confirmation = EmailMessage()
        confirmation["Subject"] = "We received your World Diabetes Day 2026 submission"
        confirmation["From"] = sender
        confirmation["To"] = data["email"]
        confirmation.set_content(
            "Thank you. Your submission to World Diabetes Day – Diabetes in Focus has been received. "
            "The conference team will follow up using the contact details you provided.\n\n"
            "Conference date: 15 November 2026\n"
            "Venue: Semiramis InterContinental Cairo\n"
            f"Contact: {CONTACT_EMAIL}"
        )
    except (TypeError, ValueError):
        return "failed"

    try:
        port = int(os.environ.get("SMTP_PORT", "587"))
        username = os.environ.get("SMTP_USERNAME")
        password = os.environ.get("SMTP_PASSWORD")
        timeout = 12
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=timeout, context=ssl.create_default_context()) as server:
                if username:
                    server.login(username, password or "")
                server.send_message(organizer_message)
                server.send_message(confirmation)
        else:
            with smtplib.SMTP(host, port, timeout=timeout) as server:
                server.ehlo()
                if os.environ.get("SMTP_STARTTLS", "true").lower() != "false":
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                if username:
                    server.login(username, password or "")
                server.send_message(organizer_message)
                server.send_message(confirmation)
    except (OSError, smtplib.SMTPException, ValueError):
        return "failed"
    return "sent"


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
            "script-src 'self'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'",
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

    def do_POST(self):
        if self.path != "/api/registrations":
            self.send_error(404)
            return

        address = self.client_address[0]
        now = time.monotonic()
        attempts = [stamp for stamp in RATE_ATTEMPTS.get(address, []) if now - stamp < RATE_WINDOW_SECONDS]
        if len(attempts) >= RATE_LIMIT:
            self.send_json(429, {"error": "Too many attempts. Please try again in a few minutes."})
            return
        RATE_ATTEMPTS[address] = attempts + [now]

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY_BYTES:
            self.send_json(413, {"error": "The submission could not be processed. Check the form and try again."})
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_json(400, {"error": "The submission could not be read. Check the form and try again."})
            return
        if not isinstance(payload, dict):
            self.send_json(400, {"error": "Check the form fields and try again."})
            return
        if payload.get("website"):
            self.send_json(400, {"error": "Check the form fields and try again."})
            return

        result, errors = validate_submission(payload)
        if errors:
            self.send_json(422, {"error": "Please correct the highlighted fields.", "fields": errors})
            return

        kind, data = result
        created_at = datetime.now(timezone.utc).isoformat()
        duplicate_attendee = False
        try:
            with sqlite3.connect(DATABASE, timeout=10) as connection:
                if kind == "attendee":
                    claim = connection.execute(
                        "INSERT OR IGNORE INTO attendee_email_claims (normalized_email) VALUES (?)",
                        (data["email"],),
                    )
                    duplicate_attendee = claim.rowcount == 0
                if not duplicate_attendee:
                    connection.execute(
                        "INSERT INTO submissions (kind, data_json, created_at) VALUES (?, ?, ?)",
                        (kind, json.dumps(data, ensure_ascii=False), created_at),
                    )
        except sqlite3.Error:
            self.send_json(503, {"error": "Registration is temporarily unavailable. Please try again later."})
            return
        if duplicate_attendee:
            self.send_json(409, {
                "code": "duplicate_attendee",
                "error": "An attendee registration with this email already exists. If you need to update your registration, please contact the conference team.",
            })
            return
        email_status = send_notifications(kind, data)
        self.send_json(201, {"accepted": True, "emailStatus": email_status})

    def send_json(self, status, body):
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        super().log_message(format, *args)


if __name__ == "__main__":
    initialize_database()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), ConferenceHandler)
    print(f"World Diabetes Day registration running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()