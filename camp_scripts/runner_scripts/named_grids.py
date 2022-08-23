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
import json
import pickle
import argparse
from pathlib import Path


def create_isolation_parameter_grid():
    print("This is hard coded to print '\033[032misolation grid\033[0m'\n")

    fixed_parameters = {
        "comorbidities": True,
        "household_beta": 0.2,
        "indoor_beta_ratio": 0.55,
        "outdoor_beta_ratio": 0.05,
    }

    infectiousness_paths = ["nature", "nature_lower", "nature_larger"]
    parameter_grid = list(
        ParameterGrid(
            {
                "isolation_compliance": [0.5, 0.75, 1.0],
                "isolation_testing": [0, 1, 2, 3, 5],
                "isolation_time": [5, 10],
                "isolation_units": [True],
                "infectiousness_path": infectiousness_paths,
            }
        )
    )
    parameter_grid2 = list(
        ParameterGrid(
            {
                "isolation_compliance": [0],
                "isolation_testing": [0],
                "isolation_time": [0],
                "isolation_units": [False],
                "infectiousness_path": infectiousness_paths,
            }
        )
    )
    parameter_grid = parameter_grid + parameter_grid2

    for parameter in parameter_grid:
        parameter.update(fixed_parameters)

    print("example:", parameter_grid[0])

    return parameter_grid


def create_mask_wearing_parameter_grid():
    print("This is hard coded to print '\033[032mmask wearing\033[0m'\n")

    fixed_parameters = {
        "household_beta": 0.2,
        "indoor_beta_ratio": 0.55,
        "outdoor_beta_ratio": 0.05,
    }

    infectiousness_paths = ["nature", "nature_lower", "nature_larger"]
    parameter_grid = list(
        ParameterGrid(
            {
                "mask_wearing": [True],
                "mask_compliance": [0.1, 0.25, 0.5, 0.75, 1.0],
                "mask_beta_factor": np.linspace(0.1, 0.9, 9),
                "infectiousness_path": infectiousness_paths,
            }
        )
    )
    # add no isolation ones
    parameter_grid2 = list(
        ParameterGrid(
            {
                "mask_wearing": [False],
                "mask_compliance": [0],
                "mask_beta_factor": [0],
                "infectiousness_path": infectiousness_paths,
            }
        )
    )
    parameter_grid = parameter_grid + parameter_grid2

    for parameter in parameter_grid:
        parameter.update(fixed_parameters)

    return parameter_grid


def create_learning_center_parameter_grid():
    print('This is hard coded to print "\033[32mlearning centers\033[0m')

    grid1 = list(
        ParameterGrid(
            {
                "comorbidities": [True],
                "child_susceptibility": [False],
                "learning_center_beta_ratio": [0.25, 0.35, 0.45, 0.55, 0.65, 0.75],
                "play_group_beta_ratio": [0.15, 0.25, 0.35],
                "learing_centers": [True],
            }
        )
    )

    grid2 = [
        {  # set all flags to default.
            "comorb": True,  # Isdefault, but needs to be passed as arg anyway.
            "child_susc": False,
            "learing_center_beta_ratio": 0,
            "play_group_beta_ratio": 0,
            "learning_centers": False,
        },
        {  # - one with no flags apart from -cs True
            "comorbidities": True,  # Isdefault, but needs to be passed as arg anyway.
            "child_susceptibility": True,
            "learning_center_beta_ratio": 0,
            "play_group_beta_ratio": 0,
            "learning_centers": False,
        },
        {  # - one with -cs True -lc True -lch 0.55 -pgh 0.25
            "comorb": True,  # Isdefault, but needs to be passed as arg anyway.
            "child_susc": True,
            "learning_center_beta_ratio": 0.55,
            "play_group_beta_ratio": 0.25,
            "learning_centers": True,
        },
    ]
    parameter_grid = grid1 + grid2

    print(f"parameter_grid has length {len(parameter_grid)}")

    return parameter_grid


def create_indoor_outdoor_parameter_grid():
    print('This is hard coded to print "\033[32mindoor outdoor\033[0m')

    parameter_grid = list(
        ParameterGrid(
            {
                "household_beta_ratio": [
                    0.1,
                    0.2,
                    0.3,
                    0.4,
                    0.5,
                    0.6,
                    0.7,
                    0.8,
                    0.9,
                    1.0,
                ],
                "indoor_beta_ratio": [0.35, 0.45, 0.55, 0.65, 0.75],
                "outdoor_beta_ratio": [0.05, 0.15, 0.25, 0.35, 0.45],
            }
        )
    )

    return parameter_grid
