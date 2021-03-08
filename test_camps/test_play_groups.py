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
import pytest
from camps.groups import PlayGroup, PlayGroups
from june.demography import Person
from camps.geography import CampArea


def test__comoposition_play_groups():
    kid_young = Person.from_attributes(age=3)
    kid_middle = Person.from_attributes(age=8)
    kid_old = Person.from_attributes(age=13)
    kid_very_old = Person.from_attributes(age=16)
    play_group = PlayGroup()
    subgroup = play_group.get_leisure_subgroup(person=kid_young)
    assert subgroup.subgroup_type == 0
    subgroup = play_group.get_leisure_subgroup(person=kid_middle)
    assert subgroup.subgroup_type == 1
    subgroup = play_group.get_leisure_subgroup(person=kid_old)
    assert subgroup.subgroup_type == 2
    subgroup = play_group.get_leisure_subgroup(person=kid_very_old)
    assert subgroup.subgroup_type == 2
    not_kid = Person.from_attributes(age=50)
    subgroup = play_group.get_leisure_subgroup(person=not_kid)
    assert subgroup is None


@pytest.mark.parametrize("n_people", [20, 50])
def test__play_group_per_area(n_people):

    people = [
        Person.from_attributes(age=age)
        for age in np.random.randint(low=3, high=16, size=n_people)
    ]
    dummy_area = CampArea(name="dummy", super_area=None, coordinates=(12.0, 15.0))
    areas = [dummy_area]
    dummy_area.people = people
    play_groups = PlayGroups.for_areas(areas=areas, venues_per_capita=1.0 / 20.0)

    assert len(play_groups) == int(np.ceil(1.0 / 20.0 * n_people))
