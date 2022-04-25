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

from typing import List, Tuple, Optional
import numpy as np
import pandas as pd
import yaml
import collections
from enum import IntEnum
from sklearn.neighbors import BallTree
from camps import paths
from june.groups import Group, Supergroup
from june.demography import Person

import logging
logger = logging.getLogger("learning_centers")

default_learning_centers_coordinates_path = (
    paths.camp_data_path / "input/activities/learning_center.csv"
)
default_config_path = paths.camp_configs_path / "defaults/groups/learning_center.yaml"


class LearningCenter(Group):
    """
    One learning center is equivalent to one room that kids go to during weekdays in 
    different shifts. There are two subgroups, students and teachers
    """
    def __init__(
        self, coordinates: Tuple[float, float] = (None,None), n_pupils_max: int = 35,
    ):
        """
        Parameters
        ----------
        coordinates
            latitude and longitude for the learning center
        n_pupils_max
            maximum number of pupils in the classroom
        """
        super().__init__()
        self.coordinates = coordinates
        self.n_pupils_max = n_pupils_max
        self.active_shift = 0
        self.has_shifts = True
        self.ids_per_shift = collections.defaultdict(list)
        self.area = None

    def add(self, person: Person, shift: int, subgroup_type):
        """
        Add a person to the learning center

        Parameters
        ----------
        person
            Person instance to add
        shift
           shift that the person will attend 
        subgroup_type
            subgroup to which the person is added
        """
        super().add(
            person=person, activity="primary_activity", subgroup_type=subgroup_type
        )
        self.ids_per_shift[shift].append(person.id)

    @property
    def n_pupils(self):
        return len(self.students)

    @property
    def n_teachers(self):
        return len(self.teachers)

    @property
    def teachers(self):              
        return self.subgroups[self.SubgroupType.teachers]

    @property
    def students(self):
        return self.subgroups[self.SubgroupType.students]

    @property
    def super_area(self):
        return self.area.super_area


class LearningCenters(Supergroup):
    venue_class = LearningCenter
    
    def __init__(
        self,
        learning_centers: List[venue_class],
        learning_centers_tree: bool = True,
        n_shifts: int = 4,
    ):
        """
        Collection of learning centers.

        Parameters
        ----------
        learning_centers
            List of learning centers
        learning_centers_tree
            Whether to build a tree with the learning center coordinates, for quick querying
        n_shifts
            Number of daily shifts 
        """
        super().__init__(members=learning_centers)
        self.members = learning_centers
        if learning_centers_tree:
            coordinates = np.vstack([np.array(lc.coordinates) for lc in self.members])
            self.learning_centers_tree = self._create_learning_center_tree(coordinates)
        self.has_shifts = True
        self.n_shifts = n_shifts

    @classmethod
    def from_config(
        cls, learning_centers: "LearningCenters", config_path: str = default_config_path
    ):
        """
        Defines class from config file

        Parameters
        ----------
        learning_centers
            Instance of LearningCentres contining all LearningCenter instances
        config_path
            Full path to config file
        
        Returns
        -------
        LearningCentres class instance
        """
        with open(config_path) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        logger.info(f"There are {len(learning_centers)} learning center(s)")
        return cls(learning_centers, **config)

    @classmethod
    def for_areas(
        cls,
        areas: "Areas",
        coordinates_path: str = default_learning_centers_coordinates_path,
        max_distance_to_area=5,
        max_size=np.inf,
        **kwargs
    ):
        """
        Defines class from areas and coordinates of learning centers

        Parameters
        ----------
        areas
            Instance of Areas containing instances of Area classes
        coordinates_path
            Full path to csv file contining coordinates of learning centers
        max_distance
            Maximum distance (in km) people are willing to travel to find their 'nearest' learning center
        max_size
            Maximum size of the learning centers

        Returns
        -------
        LearningCenters class instance
        """
        learning_centers_df = pd.read_csv(coordinates_path)
        logger.info(f"There are {len(learning_centers_df)} learning center(s)")
        coordinates = learning_centers_df.loc[:, ["latitude", "longitude"]].values
        return cls.from_coordinates(
            coordinates, max_size, areas, max_distance_to_area=max_distance_to_area,**kwargs
        )

    @classmethod
    def for_geography(
        cls,
        geography,
        coordinates_path: str = default_learning_centers_coordinates_path,
        max_distance_to_area=5,
        max_size=np.inf,
    ):
        """
        Defines class from geography

        Parameters
        ----------
        geography
            Geography class initialised with heirarchy
        coordinates_path
            Full path to csv file contining coordinates of learning centers
        max_distance
            Maximum distance (in km) people are willing to travel to find their 'nearest' learning center
        max_size
            Maximum size of the learning centers

        Returns
        -------
        LearningCenters class instance
        """
        return cls.for_areas(
            areas=geography.areas,
            coordinates_path=coordinates_path,
            max_size=max_size,
            max_distance_to_area=max_distance_to_area,
        )

    @classmethod
    def from_coordinates(
        cls,
        coordinates: List[np.array],
        areas: Optional["Areas"] = None,
        max_distance_to_area=5,
        max_size=np.inf,
        **kwargs
    ):
        """
        Defines class from coordinates

        Parameters
        ----------
        coordinates
            List of np.array of coordinates
        areas
            Instance of the Areas class to reference learning centers to their area
        max_distance
            Maximum distance (in km) people are willing to travel to find their 'nearest' learning center
        max_size
            Maximum size of the learning centers

        Returns
        -------
        LearningCenters class instance
        """
        if areas is not None:
            _, distances = areas.get_closest_areas(
                coordinates, k=1, return_distance=True
            )
            distances_close = np.where(distances < max_distance_to_area)
            coordinates = coordinates[distances_close]
        learning_centers = list()
        for coord in coordinates:
            lc = cls.venue_class()   
            lc.coordinates = coord         
            if areas is not None:
                lc.area = areas.get_closest_area(coordinates=coord)
            learning_centers.append(lc)
        return cls(learning_centers, **kwargs)

    @staticmethod
    def _create_learning_center_tree(
        learning_centers_coordinates: np.ndarray,
    ) -> BallTree:
        """

        Parameters
        ----------
        learning_centers_coordinates 
            array with coordinates

        Returns
        -------
        Tree to query nearby learning centers 
        """
        return BallTree(np.deg2rad(learning_centers_coordinates), metric="haversine")

    def get_closest(self, coordinates: Tuple[float, float], k: int) -> int:
        """
        Get the k-th closest learning center to a given coordinate

        Parameters
        ----------
        coordinates
            latitude and longitude
        k
            k-th neighbour

        Returns
        -------
        ID of the k-th closest learning center

        """
        coordinates_rad = np.deg2rad(coordinates).reshape(1, -1)
        k = min(k, len(list(self.learning_centers_tree.data)))
        distances, neighbours = self.learning_centers_tree.query(
            coordinates_rad, k=k, sort_results=True,
        )
        return neighbours[0]

    def activate_next_shift(self, n_shifts):
        """
        Activate next shift in all learning centers

        Paramters
        ---------
        n_shifts
            number of total daily shifts

        Returns
        -------
        None
        """
        for learning_center in self.members:
            learning_center.active_shift += 1
            if learning_center.active_shift == n_shifts:
                learning_center.active_shift = 0
