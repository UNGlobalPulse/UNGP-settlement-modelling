import numpy as np
import pandas as pd

from june.geography import SuperArea

from camps.geography import CampArea, CampGeography



def test__camp_area():
    super_area = SuperArea(
        name = "test_super_area",
        areas = None,
        region = None,
        coordinates = np.array([0.0,1.0])
    )
    area = CampArea(
        name = "test_area",
        super_area = super_area,
        coordinates = (0.0,1.0)
    )

    assert area.name == "test_area"
    assert area.super_area.name == "test_super_area"
    assert area.coordinates[0] == 0.0
    assert area.coordinates[1] == 1.0

def test__create_areas():
    super_area = SuperArea(
        name = "test_super_area",
        areas = None,
        region = None,
        coordinates = np.array([0.0,1.0])
    )

    area_coords = pd.DataFrame(
        data = {
            "name": ["test_area_1", "test_area_2"],
            "longitude": [0.0, 1.0],
            "latitude": [1.0, 0.0]
        }
    ).set_index("name")

    areas = CampGeography._create_areas(
        area_coords = area_coords,
        super_area = super_area,
    )

    assert len(areas) == 2
    assert areas[0].name == "test_area_1"
    assert areas[1].coordinates[0] == 0.0
