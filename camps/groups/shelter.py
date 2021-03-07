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
from enum import IntEnum
from random import randint

from june.groups import Group, Supergroup, Households, Household
from june.groups.group.interactive import InteractiveGroup
from june.geography import Areas


class Shelter(Household):
    __slots__ = "shelters_to_visit"
    class SubgroupType(IntEnum):
        household_1 = 1
        household_2 = 2

    def __init__(self, area=None):
        super().__init__(type="shelter", area=area)
        self.shelters_to_visit = None

    def add(self, household: Household):
        if not isinstance(household, Household):
            raise ValueError("Shelters want households added to them, not people.")
        if len(household.people) == 0:
            raise ValueError("Adding an empty household to a shelter is not supported.")
        if len(self.subgroups[0].people) == 0:
            for person in household.people:
                self.subgroups[0].append(person)
                setattr(person.subgroups, "residence", self[0])
        elif len(self.subgroups[1].people) == 0:
            for person in household.people:
                self.subgroups[1].append(person)
                setattr(person.subgroups, "residence", self[1])
        else:
            assert self.n_households == 2
            raise ValueError("Shelter full!")
        # add to residents
        self.residents = tuple((*self.residents, person))

    @property
    def families(self):
        return [subgroup for subgroup in self.subgroups if len(subgroup.people) != 0]

    @property
    def n_families(self):
        return len(self.families)

    @property
    def n_households(self):
        return len(self.families)

    @property
    def coordinates(self):
        return self.area.coordinates

    def get_leisure_subgroup(self, person, subgroup_type, to_send_abroad):
        self.being_visited = True
        self.make_household_residents_stay_home(to_send_abroad=to_send_abroad)
        return self[randint(0,1)]

    def get_interactive_group(self, people_from_abroad=None):
        return InteractiveGroup(self, people_from_abroad=people_from_abroad)


class Shelters(Supergroup):
    def __init__(self, shelters):
        super().__init__(shelters)

    @classmethod
    def from_families_in_area(cls, n_families_area, sharing_shelter_ratio=0.75):
        n_shelters_multi = int(np.floor(sharing_shelter_ratio * n_families_area / 2))
        n_shelters = n_families_area - n_shelters_multi
        shelters = [Shelter() for _ in range(n_shelters)]
        return cls(shelters)

    @classmethod
    def for_areas(cls, areas: Areas, sharing_shelter_ratio=0.75):
        shelters = []
        for area in areas:
            n_families_area = len(area.households)
            n_shelters_multi = int(np.floor(sharing_shelter_ratio * n_families_area/ 2))
            n_shelters = n_families_area - n_shelters_multi
            area.shelters = [Shelter(area=area) for _ in range(n_shelters)]
            shelters += area.shelters
        return cls(shelters)

class ShelterDistributor:
    def __init__(self, sharing_shelter_ratio=0.75):
        self.sharing_shelter_ratio = sharing_shelter_ratio

    def distribute_people_in_shelters(self, shelters: Shelters, households: Households):
        households_idx = np.arange(0, len(households))
        np.random.shuffle(households_idx)
        households_idx = list(households_idx)
        multifamily_shelters = int(
            np.floor(self.sharing_shelter_ratio * len(households) / 2)
        )
        for i in range(multifamily_shelters):
            shelter = shelters[i]
            shelter.add(households[households_idx.pop()])
            shelter.add(households[households_idx.pop()])
        i += 1
        while households_idx:
            i = i % len(shelters)
            shelter = shelters[i]
            shelter.add(households[households_idx.pop()])
            i += 1
