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

import yaml
import numpy as np
import pandas as pd
from typing import Optional
import matplotlib.pyplot as plt

from scipy import stats
import scipy.integrate as integrate
from scipy.special import factorial
from scipy.special import gamma as gammafunc

from june.demography.demography import (
    load_age_and_sex_generators_for_bins,
    Demography,
    Population,
)
from june.paths import data_path
from june.hdf5_savers import generate_world_from_hdf5
from june.groups import Households

from camps.distributors import CampHouseholdDistributor
from camps.geography import CampGeography
from camps.paths import camp_data_path
from camps.world import CampWorld


# area coding example CXB-219-056
# super area coding example CXB-219-C
# region coding example CXB-219


def read_yaml(config_filename):
    with open(config_filename) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


area_mapping_filename = camp_data_path / "input/geography/area_super_area_region.csv"
area_coordinates_filename = camp_data_path / "input/geography/area_coordinates.csv"
super_area_coordinates_filename = (
    camp_data_path / "input/geography/super_area_coordinates.csv"
)
age_structure_filename = (
    camp_data_path / "input/demography/age_structure_super_area.csv"
)
area_residents_families = (
    camp_data_path / "input/demography/area_residents_families.csv"
)

if area_residents_families.is_file():
    area_residents_families_exists = True
    area_residents_families_df = pd.read_csv(area_residents_families)
    area_residents_families_df.set_index("area", inplace=True)
else:
    area_residents_families_exists = False


area_household_structure_params = (
    camp_data_path / "input/households/household_structure.yaml"
)
if area_household_structure_params.is_file():
    area_household_structure_params_exists = True
    area_household_structure_params_df = read_yaml(area_household_structure_params)
else:
    area_household_structure_params_exists = False

area_household_structure = (
    camp_data_path / "input/households/area_household_structure.csv"
)

if area_household_structure.is_file():
    area_household_structure_exists = True
    area_household_structure_df = pd.read_csv(area_household_structure)
    area_household_structure_df.set_index("CampSSID", inplace=True)
else:
    area_household_structure_exists = False

# area_residents_families_exists = False
# area_household_structure_exists = False
# area_household_structure_params_exists = False


def GenerateDiscretePDF(Type="Gaussian", datarange=[0, 100], Mean=0, SD=1, stretch=False):
    def PValue(Mean, SD, Xmin, Xmax, stretch=False):
        return integrate.quad(lambda x: Gaussian(Mean, SD, x, stretch), Xmin, Xmax)


    def Gaussian(Mean, SD, x,stretch):
        if stretch:
            if abs(x - Mean) < 2:
                return 4*np.exp(-0.5 * ((x - Mean) / SD) ** 2.0) / (SD * np.sqrt(2 * np.pi))
            else:
                return 1*np.exp(-0.5 * ((x - Mean) / SD) ** 2.0) / (SD * np.sqrt(2 * np.pi))
        else:
            return np.exp(-0.5 * ((x - Mean) / SD) ** 2.0) / (SD * np.sqrt(2 * np.pi))


    Vals = np.arange(datarange[0], datarange[1] + 1, 1)
    dist = {}
    for a_i in range(len(Vals) - 1):
        XMin = Vals[a_i] - 0
        XMax = Vals[a_i] + 1
        if stretch:
            PVal = PValue(Mean, SD, XMin, XMax, stretch)[0]
        else:
            PVal = PValue(Mean, SD, XMin, XMax)[0]
        if PVal < 1e-3:
            dist[Vals[a_i]] = 0
        elif PVal >= 1e-3:
            dist[Vals[a_i]] = PVal

    # Renormalize
    dist = {k: v / sum(dist.values()) for k, v in dist.items()}
    generator = stats.rv_discrete(values=[list(dist.keys()), list(dist.values())])
    return generator, dist


def generate_empty_world(filter_key: Optional[dict] = None):
    """
    Generates an empty world with baseline geography

    Parameters
    ----------
    filter_key
        Filter the geo-units which should enter the world

    Returns
    -------
    CampWorld
        camp world class with geographical setup but nothing else

    """
    geo = CampGeography.from_file(
        filter_key=filter_key,
        hierarchy_filename=area_mapping_filename,
        area_coordinates_filename=area_coordinates_filename,
        super_area_coordinates_filename=super_area_coordinates_filename,
    )
    world = CampWorld()
    world.areas = geo.areas
    world.super_areas = geo.super_areas
    world.regions = geo.regions
    world.people = Population()
    return world


