import os
import sys
import subprocess

# Add the application root to Python path
sys.path.insert(0, os.path.dirname(__file__))

# ============================================================
# TEMPORARY: one-time dependency install (no terminal needed)
# This runs pip install ONCE (guarded by a flag file) using the
# app's own virtualenv, then never again. Safe to leave in place
# after it succeeds, but you can remove this block once you've
# confirmed the site is back up and the flag file exists.
# ============================================================
_APP_DIR = os.path.dirname(__file__)
_VENV_PIP = "/home/gisbomhj/virtualenv/Efunza/3.10/bin/pip"
_REQUIREMENTS = os.path.join(_APP_DIR, "requirements.txt")
_FLAG_FILE = os.path.join(_APP_DIR, ".deps_installed_ok")

if not os.path.exists(_FLAG_FILE):
    try:
        result = subprocess.run(
            [_VENV_PIP, "install", "-r", _REQUIREMENTS],
            capture_output=True, text=True, timeout=300,
        )
        print("=" * 60)
        print("ONE-TIME PIP INSTALL RUN")
        print("STDOUT:\n" + result.stdout)
        print("STDERR:\n" + result.stderr)
        print("Return code:", result.returncode)
        print("=" * 60)
        if result.returncode == 0:
            with open(_FLAG_FILE, "w") as f:
                f.write("installed\n")
    except Exception as e:
        print("PIP INSTALL BLOCK FAILED:", repr(e))
# ============================================================
# END TEMPORARY BLOCK
# ============================================================

# Point to the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "efunza_backend.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()