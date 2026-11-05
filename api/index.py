import os
import sys

# Ensure root directory is in Python path so app, config, models can be imported
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app as flask_app


class VercelPathFixMiddleware:
    """
    WSGI middleware to fix PATH_INFO on Vercel Serverless Functions.
    Vercel rewrites requests to /api/index.py, which overwrites PATH_INFO.
    This middleware restores the original requested path from Vercel headers.
    """

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # Diagnostic route to verify headers if needed
        if environ.get("HTTP_X_MATCHED_PATH") == "/_debug" or environ.get("PATH_INFO") == "/_debug":
            import json
            status = "200 OK"
            headers = [("Content-Type", "application/json")]
            start_response(status, headers)
            info = {
                "PATH_INFO": environ.get("PATH_INFO"),
                "HTTP_X_MATCHED_PATH": environ.get("HTTP_X_MATCHED_PATH"),
                "HTTP_X_FORWARDED_URI": environ.get("HTTP_X_FORWARDED_URI"),
                "REQUEST_URI": environ.get("REQUEST_URI"),
                "RAW_URI": environ.get("RAW_URI"),
            }
            return [json.dumps(info, indent=2).encode("utf-8")]

        # Restore the actual URL path requested by the browser
        real_path = (
            environ.get("HTTP_X_MATCHED_PATH")
            or environ.get("HTTP_X_FORWARDED_URI")
            or environ.get("REQUEST_URI")
            or environ.get("RAW_URI")
        )

        if real_path and not real_path.startswith("/api/index"):
            # Strip any query parameters from path (e.g., /students?q=test -> /students)
            clean_path = real_path.split("?")[0]
            environ["PATH_INFO"] = clean_path
        elif environ.get("PATH_INFO", "").startswith("/api/index"):
            # If PATH_INFO is literally /api/index.py without header, default to /
            environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)


# Wrap Flask application with the Vercel path fix middleware
app = VercelPathFixMiddleware(flask_app)

if __name__ == "__main__":
    flask_app.run()
