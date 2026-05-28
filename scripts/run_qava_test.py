"""Run the full qavajs BDD test suite.

Steps:
1. npm install
2. Start docker compose (application + authentik)
3. Setup Authentik OAuth2
4. Wait for services
5. Run qavajs tests
6. Tear down containers
"""

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

    # 1b. Install Playwright browser + OS dependencies (needed in CI)
    # Browser binary is cached by the workflow; OS deps (apt packages) always run but are fast
    run(["npx", "playwright", "install", "chromium"], cwd=tests_dir)
    run(["npx", "playwright", "install-deps", "chromium"], cwd=tests_dir)

    # 2. Start containers. The application container builds the frontend.
    run(compose_cmd("up", "-d", "--build"))

    try:
        # 3. Setup Authentik
        run([sys.executable, "scripts/setup_authentik.py"])

        # 4. Wait for services
        run(["npx", "wait-on", "tcp:10090", "tcp:9000"], cwd=tests_dir)

        # 4b. Debug: verify application is reachable
        run("curl -v http://127.0.0.1:10090/ 2>&1 || true", check=False)
        run(compose_cmd("logs", "--tail=30", "application"), check=False)

        # 5. Run tests
        exit_code = run(
            ["npx", "qavajs", "run", "--config", "config.mjs"],
            check=False,
            cwd=tests_dir,
        )

        # 5b. Dump application logs for debugging test failures
        if exit_code != 0:
            print("\n===== APPLICATION LOGS (last 80 lines) =====")
            run(compose_cmd("logs", "--tail=80", "application"), check=False)
            print("===== END APPLICATION LOGS =====\n")
    finally:
        # 6. Tear down
        run(compose_cmd("stop"), check=False)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
