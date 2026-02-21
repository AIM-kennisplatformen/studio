from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
frontend = root / "src" / "frontend"
kg = root / "kg"

# Remove old build
shutil.rmtree(kg, ignore_errors=True)

# Load .env
env = {}
env_file = root / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k] = v

try:
    backend_url = env["BACKEND_BASE_URL"]
except KeyError:
    sys.exit("ERROR: BACKEND_BASE_URL not found in .env")

# Write frontend env file
env_prod = frontend / ".env.production"
env_prod.write_text(f"VITE_BACKEND_BASE_URL={backend_url}")

# Run npm
subprocess.run("npm install", cwd=frontend, check=True, shell=True)
subprocess.run("npm run build", cwd=frontend, check=True, shell=True)

# Cleanup + move dist
env_prod.unlink(missing_ok=True)
shutil.move(str(frontend / "dist"), kg)
