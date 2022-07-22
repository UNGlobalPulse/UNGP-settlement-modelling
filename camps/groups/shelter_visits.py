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

import numpy as np
import pandas as pd
import yaml
from itertools import chain
from random import randint, shuffle
from june.geography import Areas, SuperAreas
from june.groups.leisure import ResidenceVisitsDistributor
from june.paths import data_path, configs_path

from camps.paths import camp_data_path, camp_configs_path
from camps.groups import Shelter, Shelters

default_config_filename = camp_configs_path / "defaults/groups/shelter_visits.yaml"


class SheltersVisitsDistributor(ResidenceVisitsDistributor):
    def __init__(
        self, times_per_week, daytypes, hours_per_day, drags_household_probability=0
    ):
        """
        Like other 'leisure' distributors in JUNE, this defines the distributor for the shelters

        Parameters
        ----------
        times_per_week
            Number of times per week people go on shelter visits
        hours_per_day
            Number of hours per day they spend visiting
        drags_household_probability
            Probability that, if one person from a household goes, that they bring everyone else with them
        """
        super().__init__(
            times_per_week=times_per_week,
            daytypes=daytypes,
            hours_per_day=hours_per_day,
            residence_type_probabilities={"household": 1.0},
            drags_household_probability=drags_household_probability,
        )

    @classmethod
    def from_config(
        cls, daytypes: dict, config_filename: str = default_config_filename
    ):
        """
        Defines class from config
        
        Parameters
        ----------
        config_filename
            Full path to config file
        
        Returns
        -------
        Instance of the ShelterVisitsDistributor class
        """

        with open(config_filename) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return cls(daytypes=daytypes, **config)

    def link_shelters_to_shelters(self, super_areas):
        """
        Links people between shelters. 
        Strategy: We pair each shelter with 0, 1, or 2 other shelters (with equal prob.). 
        The shelter of the former then has a probability of visiting the shelter of the later
        at every time step.

        Parameters
        ----------
        super_areas
            list of super areas
        
        Returns
        -------
        None
        """
        for super_area in super_areas:
            shelters_super_area = list(
                chain.from_iterable(area.shelters for area in super_area.areas)
            )
            shuffle(shelters_super_area)
            for shelter in shelters_super_area:
                if shelter.n_families == 0:
                    continue
                shelters_to_link_n = randint(0, 3)
                shelters_to_visit = []
                for _ in range(shelters_to_link_n):
                    shelter_idx = randint(0, len(shelters_super_area) - 1)
                    shelter_to_visit = shelters_super_area[shelter_idx]
                    if (
                        shelter_to_visit.id == shelter.id
                        or shelter_to_visit.n_families == 0
                    ):
                        continue
                    shelters_to_visit.append(shelter_to_visit)
                if shelters_to_visit:
                    shelter.shelters_to_visit = tuple(shelters_to_visit)

    def get_leisure_group(self, person):
        """
        Gets the group of a person
        
        Parameters
        ----------
        person
            A person - instance of the Person class

        Returns
        -------
        group
            Group of a person 
        """
        candidates = person.residence.group.shelters_to_visit
        if candidates is None:
            return
        n_candidates = len(candidates)
        if n_candidates == 0:
            return
        elif n_candidates == 1:
            group = candidates[0]
        else:
            group = candidates[randint(0, n_candidates - 1)]
        return group