def populate_world(world: CampWorld):
    """
    Populates the world. For each super area, we initialize a population
    following the data's age and sex distribution. We then split the population
    into the areas by taking the ratio of the area residents to the total super area
    population. Kids and adults are splited separately to keep a balanced population.

    Parameters
    ----------
    world
        CampWorld class which already ahs geography set up in order to populate

    Returns
    -------
    None
    """
    super_area_names = [super_area.name for super_area in world.super_areas]
    age_sex_generators = load_age_and_sex_generators_for_bins(age_structure_filename)
    demography = Demography(
        age_sex_generators=age_sex_generators, area_names=super_area_names
    )
    for super_area in world.super_areas:
        population = demography.populate(
            super_area.name, ethnicity=False, comorbidity=False
        )
        np.random.shuffle(population.people)
        world.people.extend(population)
        # create two lists to distribute even among areas
        adults = [person for person in population if person.age >= 17]
        kids = [person for person in population if person.age < 17]
        n_kids = len(kids)
        n_adults = len(adults)
        residents_data = {}
        total_residents = 0
        # note: the data that has age distributions and the data that has n_families does not match
        # so we need to do some rescaling
        for area in super_area.areas:
            residents_data[area.name] = area_residents_families_df.loc[
                area.name, "residents"
            ]
            total_residents += residents_data[area.name]
        for area in super_area.areas:
            n_residents_data = residents_data[area.name]
            population_ratio = n_residents_data / total_residents
            n_adults_area = int(np.round(population_ratio * n_adults))
            n_kids_area = int(np.round(population_ratio * n_kids))
            for _ in range(n_adults_area):
                if not adults:
                    break
                area.add(adults.pop())
            for _ in range(n_kids_area):
                if not kids:
                    break
                area.add(kids.pop())
        people_left = adults + kids
        if people_left:
            areas = np.random.choice(super_area.areas, size=len(people_left))
            for area in areas:
                area.add(people_left.pop())


def distribute_people_to_households(world: CampWorld):
    """
    Distributes the people in the world to households by using the CampHouseholdDistributor.

    Parameters
    ----------
    world
        CampWorld class with people ready to be cludtered into households

    Returns
    -------
    None
    """

    if area_household_structure_params_exists:
        household_distributor = CampHouseholdDistributor(
            max_household_size=12,
            household_size_distribution=area_household_structure_params_df["area"][
                "coarse"
            ]["household_size"],
            chance_unaccompanied_childen=area_household_structure_params_df["area"][
                "coarse"
            ]["chance_unaccompanied_childen"],
            chance_single_parent_mf=area_household_structure_params_df["area"][
                "coarse"
            ]["chance_single_parent"],
            min_age_gap_between_childen=area_household_structure_params_df["area"][
                "coarse"
            ]["min_age_gap_between_childen"],
        )
    else:
        household_distributor = CampHouseholdDistributor(
            max_household_size=12,
        )

    households_total = []
    for area in world.areas:
        areaName = area.name
        regionName = area.name[:-4]

        area_data = area_residents_families_df.loc[areaName]
        if area_household_structure_exists:
            area_structure = area_household_structure_df.loc[regionName]

            mother_firstchild_gap_mean = area_structure["Mother-First Child Age Diff"]
            partner_age_gap_mean = area_structure["avgAgeDiff"]
            chance_single_parent = area_structure["chance of Single Parent"]
            chance_multigenerational = area_structure[
                "chance of Multigenerational Families"
            ]
            chance_withchildren = area_structure["chance family with children"]

            mother_firstchild_gap_STD = 2.4
            partner_age_gap_mean_STD = 3
            n_children_STD = 2

            n_children = area_structure["children per family"]

            stretch = False

        else:
            mother_firstchild_gap_mean = 22
            mother_firstchild_gap_STD = 8

            partner_age_gap_mean = 0
            partner_age_gap_mean_STD = 10

            chance_single_parent = 0.179
            chance_multigenerational = 0.268
            chance_withchildren = 0.922

            n_children = 2.5
            n_children_STD = 2

            stretch = True

        mother_firstchild_gap_generator, dist = GenerateDiscretePDF(
            datarange=[14, 60],
            Mean=mother_firstchild_gap_mean + 0.5 + (9.0 / 12.0),
            SD=mother_firstchild_gap_STD
            
        )
        partner_age_gap_generator, dist = GenerateDiscretePDF(
            datarange=[-20, 20], 
            Mean=partner_age_gap_mean + 0.5, 
            SD=partner_age_gap_mean_STD,
            stretch=stretch
        )

        nchildren_generator, dist = GenerateDiscretePDF(
            datarange=[0, 8], 
            Mean=n_children, 
            SD=n_children_STD,
        )

        n_families = int(area_data["families"])
        n_residents = int(area_data["residents"])

        n_families_adapted = int(np.round(len(area.people) / n_residents * n_families))
        area.households = household_distributor.distribute_people_to_households(
            area=area,
            n_families=n_families_adapted,
            n_families_wchildren=int(
                np.round(chance_withchildren * n_families_adapted)
            ),
            n_families_multigen=int(
                np.round(chance_multigenerational * n_families_adapted)
            ),
            n_families_singleparent=int(
                np.round(chance_single_parent * n_families_adapted)
            ),
            partner_age_gap_generator=partner_age_gap_generator,
            mother_firstchild_gap_generator=mother_firstchild_gap_generator,
            nchildren_generator=nchildren_generator,
        )
        households_total += area.households
    world.households = Households(households_total)


def example_run(filter_key=None):
    world = generate_empty_world(filter_key=filter_key)
    populate_world(world)
    distribute_people_to_households(world)
    world.to_hdf5("camp.hdf5")


if __name__ == "__main__":
    example_run(filter_key={"super_area": ["CXB-219-C"]})
    # area coding example CXB-219-056
    # super area coding example CXB-219-C
    # region coding example CXB-219
