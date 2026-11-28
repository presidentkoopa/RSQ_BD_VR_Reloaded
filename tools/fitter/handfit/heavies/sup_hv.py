"""sup_hv.py <Class> <A|B> <out.json> [support_gun.py options]: support_gun.py (port/) with the heavies' registry (port_hv.GUNS_HV)
loaded, so the FBX support hand can be placed on a heavy gun ported with port_hv.py (r9)."""
import os, sys, runpy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'port'))
import port_hv	# registers GUNS_HV in port_gun.GUNS
sys.argv = [os.path.join(HERE, '..', 'port', 'support_gun.py')] + sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
