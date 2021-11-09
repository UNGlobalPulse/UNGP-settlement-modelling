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

from sklearn.model_selection import ParameterGrid
import numpy as np
import sys
import os
import re
import json
import pickle
import argparse
from pathlib import Path

from named_grids import *

import camps


usage_output = ( # Taken directly from output when a "bad" arg is given to the full_run_parse
    """
    [-h] [-c COMORBIDITIES] [-p PARAMETERS]
    [-hb HOUSEHOLD_BETA] [-ih INDOOR_BETA_RATIO]
    [-oh OUTDOOR_BETA_RATIO] [-sw START_WEEK] [-inf INFECTIOUSNESS_PATH]
    [-cs CHILD_SUSCEPTIBILITY] [-u ISOLATION_UNITS]
    [-t ISOLATION_TESTING] [-i ISOLATION_TIME]
    [-ic ISOLATION_COMPLIANCE] [-m MASK_WEARING]
    [-mc MASK_COMPLIANCE] [-mb MASK_BETA_FACTOR]
    [-lc LEARNING_CENTERS] [-lcs LEARNING_CENTER_SHIFTS]
    [-lce EXTRA_LEARNING_CENTERS]
    [-lch LEARNING_CENTER_BETA_RATIO]
    [-pgh PLAY_GROUP_BETA_RATIO] [-s SAVE_PATH]
    """
)
accepted = re.findall("\[(.*?)\]", usage_output)

accepted_short = []
accepted_long = []

for flag in accepted:
    spl = flag.split()
    if len(spl) == 1:
        accepted_short.append(spl[0].replace("-",""))
    elif len(spl) == 2:
        accepted_short.append(spl[0].replace("-",""))
        accepted_long.append(spl[1].casefold())
    else:
        print("usage_output has an unusual argument...")

home_dir = Path(camps.__path__[0]).parent

