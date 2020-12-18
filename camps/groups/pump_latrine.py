import numpy as np
import pandas as pd
import yaml
from typing import List

from june.groups.leisure.social_venue import SocialVenue, SocialVenues, SocialVenueError
from june.groups.leisure.social_venue_distributor import SocialVenueDistributor
from camps.paths import camp_configs_path
from june.geography import SuperArea, Area
from june.groups import Household

default_config_filename = camp_configs_path / "defaults/groups/pump_latrine.yaml"


class PumpLatrine(SocialVenue):
    def __init__(self, max_size=np.inf, area=None):
        self.max_size = max_size
        super().__init__()
        self.area = area

    @property
    def coordinates(self):
        return self.area.coordinates


class PumpLatrines(SocialVenues):
    social_venue_class = PumpLatrine
    def __init__(self, pump_latrines: List[PumpLatrine]):
        super().__init__(pump_latrines, make_tree=False)

    @classmethod
    def for_areas(
        cls, areas: List[Area], venues_per_capita=1 / (100 + 35 / 2), max_size=np.inf
    ):
        pump_latrines = []
        for area in areas:
            area_population = len(area.people)
            for _ in range(0, int(np.ceil(venues_per_capita * area_population))):
                pump_latrine = PumpLatrine(max_size, area=area)
                area.pump_latrines.append(pump_latrine)
                pump_latrines.append(pump_latrine)
        return cls(pump_latrines)


class PumpLatrineDistributor(SocialVenueDistributor):
    default_config_filename = default_config_filename

    def get_social_venue_for_person(self, person):
        """
        We select a random pump or latrine from the person area.
        """
        venue = np.random.choice(person.area.pump_latrines)
        return venue

    def get_possible_venues_for_area(self, area: Area):
        venue = np.random.choice(area.pump_latrines)
        return [venue]
