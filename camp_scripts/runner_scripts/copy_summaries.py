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


shutil.make_archive(
    base_name=new_dir.stem, 
    format="zip",
    base_dir=new_dir,
)
