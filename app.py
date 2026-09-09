"""
BhoomiSetu — Unified Platform Launcher & Entry Point

This script allows running both the FastAPI backend and React (Vite) frontend:
1. Direct execution: `python app.py` (Launches both Backend & Frontend dev servers)
2. ASGI module import: `uvicorn app:app` (Exposes FastAPI app from root)

Usage:
    python app.py                  # Launch backend (port 8000) & frontend (port 5173)
    python app.py --backend-only   # Launch only the FastAPI backend
    python app.py --frontend-only  # Launch only the React Vite frontend
    python app.py --port 8000      # Custom backend port
"""

import argparse
import importlib
import importlib.util
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

# Paths configuration
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
BACKEND_APP_DIR = BACKEND_DIR / "app"

# Ensure backend directory is at index 0 of sys.path
if str(BACKEND_DIR) in sys.path:
    sys.path.remove(str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR))

# Register backend/app package in sys.modules so 'app.main', 'app.config', etc. resolve seamlessly
import types
try:
    app_pkg = types.ModuleType("app")
    app_pkg.__path__ = [str(BACKEND_APP_DIR)]
    app_pkg.__file__ = str(BACKEND_APP_DIR / "__init__.py")
    sys.modules["app"] = app_pkg

    from app.main import app as fastapi_app
    app = fastapi_app
    app_pkg.app = fastapi_app
    _import_error = None
except Exception as err:
    app = None
    _import_error = err


def stream_output(process, prefix):
    """Stream process stdout to main stdout with a prefixed line label."""
    try:
        for line in iter(process.stdout.readline, ""):
            if not line:
                break
            sys.stdout.write(f"[{prefix}] {line}")
            sys.stdout.flush()
    except Exception:
        pass


def run_servers(backend_host="0.0.0.0", backend_port=8000, run_backend=True, run_frontend=True):
    processes = []

    print("\n" + "=" * 65)
    print("  BhoomiSetu -- Unified Platform Launcher")
    print("=" * 65)

    if run_backend:
        print(f" * Backend API Server  : http://localhost:{backend_port}")
        print(f" * API Documentation   : http://localhost:{backend_port}/docs")
    if run_frontend:
        print(f" * Frontend Web Client : http://localhost:5173")
    print("=" * 65 + "\n")

    try:
        # 1. Start Backend Process
        if run_backend:
            cmd_backend = [
                sys.executable, "-m", "uvicorn", "app.main:app",
                "--host", backend_host,
                "--port", str(backend_port),
                "--reload"
            ]
            print(f"[Launcher] Starting Backend: {' '.join(cmd_backend)}")
            backend_proc = subprocess.Popen(
                cmd_backend,
                cwd=str(BACKEND_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            processes.append(("Backend", backend_proc))

            t_backend = threading.Thread(
                target=stream_output, args=(backend_proc, "Backend"), daemon=True
            )
            t_backend.start()

        # 2. Start Frontend Process
        if run_frontend:
            npm_cmd = shutil.which("npm") or shutil.which("npm.cmd") or "npm"
            cmd_frontend = [npm_cmd, "run", "dev"]
            print(f"[Launcher] Starting Frontend: {' '.join(cmd_frontend)}")

            use_shell = sys.platform == "win32"
            frontend_proc = subprocess.Popen(
                cmd_frontend,
                cwd=str(FRONTEND_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                shell=use_shell,
            )
            processes.append(("Frontend", frontend_proc))

            t_frontend = threading.Thread(
                target=stream_output, args=(frontend_proc, "Frontend"), daemon=True
            )
            t_frontend.start()

        print("[Launcher] Both services initialized. Press Ctrl+C to shutdown.\n")

        # Keep main process alive and monitor child processes
        while True:
            time.sleep(1)
            for name, proc in processes:
                retcode = proc.poll()
                if retcode is not None:
                    print(f"[{name}] Process exited with status code {retcode}")
                    raise KeyboardInterrupt

    except KeyboardInterrupt:
        print("\n[Launcher] Shutting down servers gracefully...")
    finally:
        for name, proc in processes:
            print(f"[Launcher] Stopping {name} process (PID {proc.pid})...")
            try:
                if sys.platform == "win32":
                    subprocess.call(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    proc.terminate()
                    proc.wait(timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        print("[Launcher] All processes stopped cleanly. Goodbye!")


def main():
    parser = argparse.ArgumentParser(description="Run BhoomiSetu Backend and Frontend simultaneously")
    parser.add_argument("--host", default="0.0.0.0", help="Backend host interface (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Backend port (default: 8000)")
    parser.add_argument("--backend-only", action="store_true", help="Launch only backend service")
    parser.add_argument("--frontend-only", action="store_true", help="Launch only frontend service")

    args = parser.parse_args()

    if _import_error and not args.frontend_only:
        print(f"[Launcher Notice] Could not pre-import app.main: {_import_error}")

    run_backend = not args.frontend_only
    run_frontend = not args.backend_only

    run_servers(
        backend_host=args.host,
        backend_port=args.port,
        run_backend=run_backend,
        run_frontend=run_frontend,
    )


if __name__ == "__main__":
    main()
