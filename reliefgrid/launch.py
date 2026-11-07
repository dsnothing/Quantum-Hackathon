"""Local-only companion launcher. Run --setup once, then launch normally."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen
import webbrowser

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def pnpm_command():
    explicit = os.environ.get("PNPM_CLI")
    if explicit:
        return [shutil.which("node") or "node", explicit]
    executable = shutil.which("pnpm")
    if executable:
        return [executable]
    # Codex desktop bundles pnpm even when npm/corepack are absent from PATH.
    runtime = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "WindowsApps"
    matches = sorted(runtime.glob("OpenAI.CodexPrimaryRuntime.*/dependencies/node/node_modules/pnpm/bin/pnpm.cjs")) if os.name == "nt" else []
    if matches:
        return [shutil.which("node") or "node", str(matches[-1])]
    raise RuntimeError("Install Node.js 20.19+ and pnpm, or set PNPM_CLI to pnpm.cjs. See reliefgrid/README.md.")


def setup():
    if not PYTHON.exists():
        subprocess.run([sys.executable, "-m", "venv", str(ROOT / ".venv")], check=True)
    subprocess.run([str(PYTHON), "-m", "ensurepip", "--upgrade"], check=True)
    subprocess.run([str(PYTHON), "-m", "pip", "install", "-r", str(ROOT / "requirements-lock.txt")], check=True)
    command = pnpm_command()
    subprocess.run(command + ["install", "--frozen-lockfile"], cwd=ROOT / "frontend", check=True)
    subprocess.run(command + ["build"], cwd=ROOT / "frontend", check=True)


def health(url):
    try:
        with urlopen(url + "/api/v1/health", timeout=1) as response:
            payload = json.load(response)
        return payload.get("app") == "reliefgrid" and payload.get("version") == "1" and payload.get("ready") is True
    except (URLError, OSError, ValueError):
        return False


def occupied(port):
    with socket.socket() as connection:
        connection.settimeout(0.5)
        return connection.connect_ex(("127.0.0.1", port)) == 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup", action="store_true", help="Install Python dependencies and build optional UI first")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=8010)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        raise RuntimeError("Port must be between 1 and 65535.")
    if args.setup:
        setup()
    if not PYTHON.exists():
        raise RuntimeError("Python environment missing. Run: python reliefgrid/launch.py --setup")
    if not (ROOT / "frontend/dist/index.html").is_file():
        raise RuntimeError("Companion frontend missing. Run: python reliefgrid/launch.py --setup")
    url = f"http://127.0.0.1:{args.port}"
    reused = health(url)
    process = None
    log_path = REPO / "build/reliefgrid/server.log"
    if not reused:
        if occupied(args.port):
            raise RuntimeError(f"Port {args.port} belongs to another service. Use --port with a free port; no process was stopped.")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        environment = os.environ.copy()
        environment["RELIEFGRID_PORT"] = str(args.port)
        options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
        with log_path.open("ab") as log:
            process = subprocess.Popen([str(PYTHON), "-m", "reliefgrid.backend.api"], cwd=REPO,
                                       env=environment, stdin=subprocess.DEVNULL, stdout=log, stderr=log, **options)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if health(url):
                break
            if process.poll() is not None:
                raise RuntimeError(f"ReliefGrid exited during startup. See {log_path}")
            time.sleep(0.25)
        else:
            process.terminate()
            process.wait(timeout=5)
            raise RuntimeError(f"ReliefGrid health check timed out. See {log_path}")
    print(f"ReliefGrid {'already running' if reused else 'started'}: {url}")
    if process:
        print(f"Server PID: {process.pid}. Log: {log_path}")
        (log_path.parent / f"server-{args.port}.pid").write_text(str(process.pid), encoding="ascii")
    if not args.no_browser:
        webbrowser.open(url)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        print(f"ReliefGrid: {exc}", file=sys.stderr)
        raise SystemExit(1)
