import os
import sys
import urllib.parse

# Ensure root directory is in Python path so app, config, models can be imported
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app as flask_app


class VercelPathFixMiddleware:
    """
    WSGI middleware to fix PATH_INFO on Vercel Serverless Functions.
    Vercel rewrites requests to /api/index.py?__path=$1.
    This middleware extracts the original URL path and restores it into PATH_INFO.
    """

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get("QUERY_STRING", "")
        if "__path=" in qs:
            parsed = urllib.parse.parse_qs(qs, keep_blank_values=True)
            path_list = parsed.pop("__path", None)
            if path_list is not None:
                raw_path = path_list[0] if path_list else ""
                clean_path = "/" + raw_path.lstrip("/")
                environ["PATH_INFO"] = clean_path
                # Re-encode remaining query string without __path
                environ["QUERY_STRING"] = urllib.parse.urlencode(
                    [(k, v) for k, vs in parsed.items() for v in vs]
                )
        elif environ.get("PATH_INFO", "").startswith("/api/index"):
            environ["PATH_INFO"] = "/"

        # Diagnostic endpoint if needed
        if environ.get("PATH_INFO") == "/_debug":
            import json
            status = "200 OK"
            headers = [("Content-Type", "application/json")]
            start_response(status, headers)
            info = {
                "PATH_INFO": environ.get("PATH_INFO"),
                "QUERY_STRING": environ.get("QUERY_STRING"),
                "DATABASE_URL_SET": bool(os.environ.get("DATABASE_URL")),
            }
            return [json.dumps(info, indent=2).encode("utf-8")]

        return self.wsgi_app(environ, start_response)


# Wrap Flask application with the Vercel path fix middleware
app = VercelPathFixMiddleware(flask_app)

if __name__ == "__main__":
    flask_app.run()
