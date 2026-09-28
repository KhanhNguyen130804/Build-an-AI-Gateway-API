"""Restart two owned local runner processes and check real DB persistence."""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402
import psycopg  # noqa: E402

from app.core.config import load_settings  # noqa: E402
from app.db.session import database_url  # noqa: E402


def run():
    settings = load_settings()
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    dsn = database_url(settings).set(drivername="postgresql").render_as_string(hide_password=False)
    checks = []
    for attempt in range(2):
        env = {**os.environ, "PORT": str(port)}
        process = subprocess.Popen(
            [sys.executable, "-m", "app"],
            env=env,
            cwd=Path(__file__).resolve().parent.parent,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        try:
            deadline = time.monotonic() + 30
            with httpx.Client(timeout=8) as client:
                while True:
                    if process.poll() is not None:
                        raise RuntimeError("Runner exited")
                    try:
                        response = client.get(f"http://127.0.0.1:{port}/health/ready")
                        if response.status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    if time.monotonic() > deadline:
                        raise RuntimeError("Runner not ready")
                    time.sleep(0.3)
            with psycopg.connect(dsn, connect_timeout=5, prepare_threshold=None) as connection:
                count = connection.execute(
                    "SELECT count(*) FROM gateway.users WHERE username IN (%s,%s)",
                    (settings.demo_username, settings.second_test_username),
                ).fetchone()[0]
                assert count == 2
            checks.append(
                {
                    "fresh_process": attempt + 1,
                    "readiness_status": 200,
                    "persisted_seed_users": count,
                }
            )
        finally:
            process.terminate()
            process.wait(timeout=10)
    target = Path(__file__).resolve().parent.parent / "artifacts/evidence/phase02.json"
    evidence = json.loads(target.read_text(encoding="utf-8"))
    evidence["actual_runner_restart_checks"] = checks
    target.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"process_restart": "PASS", "checks": checks}))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(
            json.dumps(
                {"check": "process_restart", "status": "FAIL", "error_type": type(exc).__name__}
            )
        )
        raise SystemExit(1) from None
