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
from typing import List, Optional
from june.geography import Areas
from enum import IntEnum

from june.groups.leisure.social_venue import SocialVenue, SocialVenues, SocialVenueError
from june.groups.leisure.social_venue_distributor import SocialVenueDistributor
from camps.paths import camp_data_path, camp_configs_path

default_communals_coordinates_filename = camp_data_path / "input/activities/communal.csv"
default_config_filename = camp_configs_path / "defaults/groups/communal.yaml"


class Communal(SocialVenue):
    class SubgroupType(IntEnum):
        kids = 0
        adults = 1

    def __init__(
        self,
        age_group_limits: List[int] = [0, 18, 100],
        max_size = np.inf,
        area=None,
    ):
        super().__init__()
        self.age_group_limits = age_group_limits
        self.min_age = age_group_limits[0]
        self.max_age = age_group_limits[-1] - 1
        self.max_size = max_size

    def get_leisure_subgroup(self, person, subgroup_type=None, to_send_abroad=None):
        if person.age >= self.min_age and person.age <= self.max_age:
            subgroup_idx = (
                np.searchsorted(self.age_group_limits, person.age, side="right") - 1
            )
            return self.subgroups[subgroup_idx]
        else:
            return

    @property
    def kids(self):
        return self.subgroups[self.SubgroupType.kids]

    @property
    def adults(self):
        return self.subgroups[self.SubgroupType.adults]
    


class Communals(SocialVenues):
    social_venue_class = Communal
    default_coordinates_filename = default_communals_coordinates_filename


class CommunalDistributor(SocialVenueDistributor):
    default_config_filename = default_config_filename
