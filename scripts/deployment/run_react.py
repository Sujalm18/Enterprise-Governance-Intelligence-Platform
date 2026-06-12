import os
import sys
import time
import subprocess
import signal
from pathlib import Path

def get_python_executable():
    """Finds the appropriate Python executable in the virtual environment or fallback."""
    cwd = Path.cwd()
    
    # Check if running in Windows and virtual env exists
    if sys.platform == "win32":
        venv_python = cwd / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            return str(venv_python)
            
    # For Unix-based or fallback
    venv_python_unix = cwd / ".venv" / "bin" / "python"
    if venv_python_unix.exists():
        return str(venv_python_unix)
        
    # Return current running Python executable
    return sys.executable

def main():
    python_bin = get_python_executable()
    print("=" * 60)
    print("   Enterprise Governance Intelligence Platform Launcher")
    print("=" * 60)
    print(f"Using Python: {python_bin}")
    print("Starting backend and React frontend services...\n")
    
    # Define subprocesses
    backend_cmd = [
        python_bin, "-m", "uvicorn", "backend.app.main:app",
        "--host", "127.0.0.1", "--port", "8000", "--reload"
    ]
    
    frontend_cmd = [
        "npm", "--prefix", "frontend", "run", "dev"
    ]
    
    # Use shell=True on Windows for npm commands since it's a batch script (npm.cmd)
    shell_mode = sys.platform == "win32"
    
    processes = []
    try:
        # Start Backend (FastAPI)
        print("[+] Launching Backend (FastAPI) on http://127.0.0.1:8000 ...")
        backend_proc = subprocess.Popen(
            backend_cmd,
            stdout=None,
            stderr=None,
            shell=False
        )
        processes.append(backend_proc)
        
        # Small delay to let the backend start
        time.sleep(2)
        
        # Start Frontend (React + Vite)
        print("[+] Launching React Frontend (Vite) on default port (e.g. http://127.0.0.1:5173) ...")
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            stdout=None,
            stderr=None,
            shell=shell_mode
        )
        processes.append(frontend_proc)
        
        print("\n" + "=" * 60)
        print("Services are running successfully!")
        print("  - Backend API:       http://127.0.0.1:8000")
        print("  - API Documentation: http://127.0.0.1:8000/docs")
        print("  - React Frontend:    Check Vite console output (usually http://localhost:5173)")
        print("=" * 60)
        print("Press Ctrl+C to stop all services.\n")
        
        # Keep running until interrupted
        while True:
            # Check if any process terminated unexpectedly
            for p in processes:
                if p.poll() is not None:
                    print(f"\n[!] Process {p.args} exited with code {p.returncode}")
                    raise KeyboardInterrupt
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[-] Shutting down all services gracefully...")
        for p in processes:
            if p.poll() is None:
                print(f"Stopping process: {p.pid}")
                try:
                    if sys.platform == "win32":
                        # Send taskkill to make sure child processes are also terminated
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(p.pid)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    else:
                        p.terminate()
                        p.wait(timeout=3)
                except Exception as e:
                    print(f"Error terminating process {p.pid}: {e}")
        print("[+] Cleanup complete. Goodbye!")

if __name__ == "__main__":
    main()
