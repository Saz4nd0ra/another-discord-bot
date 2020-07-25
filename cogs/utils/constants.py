import os.path, subprocess

try:
    VERSION = subprocess.check_output(["git", "describe", "--tags", "--always"]).decode('ascii').strip()
except Exception:
    VERSION = 'non-git-version'

