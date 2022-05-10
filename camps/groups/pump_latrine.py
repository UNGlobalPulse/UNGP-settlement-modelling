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

from pipes import Template
from june.groups.group.subgroup import Subgroup
import numpy as np
import pandas as pd
import yaml
from typing import List

from june.groups.leisure.social_venue import SocialVenue, SocialVenues, SocialVenueError
from june.groups.leisure.social_venue_distributor import SocialVenueDistributor
from camps.paths import camp_configs_path
from june.geography import SuperArea, Area
from june.groups import Household
from enum import IntEnum, Enum

default_config_filename = camp_configs_path / "defaults/groups/pump_latrine.yaml"

class PumpLatrine(SocialVenue):
    def __init__(self, max_size=np.inf, area=None):
        """
        Pumps and latrines people can use

        Parameters
        ----------
        max_size
            Maximum size of any one given play group
        area
            Optional Area class for play groups to be associated with
        """
        super().__init__()
        self.max_size = max_size
        self.area = area   
        self.coordinates = self.get_coordinates   

class PumpLatrines(SocialVenues):
    venue_class = PumpLatrine 

    def __init__(self, pump_latrines: List[PumpLatrine]):
        """
        Create and store information on multiple PumpLatrine instances
        
        Parameters
        ----------
        pump_latrines
            List of PumpLatrine classes
        """
        super().__init__(pump_latrines, make_tree=False)
    
    @classmethod
    def for_areas(
        cls, 
        areas: List[Area], 
        venues_per_capita=0.002426274539, #1 / (100 + 35 / 2),
        max_size=np.inf,
    ):

        """
        Defines class from areas

        Parameters
        ----------
        areas
            List of Area instances
        venues_per_capita
            Number of venues to be created for every n people
        max_size
            Maximum size of any one given play group

        Returns
        -------
        PumpLatrines class instance
        """
        pump_latrines = []
        for area in areas:
            area_population = len(area.people)
            for _ in range(0, int(np.ceil(venues_per_capita * area_population))):
                pump_latrine = cls.venue_class(
                    max_size, 
                    area=area)
                area.pump_latrines.append(pump_latrine)
                pump_latrines.append(pump_latrine)
        return cls(pump_latrines)

class PumpLatrineDistributor(SocialVenueDistributor):
    """
    Distributes people to pumps and latrines according to probability parameters
    """
    default_config_filename = default_config_filename

    def get_social_venue_for_person(self, person):
        """
        We select a random pump or latrine from the person area.

        Parameters
        ----------
        person
            Instance of the Person class

        Returns
        -------
        venue
            Venue selected for person
        """
        venue = np.random.choice(person.area.pump_latrines)
        return venue

    def get_possible_venues_for_area(self, area: Area):
        """
        Select a random pump or latrine from a given Area

        Parameters
        ----------
        area
            Area from which to select pump or latrine
        
        Returns
        -------
        venue
            Venue selected from area
        """
        venue = np.random.choice(area.pump_latrines)
        return [venue]
