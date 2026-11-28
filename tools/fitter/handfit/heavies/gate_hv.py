"""gate_hv.py: port/gate_gun.py (same commands) with the heavies' registry (port_hv.GUNS_HV) loaded, so `steady` finds the
SupportPoint row of a heavy gun ported with port_hv.py (r9)."""
import os, sys, runpy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'port'))
import port_hv	# registers GUNS_HV in port_gun.GUNS
sys.argv = [os.path.join(HERE, '..', 'port', 'gate_gun.py')] + sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
