#!/usr/bin/env python3
"""Start the car_consumption app as a daemon."""
import os
import sys
import subprocess

# Fork into background
if os.fork() == 0:
    os.setsid()
    os.chdir("/home/hermes/code/car_consumption")
    # Redirect stdout/stderr
    with open("/tmp/car_consumption.log", "w") as f:
        os.dup2(f.fileno(), 1)
        os.dup2(f.fileno(), 2)
    env = os.environ.copy()
    env["PATH"] = f"/home/hermes/code/car_consumption/.venv/bin:{env['PATH']}"
    os.execvpe(
        "/home/hermes/code/car_consumption/.venv/bin/python",
        [
            "/home/hermes/code/car_consumption/.venv/bin/python",
            "-m", "app.main",
            "--port", "8080",
            "--bind", "0.0.0.0"
        ],
        env
    )
