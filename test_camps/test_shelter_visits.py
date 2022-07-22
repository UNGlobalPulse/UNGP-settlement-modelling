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


import pytest
import numpy as np
from collections import defaultdict

from june.geography import SuperAreas, SuperArea

from camps.groups import Shelter, Shelters
from camps.groups import SheltersVisitsDistributor


@pytest.fixture(name="visits_world", scope="module")
def setup_shelter_visits(camps_world):
    shelter_visits_distributor = SheltersVisitsDistributor.from_config()
    shelter_visits_distributor.link_shelters_to_shelters(camps_world.super_areas)
    return camps_world


def test__shelter_links(visits_world):
    shelters_to_visit_sizes = defaultdict(int)
    for shelter in visits_world.shelters:
        if shelter.shelters_to_visit == None:
            shelters_to_visit_sizes[0] += 1
        else:
            shelters_to_visit_sizes[len(shelter.shelters_to_visit)] += 1
            for shelter in shelter.shelters_to_visit:
                assert isinstance(shelter, Shelter)

    assert set(shelters_to_visit_sizes.keys()) == set([0, 1, 2, 3])
    for i in shelters_to_visit_sizes.values():
        for j in shelters_to_visit_sizes.values():
            assert np.isclose(i, j, rtol=0.11)
