import pandas as pd
from typing import List

from june.paths import data_path

default_cities_filename = data_path / "input/geography/england_wales_cities.csv"


class City:
    """
    A city is a collection of areas, with some added methods for functionality,
    such as commuting or local lockdowns.
    """

    def __init__(self, areas: List[str] = None, name: str = None):
        self.areas = areas
        self.name = name

    @classmethod
    def from_file(cls, name, city_areas_filename=default_cities_filename):
        city_areas_df = pd.read_csv(city_areas_filename)
        city_areas_df.set_index("city", inplace=True)
        return cls.from_df(name=name, city_areas_df=city_areas_df)

    @classmethod
    def from_df(cls, name, city_areas_df):
        city_areas = city_areas_df.loc[name].values
        return cls(areas=city_areas, name=name)


class Cities:
    """
    A collection of cities.
    """

    def __init__(self, cities: List[City]):
        self.members = cities

    def __iter__(self):
        return iter(self.members)

    def __getitem__(self, idx):
        return self.members[idx]

    @classmethod
    def for_areas(
        cls, areas: List["Area"], city_areas_filename=default_cities_filename
    ):
        """
        Initializes the cities which are on the given areas.
        """
        city_areas = pd.read_csv(city_areas_filename)
        city_areas.set_index("area", inplace=True)
        city_areas = city_areas.loc[[area.name for area in areas]]
        city_areas.reset_index(inplace=True)
        city_areas.set_index("city", inplace=True)
        cities = []
        for city in city_areas.index.unique():
            city = City(name=city, areas=city_areas.loc[city, "area"])
            cities.append(city)
        return cls(cities)


