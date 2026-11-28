"""Melee lane: stop ONE of this lane's own farm batches (the detached fit_melee.py batch process and its pool workers), only if the
PID's command line is fit_melee.py with that --batch name. usage: python melee_stop.py <pid> <batch>"""
import subprocess, sys
pid, batch = sys.argv[1], sys.argv[2]
q = '(Get-CimInstance Win32_Process -Filter "ProcessId=%s").CommandLine' % pid
cl = subprocess.run(['powershell', '-NoProfile', '-Command', q], capture_output=True, text=True).stdout.strip()
print('cmdline:', cl)
kids = subprocess.run(['powershell', '-NoProfile', '-Command', '(Get-CimInstance Win32_Process -Filter "ParentProcessId=%s").ProcessId' % pid], capture_output=True, text=True).stdout.split()
print('children:', kids)
if 'fit_melee.py' in cl and ('--batch ' + batch) in cl:
    print(subprocess.run(['taskkill', '/PID', pid, '/T', '/F'], capture_output=True, text=True).stdout)
else:
    print('NOT STOPPED: not this lane\'s batch')
