"""
(c) 2021 UN Global Pulse

This file is part of UNGP Operational Intervention Simulation Tool.

UNGP Operational Intervention Simulation Tool is free software: 
you can redistribute it and/or modify it under the terms of the 
GNU General Public License as published by the Free Software Foundation, 
either version 3 of the License, or (at your option) any later version.

UNGP Operational Intervention Simulation Tool is distributed in the 
hope that it will be useful, but WITHOUT ANY WARRANTY; without even 
the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details.
"""

import os
import sys
from glob import glob
from pathlib import Path
import shutil

name = sys.argv[1].replace("/", "_")

base_dir = Path(sys.argv[1]).absolute()

dir_list = sorted(glob(str(base_dir / "run*/")))


new_dir = Path.cwd() / f"{name}_summaries"
new_dir.mkdir(parents=True, exist_ok=True)

for ii, old_dir in enumerate(dir_list):
    old_dir = Path(old_dir)

    assert f"{ii:03d}" == old_dir.stem.split("_")[1]

    new_summ_path = new_dir / f"summary_{ii:03d}.csv"
    old_summ_path = old_dir / "summary.csv"
    if not new_summ_path.exists():
        if old_summ_path.exists():
            shutil.copy2(old_summ_path, new_summ_path)
        else:
            print(f"{old_summ_path} missing")

    new_loc_path = new_dir / f"locations_{ii:03d}.csv"
    old_loc_path = old_dir / "locations.csv"
    if not new_loc_path.exists():
        if old_loc_path.exists():
            shutil.copy2(old_loc_path, new_loc_path)
        else:
            print(f"{old_loc_path} missing")

old_param_path = base_dir / "parameter_grid.pkl"
new_param_path = new_dir / "parameter_grid.pkl"
shutil.copy2(old_param_path, new_param_path)


shutil.make_archive(base_name=new_dir.stem, format="zip", base_dir=new_dir)
