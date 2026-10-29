import os
import sys

# Disable the email watcher via environment variables
os.environ["EMAIL_WATCH_ENABLED"] = "0"
os.environ["ACE_EMAIL_WATCH"] = "0"

# Import the app from server.py
try:
    from server import app
    print("✅ App imported successfully!")
except Exception as e:
    print(f"❌ Failed to import app: {e}")
    sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting Flask server on http://127.0.0.1:5000...")
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=True)