class ClusterRunner:
    def __init__(self, parameter_grid, output_dir):
        self.parameter_grid = parameter_grid
        self.output_dir = Path(output_dir)
        self.job_name = output_dir.stem

        ii = 1
        while self.output_dir.is_dir():
            self.output_dir = output_dir.parent / f"{output_dir.stem}_{ii}"
            ii = ii + 1
        self.output_dir.mkdir(parents=True, exist_ok=True)

        parameter_grid_path = self.output_dir / "parameter_grid.pkl"
        if parameter_grid_path.exists() is False:
            with open(parameter_grid_path, "wb") as f:
                pickle.dump(parameter_grid, f)

        arg_warnings = []
        warn = "\033[31;1mWARN\033[0m "

        script_flags = []
        for ii, parameter_set in enumerate(parameter_grid):
            flags = []
            for param, value in parameter_set.items():
                pc = param.casefold()
                if len(param) <= 2:
                    if pc not in accepted_short and pc not in arg_warnings:
                        arg_warnings.append(pc)
                        print(warn + f"-{pc} not in known short arguments")                      
                    flags.append(f"-{param} {value}")
                else:
                    if pc not in accepted_long and pc not in arg_warnings:
                        arg_warnings.append(pc)
                        print(warn + f"--{pc} not in known long arguments")                      
                    flags.append(f"--{param} {value}")
            
            is_save_path = [p in ["s", "save_path"] for p in parameter_set.keys()]
            if sum(is_save_path) == 0:
                flags.append(f"--save_path {self.output_dir}/run_{ii:03d}")

            script_flags.append(
                ' '.join(flag for flag in flags)
            )
        self.script_flags = script_flags

    @classmethod
    def from_named_grid(cls, named_grid, output_path):
        if output_path is None:
            output_dir = Path.cwd() / named_grid
        else:
            output_dir = Path(output_path)

        if named_grid == "isolation":
            parameter_grid = create_isolation_parameter_grid()
        elif named_grid == "mask_wearing":
            parameter_grid = create_mask_wearing_parameter_grid()
        elif named_grid == "learning_center":
            parameter_grid = create_learning_center_parameter_grid()
        elif named_grid == "indoor_outdoor":
            parameter_grid = create_indoor_outdoor_parameter_grid()
        else:
            print(
                "Named grids are: \n"
                "    ['isolation', 'mask_wearing', 'learning_center', 'indoor_outdoor']\n"
                "    choose from these, or modify \"named_grids.py\" and from_named_grid()"
                "    Exiting."
            )
        return cls(parameter_grid, output_dir)

    @classmethod
    def from_json(cls, json_path, output_path):
        if output_path is None:
            output_dir = Path.cwd() / Path(json_path).stem
        else:
            output_dir = Path(output_path)
        with open(json_path, "r") as f:
            parameter_grid = json.loads(f)

    @classmethod
    def from_pkl(cls, pkl_path, output_path):
        if output_path is None:
            output_dir = Path.cwd() / Path(pkl_path).stem
        else:
            output_dir = Path(output_path)

        with open(pkl_path, "rb") as pkl:
            parameter_grid = pickle.load(pkl)
        return cls(parameter_grid, output_dir)

    def create_submission_scripts(self, jobs_per_node=16):
        print("\n-------create scripts-------\n\n")
        number_of_parameters = len(self.parameter_grid)
        number_of_scripts = int(np.ceil(number_of_parameters / jobs_per_node))
        print(f"num. parameters: {number_of_parameters}")
        print(f"num. scripts: {number_of_scripts}")

        submit_all_script_lines = ["#!/bin/bash\n"]

        stdout_dir = self.output_dir / "stdout"
        stdout_dir.mkdir(parents=True, exist_ok=True)

        python_core = f"python3 -u {home_dir}/camp_scripts/full_run_parse.py"

        for ii in range(number_of_scripts):
            low = ii * jobs_per_node
            high = min( (ii + 1) * jobs_per_node - 1, number_of_parameters -1)

            command_arr="\n".join(
                f"\"{python_core} {self.script_flags[i]}\"" for i in range(low, high+1)
            )

            script = (
                f"#!/bin/bash -l\n"
                
                + f"#SBATCH --ntasks {jobs_per_node}\n"
                + f"#SBATCH -J {self.job_name[:4]}_{ii:03d}\n"
                + f"#SBATCH -o {stdout_dir}/camps{ii:03d}.out\n"
                + f"#SBATCH -e {stdout_dir}/camps{ii:03d}.err\n"
                + f"#SBATCH -p cosma\n"
                + f"#SBATCH -A durham #durham #e.g. dp004\n"
                + f"#SBATCH --exclusive\n"
                + f"#SBATCH -t 48:00:00\n"

                + f"module purge\n"
                + f"#load the modules used to build your program.\n"
                + f"module load python/3.6.5\n"
                + f"module load gnu_comp/7.3.0\n"
                + f"module load hdf5\n"
                + f"module load openmpi/3.0.1\n"
                + f"module load gnu-parallel/20181122\n"
                + f"#venv\n"
                + f"source /cosma/home/durham/gnvq71/campmodelling/UNGP-settlement-modelling/campmodelling/bin/activate\n"
                + f"cd /cosma/home/durham/gnvq71/campmodelling/UNGP-settlement-modelling/\n"

                + f"COMMAND_ARR=({command_arr}) \n"
                + "parallel --lb ::: \"${COMMAND_ARR[@]}\""
            )

            scripts_dir = self.output_dir / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            script_path = scripts_dir / f"submit_{ii:02d}.sh"

            with open(script_path, "w") as f:
                f.write(script)

            submit_all_script_lines.append(f"sbatch {script_path}\n")
        
            if ii==0:
                try:
                    print_script_path = script_path.relative_to(Path.cwd())
                except:
                    print_script_path = script_path
                print(f"script at eg.\n    {print_script_path}")

        submit_all_path = self.output_dir / "submit_all.sh"
        with open(submit_all_path,"w") as submit_all:
            submit_all.writelines(submit_all_script_lines)
        try:
            print_submit_all_path = submit_all_path.relative_to(Path.cwd())
        except:
            print_submit_all_path = submit_all_path

        print(f"submit all with\n    \033[35mbash {print_submit_all_path}\033[0m")


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--named-grid", action="store", default=None)
    parser.add_argument("--json", action="store", default=None)
    parser.add_argument("--pkl", action="store", default=None)
    parser.add_argument("-o", "--output", action="store", default=None)
    args = parser.parse_args()

    check = sum([getattr(args,x) is not None for x in ["named_grid", "json", "pkl"]])
    if check != 1:
        print("provide one of --named-grid [name], --json [json file] --pkl [file].\n Exiting.")
        sys.exit()        

    if args.named_grid is not None:
        runner = ClusterRunner.from_named_grid(args.named_grid, args.output)
    if args.json is not None:
        runner = ClusterRunner.from_json(args.json, args.output)
    if args.pkl is not None:
        runner = ClusterRunner.from_pkl(args.pkl, args.output)

    runner.create_submission_scripts()



        
    















