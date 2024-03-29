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

from typing import Tuple, List
import pandas as pd
import numpy as np

from june.geography import Area, Geography, SuperArea, Region


class CampArea(Area):
    def __init__(
        self, name: str, super_area: "SuperArea", coordinates: Tuple[float, float]
    ):
        super().__init__(name, super_area, coordinates)
        self.pump_latrines = list()
        self.play_groups = list()
        self.shelters = list()
        self.informal_works = list()


class CampGeography(Geography):
    def __init__(
        self, areas: List[CampArea], super_areas: List[SuperArea], regions: List[Region]
    ):
        """
        Generate hierachical devision of geography.

        Parameters
        ----------
        areas
            List of CampArea instances to create the lowerest layer in the geographical heirarchy
        super_areas
            List of SuperArea instances to create the midde layer in the geographical heirarchy
        regions
            List of Region instances to create highest layer in the geographical heirarchy
        """
        self.areas = areas
        self.super_areas = super_areas
        self.regions = regions
        # possible buildings
        self.schools = None
        self.hospitals = None
        self.cemeteries = None
        self.shelters = None
        self.households = None

    @classmethod
    def _create_areas(
        cls,
        area_coords: pd.DataFrame,
        super_area: "SuperArea",
        socioeconomic_indices=None,
    ) -> List[Area]:
        """
        Applies the _create_area function throught the area_coords dataframe.
        If area_coords is a series object, then it does not use the apply()
        function as it does not support the axis=1 parameter.

        Parameters
        ----------
        area_coords
            pandas Dataframe with the area name as index and the coordinates
            X, Y where X is longitude and Y is latitude.
        super_area
            Instance of the SuperArea class for for each of the areas in the area_coords Dataframes
        """
        # if a single area is given, then area_coords is a series
        # and we cannot do iterrows()
        if isinstance(area_coords, pd.Series):
            areas = [CampArea(area_coords.name, super_area, area_coords.values)]
        else:
            areas = []
            for name, coordinates in area_coords.iterrows():
                areas.append(
                    CampArea(
                        name,
                        super_area,
                        coordinates=np.array(
                            [coordinates.latitude, coordinates.longitude]
                        ),
                    )
                )
        return areas
