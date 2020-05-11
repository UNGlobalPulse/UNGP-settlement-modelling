import pytest
import numpy.testing as npt
from time import time

from june import geography as g


@pytest.fixture()
def geography_example():
    return g.Geography.from_file(
        filter_key={"msoa": ["E02000140"]}
    )


def test__nr_of_members_in_units(geography_example):
    assert len(geography_example.areas) == 26
    assert len(geography_example.super_areas) == 1

def test__area_attributes(geography_example):
    area = geography_example.areas.members[0]
    assert area.name == "E00003598"
    npt.assert_almost_equal(
        area.coordinates,
        [51.395954503652504, 0.10846483370388499],
        decimal=3,
    )
    assert area.super_area.name in "E02000140"

def test__super_area_attributes(geography_example):
    super_area = geography_example.super_areas.members[0]
    assert super_area.name == "E02000140"
    npt.assert_almost_equal(
        super_area.coordinates,
        [51.40340615262757, 0.10741193961090514],
        decimal=3,
    )
    assert "E00003595" in [area.name for area in super_area.areas]

def test__create_single_area():
    geography = g.Geography.from_file(filter_key={"oa" : ["E00120481"]})
    assert len(geography.areas) == 1

def test__create_north_east():
    t1 = time()
    geography = g.Geography.from_file(
        filter_key={"region": ["North East"]}
    )
    t2 = time()
    assert t2 - t1 < 5
    assert len(geography.areas) == 8802 
    assert len(geography.super_areas) == 340

