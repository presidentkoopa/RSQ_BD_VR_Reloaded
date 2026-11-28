"""gate_r12.py: port/gate_gun.py (same commands) with the heavies registry (port_hv) and the r12 melee registry (melee_r12) loaded,
so `steady` finds the SupportPoint row of FlameCannon (row 28), Unmaker, HellishMissileLauncher and the melee weapons (r12)."""
import os, sys, runpy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'heavies'))
import port_hv, melee_r12	# noqa: register GUNS_HV + MELEE in port_gun.GUNS
sys.argv = [os.path.join(HERE, 'gate_gun.py')] + sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
