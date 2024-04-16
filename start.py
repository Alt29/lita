import os
import subprocess

# Exécutez keep_alive.py en arrière-plan
subprocess.Popen(["python", "keep_alive.py"])

# Exécutez scheduler.py en arrière-plan
subprocess.Popen(["python", "scheduler.py"])

# Exécutez test.py (ou tout autre script que vous souhaitez exécuter)
subprocess.call(["python", "test.py"])
