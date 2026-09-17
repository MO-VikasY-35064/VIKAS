from dotenv import load_dotenv
result = load_dotenv()

from app import create_app
app = create_app()

import os, socket
print("=== DEBUG ===")
print("load_dotenv() returned:", result)
print("CWD:", os.getcwd())
print("EMAIL_BACKEND:", repr(os.environ.get("EMAIL_BACKEND")))
print("SMTP_HOST:", repr(os.environ.get("SMTP_HOST")))
print("SMTP_PORT:", repr(os.environ.get("SMTP_PORT")))
try:
    ip = socket.gethostbyname(os.environ.get("SMTP_HOST", ""))
    print("DNS resolved smtp.gmail.com ->", ip)
except socket.gaierror as e:
    print("DNS resolution FAILED:", e)
print("=============")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)