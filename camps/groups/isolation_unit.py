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


class IsolationUnit(Group, MedicalFacility):
    def __init__(self, area):
        super().__init__()
        self.area = area

    @property
    def coordinates(self):
        return self.area.coordinates
    
    def add(self, person: Person):
        super().add(person=person, activity="medical_facility", subgroup_type=0)


class IsolationUnits(Supergroup, MedicalFacilities):
    def __init__(self, isolation_units: List[IsolationUnit]):
        super().__init__(isolation_units)
        self.refused_to_go_ids = set()

    def get_closest(self):
        return self[0]

    def release_patient(self, person):
        pass 


