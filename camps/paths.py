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

import logging
import os
from pathlib import Path
from sys import argv

logger = logging.getLogger(
    __name__
)

project_directory = Path(
    os.path.abspath(__file__)
).parent.parent

working_directory = Path(
    os.getcwd()
)

working_directory_parent = working_directory.parent


def find_default(name: str) -> Path:
    """
    Get a default path when no command line argument is passed.

    - First attempt to find the folder in the current working directory.
    - If it is not found there then try the directory in which June lives.
    - Finally, try the directory above the current working directory. This
    is for the build pipeline.

    This means that tests will find the configuration regardless of whether
    they are run together or individually.

    Parameters
    ----------
    name
        The name of some folder

    Returns
    -------
    The full path to that directory
    """
    for directory in (
        working_directory,
        project_directory,
        working_directory_parent
    ):
        path = directory / name
        if os.path.exists(
                path
        ):
            return path
    raise FileNotFoundError(
        f"Could not find a default path for {name}"
    )


def path_for_name(name: str) -> Path:
    """
    Get a path input using a flag when the program is run.

    If no such argument is given default to the directory above
    the june with the name of the flag appended.

    e.g. --data indicates where the data folder is and defaults
    to june/../data

    Parameters
    ----------
    name
        A string such as "data" which corresponds to the flag --data

    Returns
    -------
    A path
    """
    flag = f"--{name}"
    try:
        path = Path(argv[argv.index(flag) + 1])
        if not path.exists():
            raise FileNotFoundError(
                f"No such folder {path}"
            )
    except (IndexError, ValueError):
        path = find_default(name)
        logger.warning(
            f"No {flag} argument given - defaulting to:\n{path}"
        )

    return path


camp_data_path = path_for_name("camp_data")
camp_configs_path = path_for_name("configs_camps")
