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

from typing import List
from june.groups import Group, Supergroup
from june.demography import Person
from june.groups.hospital import MedicalFacility, MedicalFacilities
from enum import IntEnum
import numpy as np

import logging

logger = logging.getLogger("isolation units")


class IsolationUnit(Group, MedicalFacility):
    def __init__(self, area, age_group_limits: List[int] = [0, 17, 100]):

        super().__init__()
        self.age_group_limits = age_group_limits
        self.min_age = age_group_limits[0]
        self.max_age = age_group_limits[-1] - 1
        self.area = area

    @property
    def coordinates(self):
        return self.area.coordinates

    def add(self, person: Person):
        super().add(person=person, activity="medical_facility", subgroup_type=0)


class IsolationUnits(Supergroup, MedicalFacilities):
    venue_class = IsolationUnit

    def __init__(self, isolation_units: List[IsolationUnit]):
        super().__init__(isolation_units)
        self.refused_to_go_ids = set()
        logger.info(f"There are {len(isolation_units)} isolation unit(s)")

    def get_closest(self):
        return self[0]

    def release_patient(self, person):
        pass
