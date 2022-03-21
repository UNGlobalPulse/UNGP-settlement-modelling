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

default_nfdistributioncenters_coordinates_filename = (
    camp_data_path / "input/activities/non_food_distribution_center.csv"
)
default_config_filename = (
    camp_configs_path / "defaults/groups/non_food_distribution_center.yaml"
)


class NFDistributionCenter(SocialVenue):
    def __init__(
        self,
        max_size = np.inf,
        area=None,
    ):
        super().__init__()
        self.max_size = max_size
        self.area = area   
        self.coordinates = self.get_coordinates    

class NFDistributionCenters(SocialVenues):
    venue_class = NFDistributionCenter
    default_coordinates_filename = default_nfdistributioncenters_coordinates_filename


class NFDistributionCenterDistributor(SocialVenueDistributor):
    default_config_filename = default_config_filename
