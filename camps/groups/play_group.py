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
from typing import List, Optional, Dict
from enum import IntEnum

from june.groups import Group, Supergroup
from june.geography import Area
from june.groups.leisure.social_venue import SocialVenue, SocialVenues, SocialVenueError
from june.groups.leisure.social_venue_distributor import SocialVenueDistributor
from camps.paths import camp_data_path, camp_configs_path
from camps.geography import CampArea

default_config_filename = camp_configs_path / "defaults/groups/play_group.yaml"


class PlayGroup(SocialVenue):
    def __init__(self, max_size=np.inf, area=None):
        """
        Play groups in which children can play according to their age groups
        
        Parameters
        ----------
        age_group_limits
            List of successive upper bound age limits for different play groups.
            For example, [3, 7, 12] creates 3 groups with upper bounds of 3, 7, and 12.
        max_size
            Maximum size of any one given play group
        area
            Optional Area class for play groups to be associated with
        """
        super().__init__()
        self.max_size = max_size
        self.area = area
        self.coordinates = self.get_coordinates


class PlayGroups(SocialVenues):
    venue_class = PlayGroup

    def __init__(self, play_groups: List[PlayGroup]):
        super().__init__(play_groups, make_tree=False)
        """
        Create and store information on multiple PlayGroup instances
        """

    @classmethod
    def for_areas(
        cls,
        areas: List[CampArea],
        venues_per_capita: float = 1 / 20,
        max_size: int = 10,
    ):
        """
        Defines class from areas

        Parameters
        ----------
        areas
            List of CampArea instances
        venues_per_capita
            Number of venues to be created for every n people
        age_group_limits
            List of successive upper bound age limits for different play groups.
            For example, [3, 7, 12] creates 3 groups with upper bounds of 3, 7, and 12.
        max_size
            Maximum size of any one given play group

        Returns
        -------
        PlayGroups class instance
        """
        play_groups = []

        # Make a dummy to get the age bins
        age_group_limits = cls.venue_class().subgroup_bins

        for area in areas:
            area_population = len(
                [
                    person
                    for person in area.people
                    if person.age >= age_group_limits[0]
                    and person.age <= age_group_limits[-1]
                ]
            )
            for _ in range(0, int(np.ceil(venues_per_capita * area_population))):
                play_group = cls.venue_class(max_size=max_size, area=area)
                area.play_groups.append(play_group)
                play_groups.append(play_group)
        return cls(play_groups=play_groups)


class PlayGroupDistributor(SocialVenueDistributor):
    """
    Distributes people to play groups according to probability parameters
    """

    default_config_filename = default_config_filename

    def get_social_venue_for_person(self, person):
        """
        We select a random play group from the person area.
        """
        venue = np.random.choice(person.area.play_groups)
        return venue

    def get_possible_venues_for_area(self, area: Area):
        if area.play_groups:
            venue = np.random.choice(area.play_groups)
            return [venue]
        else:
            return None
