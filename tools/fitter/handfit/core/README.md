# lane_c: ModelSwapper_Hands prototype (FBX hand fitter)

Research prototype. Nothing here ships. See REPORT.md.

Run it from `hands_tool/` with python3 (numpy, scipy, Pillow). The steps run in order and each writes the json the next one reads:
```
cd /home/claude/lane_c/hands_tool
python3 calib.py ../calib.json                      # FBX hand -> controller (Ermac free hand), scale + grip pose
python3 landmarks.py ../landmarks_fbx.json          # web, palm, pads, cuff on the FBX mesh
python3 regions.py && python3 ermaclm.py            # landmark regions; the same regions on Ermac's 1021-vertex topology
python3 ermac_lm.py ../rows192.json ../landmarks_fbx.json ../calib.json ../landmarks_ermac_frames.json
python3 gunlm.py ../gun_landmarks.json              # gun landmarks from the meshes
python3 measure192.py ../rows192.json x ../metrics192.json   # 1.92's 22 guns -> the tolerances
python3 run_gun.py BrutalPistol; python3 run_gun.py Flamethrower2@nozzle      # gun-hand solves (modes A and B)
python3 run_support.py BrutalPistol cup; python3 run_support.py Flamethrower2@nozzle vgrip
python3 report_gun.py BrutalPistol; python3 report_gun.py Flamethrower2       # sheets/, out/*.md3, results/*_report.json
python3 fbx_sheet.py ../poses_auto.json ../sheets/fbx_poses.png
python3 testpack.py ../results/pistol_report.json ../out/BD22Q_192_fbxpistol.pk3   # TEST pk3
flock -o -s /home/claude/rig.lock python3 engine_check.py ../out/BD22Q_192_fbxpistol.pk3 fbx   # QZD 17.3 rig
```
The first run of a gun builds its signed distance fields into `cache/`, about 2 min each.
