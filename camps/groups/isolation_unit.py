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


class IsolationUnit(Group, MedicalFacility):
    class SubgroupType(IntEnum):
        kids = 0
        adults = 1

    def __init__(
        self, 
        area,
        age_group_limits: List[int] = [0, 18, 100],
    ):

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


class IsolationUnits(Supergroup, MedicalFacilities):
    def __init__(self, isolation_units: List[IsolationUnit]):
        super().__init__(isolation_units)
        self.refused_to_go_ids = set()

    def get_closest(self):
        return self[0]

    def release_patient(self, person):
        pass 


