import os
import sys

# Ensure root directory is in Python path so app, config, models can be imported
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# Vercel looks for the WSGI application callable named 'app'
if __name__ == "__main__":
    app.run()
