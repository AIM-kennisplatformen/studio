"""Run the full qavajs BDD test suite.

Steps:
1. npm install
2. Build the frontend
3. Start docker compose (app + authentik)
4. Setup Authentik OAuth2
5. Wait for services
6. Run qavajs tests
7. Tear down containers
"""

import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]

COMPOSE_FILES = [
    "docker-compose.yml",
    "tests/bdd/containers/docker-compose-authentik.yml",
]
ENV_FILE = ".env"


tests_dir = root / "tests" / "bdd"


def run(cmd: str | list[str], *, check: bool = True, env: dict | None = None, cwd: Path | None = None) -> int:
    """Run a command, return the exit code.

    If env is provided, it is used AS-IS (not merged with os.environ).
    If env is None, the subprocess inherits the current environment.
    """
    if isinstance(cmd, str):
        result = subprocess.run(cmd, shell=True, cwd=cwd or root, env=env)
    else:
        result = subprocess.run(cmd, cwd=cwd or root, env=env)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result.returncode


def compose_cmd(*args: str) -> list[str]:
    cmd = ["docker", "compose", "--env-file", ENV_FILE]
    for f in COMPOSE_FILES:
        cmd += ["-f", f]
    cmd += list(args)
    return cmd


def main() -> int:
    # 1. npm install
    run(["npm", "install"], cwd=tests_dir)

    # 1b. Install Playwright browsers (needed in CI)
    run(["npx", "playwright", "install", "--with-deps", "chromium"], cwd=tests_dir)

    # 2. Build frontend
    run([sys.executable, "scripts/build_frontend.py"])

    # 3. Start containers
    run(compose_cmd("up", "-d"))

    try:
        # 4. Setup Authentik
        run([sys.executable, "scripts/setup_authentik.py"])

        # 5. Wait for services
        run(["npx", "wait-on", "tcp:10090", "tcp:9000"], cwd=tests_dir)

        # 5b. Debug: verify backend is reachable
        run("curl -v http://127.0.0.1:10090/ 2>&1 || true", check=False)
        run(compose_cmd("logs", "--tail=30", "backend"), check=False)

        # 6. Run tests
        # Clear LD_LIBRARY_PATH to prevent pixi's conda libs from breaking Chromium's
        # network stack (causes ERR_NAME_NOT_RESOLVED in CI).
        if os.environ.get("LD_LIBRARY_PATH"):
            print(f"[DEBUG] Clearing LD_LIBRARY_PATH={os.environ['LD_LIBRARY_PATH']}")
        clean_env = {k: v for k, v in os.environ.items() if k not in ("LD_LIBRARY_PATH", "LD_PRELOAD")}
        exit_code = run(
            ["npx", "qavajs", "run", "--config", "config.mjs"],
            check=False,
            cwd=tests_dir,
            env=clean_env,
        )
    finally:
        # 7. Tear down
        run(compose_cmd("stop"), check=False)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
