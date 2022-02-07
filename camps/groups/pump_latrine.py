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
from typing import List

from june.groups.leisure.social_venue import SocialVenue, SocialVenues, SocialVenueError
from june.groups.leisure.social_venue_distributor import SocialVenueDistributor
from camps.paths import camp_configs_path
from june.geography import SuperArea, Area
from june.groups import Household
from enum import IntEnum

default_config_filename = camp_configs_path / "defaults/groups/pump_latrine.yaml"


class PumpLatrine(SocialVenue):
    class SubgroupType(IntEnum):
        kids = 0
        adults = 1

    def __init__(
        self, 
        max_size=np.inf, 
        area=None,
        age_group_limits: List[int] = [0, 18, 100],
    ):

        super().__init__()
        self.age_group_limits = age_group_limits
        self.min_age = age_group_limits[0]
        self.max_age = age_group_limits[-1] - 1
        self.max_size = max_size
        self.area = area

    @property
    def coordinates(self):
        return self.area.coordinates

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


class PumpLatrines(SocialVenues):
    social_venue_class = PumpLatrine
    def __init__(self, pump_latrines: List[PumpLatrine]):
        super().__init__(pump_latrines, make_tree=False)

    @classmethod
    def for_areas(
        cls, areas: List[Area], venues_per_capita=1 / (100 + 35 / 2), max_size=np.inf
    ):
        pump_latrines = []
        for area in areas:
            area_population = len(area.people)
            for _ in range(0, int(np.ceil(venues_per_capita * area_population))):
                pump_latrine = PumpLatrine(max_size, area=area)
                area.pump_latrines.append(pump_latrine)
                pump_latrines.append(pump_latrine)
        return cls(pump_latrines)


class PumpLatrineDistributor(SocialVenueDistributor):
    default_config_filename = default_config_filename

    def get_social_venue_for_person(self, person):
        """
        We select a random pump or latrine from the person area.
        """
        venue = np.random.choice(person.area.pump_latrines)
        return venue

    def get_possible_venues_for_area(self, area: Area):
        venue = np.random.choice(area.pump_latrines)
        return [venue]
