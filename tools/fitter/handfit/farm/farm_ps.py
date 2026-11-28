"""Read-only: list python.exe processes (pid, cpu time, memory) so the farm's workers can be seen."""
import subprocess
print(subprocess.run(['tasklist', '/V', '/FI', 'IMAGENAME eq python.exe', '/FO', 'TABLE'], capture_output=True, text=True).stdout)
