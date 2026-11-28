"""Fit farm path config. The fitter's tools were written with absolute cloud paths (<work>/fitter_home/...).
pack_farm.py rewrites every such literal in the packed copies to  farmpaths.HOME + '/...'  so the same code runs
on any machine. HOME is the folder that mirrors the cloud's <work>/fitter_home/ subtree (only the files the fits read).
Where HOME comes from, first hit wins:
  1. env FITFARM_HOME
  2. farm.json next to this file: {"home": "<dir>", "workers": 12, ...}   (relative paths are relative to farm.json)
  3. <this folder>/home
"""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.environ.get('FITFARM_CONFIG', os.path.join(HERE, 'farm.json'))
CFG = {}
if os.path.exists(CFG_PATH):
    with open(CFG_PATH, encoding='utf-8') as f: CFG = json.load(f)
def _abs(p, base): return p if os.path.isabs(p) else os.path.normpath(os.path.join(base, p))
HOME = os.environ.get('FITFARM_HOME') or _abs(CFG.get('home', 'home'), os.path.dirname(CFG_PATH))
HOME = HOME.replace('\\', '/').rstrip('/')
RESULTS = _abs(CFG.get('results', 'results'), os.path.dirname(CFG_PATH))
WORKERS = int(CFG.get('workers', 12))
def P(rel): return HOME + '/' + rel.lstrip('/')
