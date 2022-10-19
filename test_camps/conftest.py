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
import numba as nb
import pandas as pd
import random
from scipy.stats import lognorm, rv_discrete
from collections import defaultdict
from datetime import datetime
import os
import pickle
import json

from june.demography import Person, Population
from june.groups import Household, Households, Hospital, Hospitals, Cemeteries
from june.distributors import HospitalDistributor
from june.world import World
from june.epidemiology.epidemiology import Epidemiology
from june.epidemiology.infection import Immunity, InfectionSelector, InfectionSelectors
from june.interaction import Interaction
from june.policy import Hospitalisation, MedicalCarePolicies, Policies
from june.simulator import Simulator

from camps.geography import CampGeography
from camps.world import CampWorld
from camps.activity import CampActivityManager
from camps.groups.leisure import generate_leisure_for_world, generate_leisure_for_config
from camps.paths import camp_data_path, camp_configs_path
from camps.camp_creation import (
    generate_empty_world,
    populate_world,
    distribute_people_to_households,
    GenerateDiscretePDF
)
from camps.distributors import camp_household_distributor
from camps.groups import PumpLatrines, PumpLatrineDistributor
from camps.groups import DistributionCenters, DistributionCenterDistributor
from camps.groups import Communals, CommunalDistributor
from camps.groups import FemaleCommunals, FemaleCommunalDistributor
from camps.groups import Religiouss, ReligiousDistributor
from camps.groups import Shelter, Shelters, ShelterDistributor
from camps.groups import IsolationUnit, IsolationUnits
from camps.groups import LearningCenter, LearningCenters
from camps.distributors import LearningCenterDistributor
from camps.groups import PlayGroups, PlayGroupDistributor
from camps.groups import EVouchers, EVoucherDistributor
from camps.groups import NFDistributionCenters, NFDistributionCenterDistributor
from camps.groups import SheltersVisitsDistributor
from camps.groups import InformalWorks, InformalWorkDistributor

config_file_path = camp_configs_path / "config_demo.yaml"
interactions_file_path = camp_configs_path / "defaults/interaction/interaction_Survey.yaml"
policies_file_path = camp_configs_path / "defaults/policy/simple_policy.yaml"

# read synthetic input data
syn_data_path = "./camp_test_data"
basecamp_population_dist_df = pickle.load(open(os.path.join(syn_data_path, "basecamp_population_dist_df.pkl"), 'rb'))
area_n_residents_params = pickle.load(open(os.path.join(syn_data_path, "basecamp_residents_area_fit_params.pkl"), 'rb'))
with open(os.path.join(syn_data_path, "basecamp_famsize.pkl"), 'rb') as f:
    basecamp_famsize_dict = pickle.load(f)
    basecamp_famsize_avg = pickle.load(f)
with open(os.path.join(syn_data_path, "basecamp_flat_enrollment_rates.json")) as f:
    flat_enrollment_rates = json.load(f)

# venues to be assigned from coordinates and relative per-capita baseline parameters
coords_venues_types = ['distribution_centers', 'n_f_distribution_centers', 'e_vouchers',
                       'communals', 'female_communals', 'religiouss', 'learning_centers', 'hospitals']
venues_per_capita = {
    'pump_latrines': 1/50,              # from unhcr/sphere -- not used here
    'play_groups': 1/20,                # on kids_population, from unhcr/sphere -- not used here
    'distribution_centers': 1/20000,    # from unhcr/sphere
    'n_f_distribution_centers': 1/20000,
    'e_vouchers': 1/20000,
    'communals': 1/5000,
    'female_communals': 1/5000,
    'religiouss': 1/500,
    'learning_centers': 1/500,          # on kids_population
    'hospitals': 1/20000
}

earth_radius = 6371000.  # meters


def set_random_seed(seed=999):
    """
    Sets global seeds for testing in numpy, random, and numbaized numpy.
    """

    @nb.njit(cache=True)
    def set_seed_numba(seed):
        random.seed(seed)
        return np.random.seed(seed)

    np.random.seed(seed)
    set_seed_numba(seed)
    random.seed(seed)
    return


def new_lat_lon(lat, lon, d_lat, d_lon):
    new_lat = lat + (d_lat / earth_radius) * (180 / np.pi)
    new_lon = lon + (d_lon / earth_radius) * (180 / np.pi) / np.cos(lat * np.pi/180)
    return new_lat, new_lon


def generate_geo_grid(n_regions, area_spacing=150, init_lat=0.0, init_lon=0.0):
    """
    Generate geographical location for a grid-like world.
    Every region is divided into 4 super areas of 9 areas each (total n_areas = 4*9*n_regions).
    With this geography of 4*9 areas in each region, an area_spacing of 150m allows to get regions (i.e. UNHCR camps)
    that can accommodate 20K people with ~40m^2 per person, which satisfies minimal standards.

    Parameters
    ----------
    n_regions : int
        Number of regions the grid-like world should contain. Must be a square number.
    area_spacing: float
        Spacing between centers of areas.
    init_lat : float
        Initial latitude used to position the grid.
    init_lon : float
        Initial longitude used to position the grid.

    Returns
    -------
    region_coords, super_area_coords, area_coords, area_super_area_region : pd.DataFrame
        DataFrames containing coordinates and hierarchy of regions, super areas and areas.
    """

    if np.sqrt(n_regions) % 1 != 0:
        raise ValueError("Number of regions must be a square number")
    else:
        side_length = int(np.sqrt(n_regions))

    n_super_areas = n_regions * 4
    n_areas = n_super_areas * 9

    region_names = []
    region_lat = []
    region_lon = []

    super_area_names = []
    super_area_lat = []
    super_area_lon = []

    area_names = []
    super_area_hierarchy = []
    region_hierarchy = []
    area_lat = []
    area_lon = []

    region_number = 0
    super_area_number = 0
    area_number = 0

    for r_i in range(side_length):
        for r_j in range(side_length):
            new_lat, new_lon = new_lat_lon(
                init_lat,
                init_lon,
                (r_j * 6 * area_spacing) + 2.5 * area_spacing,
                (r_i * 6 * area_spacing) + 2.5 * area_spacing
            )
            region_names.append("r{}".format(region_number))
            region_lat.append(new_lat)
            region_lon.append(new_lon)
            for sa_i in range(2):
                for sa_j in range(2):
                    new_lat, new_lon = new_lat_lon(
                        init_lat,
                        init_lon,
                        (sa_j * 3 * area_spacing) + (r_j * 6 * area_spacing) + area_spacing,
                        (sa_i * 3 * area_spacing) + (r_i * 6 * area_spacing) + area_spacing
                    )
                    super_area_names.append("sa{}".format(super_area_number))
                    super_area_lat.append(new_lat)
                    super_area_lon.append(new_lon)
                    for a_i in range(3):
                        for a_j in range(3):
                            new_lat, new_lon = new_lat_lon(
                                init_lat,
                                init_lon,
                                (a_j * area_spacing) + (sa_j * 3 * area_spacing) + (r_j * 6 * area_spacing),
                                (a_i * area_spacing) + (sa_i * 3 * area_spacing) + (r_i * 6 * area_spacing)
                            )
                            area_names.append("a{}".format(area_number))
                            area_number += 1
                            super_area_hierarchy.append("sa{}".format(super_area_number))
                            region_hierarchy.append("r{}".format(region_number))
                            area_lat.append(new_lat)
                            area_lon.append(new_lon)
                    super_area_number += 1
            region_number += 1

    region_coords = pd.DataFrame(
        {
            "region": region_names,
            "latitude": region_lat,
            "longitude": region_lon
        }
    )
    super_area_coords = pd.DataFrame(
        {
            "super_area": super_area_names,
            "latitude": super_area_lat,
            "longitude": super_area_lon
        }
    )
    area_coords = pd.DataFrame(
        {
            "area": area_names,
            "latitude": area_lat,
            "longitude": area_lon
        }
    )
    area_super_area_region = pd.DataFrame(
        {
            "area": area_names,
            "super_area": super_area_hierarchy,
            "region": region_hierarchy
        }
    )
    return region_coords, super_area_coords, area_coords, area_super_area_region


def get_gridcamp_boundary(n_areas, area_spacing, init_lat, init_lon):
    """
    Get latitude and longitude ranges for gridcamp.
    """
    length = np.sqrt(n_areas) * area_spacing  # total length of gridcamp side
    # (init_lat,init_long) is the center of the first area, shift by -area_spacing/2 to get the lower left (ll) corner
    ll_lat, ll_lon = new_lat_lon(init_lat, init_lon, -area_spacing/2, -area_spacing/2)
    lat_delta = ll_lat + (length / earth_radius) * (180 / np.pi)
    lon_delta = ll_lon + (length / earth_radius) * (180 / np.pi) / np.cos(ll_lat * np.pi / 180)
    return [ll_lat, lat_delta], [ll_lon, lon_delta]


def generate_empty_virtual_world(n_regions, area_spacing=150, init_lat=0.0, init_lon=0.0):
    # generate a geo grid with nregions
    region_coords, super_area_coords, area_coords, area_super_area_region = generate_geo_grid(
        n_regions=n_regions,
        area_spacing=area_spacing,
        init_lat=init_lat,
        init_lon=init_lon
    )

    # set indices to use create_geographical_units (cf. june.geography)
    area_super_area_region.set_index("super_area", inplace=True)
    area_coords.set_index("area", inplace=True)
    super_area_coords.set_index("super_area", inplace=True)

    # use the defined geographical units to instantiate CampGeography
    areas, super_areas, regions = CampGeography.create_geographical_units(
        hierarchy=area_super_area_region,
        area_coordinates=area_coords,
        super_area_coordinates=super_area_coords,
        area_socioeconomic_indices=None,
    )
    geography = CampGeography(
        areas=areas,
        super_areas=super_areas,
        regions=regions
    )

    # instantiate a virtual CampWorld
    world = CampWorld()
    world.areas = geography.areas
    world.super_areas = geography.super_areas
    world.regions = geography.regions
    return world, area_super_area_region


def populate_virtual_world(world, basecamp_population_dist_df, area_n_residents_params, seed):
    """
    Generate population for gridcamp based on age distribution and n_residents/area obtained from a basecamp.
    Note: this currently works only with lognorm parameters and model.

    Parameters
    ----------
    world : CampWorld
        The gridcamp object to be populated.
    basecamp_population_dist_df : pd.DataFrame
        Population distribution of the basecamp (e.g., obtained with get_basecamp_age_distribution).
    area_n_residents_params: dict
        (lognorm) Parameters to sample areas' density (e.g., obtained with fit_basecamp_n_residents_area).
    seed : int
        Random seed

    Returns
    -------
    gridcamp_ages : dict
        Sampled ages for each area.
    """
    # generate gridcamp areas' n_residents
    grid_area_sizes = list(map(int, np.round(
        lognorm.rvs(
            s=area_n_residents_params['s'],
            loc=area_n_residents_params['loc'],
            scale=area_n_residents_params['scale'],
            size=len(world.areas),
            random_state=seed
        ))))

    # organize values and probabilities for population ages from basecamp distribution
    # the first bins are for female, the last bins for male (fictitious age+100)
    xk = np.concatenate((basecamp_population_dist_df['upper_age'].values, basecamp_population_dist_df['upper_age'].values + 100))
    pk = np.concatenate((basecamp_population_dist_df['f_per'].values / 100, basecamp_population_dist_df['m_per'].values / 100))
    grid_populator = rv_discrete(name='grid_populator', values=(xk, pk), seed=seed)

    world_ages = {}
    people = []
    # generate people from basecamp distribution respecting the sampled area size (sampled with lognorm)
    print("Populating by areas...")
    for area, size in zip(world.areas, grid_area_sizes):
        grid_area_ages = grid_populator.rvs(size=size)
        world_ages[area.name] = grid_area_ages
        for i in range(size):
            if grid_area_ages[i] >= 100:  # male
                person = Person.from_attributes(
                    age=grid_area_ages[i]-100,
                    sex="m",
                )
                area.add(person)
                people.append(person)
            else:  # female
                person = Person.from_attributes(
                    age=grid_area_ages[i],
                    sex="f",
                )
                area.add(person)
                people.append(person)

    world.people = Population(people=people)
    print(f"There are {len(world.people)} people in the virtual world.")

    return world_ages


def distribute_virtual_people_to_households(world, basecamp_famsize_dict, basecamp_famsize_avg, max_hh_size=12):
    """
    Distribute people to households in the world, according to average family size distribution of a basecamp.
    CampHouseholdDistributor uses average size distribution from histogram of basecamp data;
    n_families for each area is determined as len(area.people)/(basecamp average family size).

    Parameters
    ---------
    world : CampWorld
        The gridcamp object where households should be distributed (Population should be already defined).
    basecamp_famsize_dict : dict
        Dictionary describing family size distribution, up to max_hh_size.
    basecamp_famsize_avg : float
        Average family size from basecamp data.
    max_hh_size : int, default=12
        Maximum size allowed for households.
    """
    # instantiate refined household distributor
    household_distributor = camp_household_distributor.CampHouseholdDistributor(
        kid_max_age=17,
        adult_min_age=17,
        adult_max_age=99,
        young_adult_max_age=49,
        max_household_size=max_hh_size,
        household_size_distribution=basecamp_famsize_dict,
        chance_unaccompanied_children=0.01,
        min_age_gap_between_children=1,
        chance_single_parent_mf={"m": 1, "f": 10},
        ignore_orphans=False
    )
    # distribute people area by area
    households_total = []
    print("Distributing households by areas...")
    for area in world.areas:
        n_residents = len(area.people)
        if n_residents < basecamp_famsize_avg:
            n_families = 1
            print(f"\tArea {area.name} has {n_residents} residents (< {basecamp_famsize_avg} avg). Set n_families "
                  f"= 1.")
        else:
            n_families = int(n_residents / basecamp_famsize_avg)

        # default parameters for family composition
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

        area.households = household_distributor.distribute_people_to_households(
            area=area,
            n_families=n_families,
            n_families_wchildren=int(np.round(chance_withchildren * n_families)),
            n_families_multigen=int(np.round(chance_multigenerational * n_families)),
            n_families_singleparent=int(np.round(chance_single_parent * n_families)),
            partner_age_gap_generator=partner_age_gap_generator,
            mother_firstchild_gap_generator=mother_firstchild_gap_generator,
            nchildren_generator=nchildren_generator,
        )
        households_total += area.households
    world.households = Households(households_total)
    print(f"{len(world.households)} households have been added to the virtual world.")
    return


def uniformly_sample_locations(coords_ranges, n_venues):
    """
    Uniformly sample n_venues geo-locations within given boundary.
    """
    xy_min = [coords_ranges[0][0], coords_ranges[1][0]]
    xy_max = [coords_ranges[0][1], coords_ranges[1][1]]
    selected_coords = np.random.uniform(low=xy_min, high=xy_max, size=(n_venues, 2))
    return selected_coords


@pytest.fixture(name="camps_world", scope="module")
def generate_virtual_camp():

    world, area_super_area_region = generate_empty_virtual_world(n_regions=1, area_spacing=150)
    world_ages = populate_virtual_world(world, basecamp_population_dist_df, area_n_residents_params, seed=999)
    # distribute people to households
    distribute_virtual_people_to_households(world, basecamp_famsize_dict, basecamp_famsize_avg, max_hh_size=12)

    # define all venues_counts and venues_coords (except pump_latrines, play_groups, informal_works, isolation units)
    # get gridcamp latitude and longitude range
    lat_range, lon_range = get_gridcamp_boundary(
        n_areas=len(world.areas),
        area_spacing=150,
        init_lat=0.0,
        init_lon=0.0
    )

    venues_coords = dict.fromkeys(coords_venues_types)
    venues_counts = dict.fromkeys(coords_venues_types)

    total_population = len(world.people)
    kids_population = len([p for p in world.people if 3 <= p.age <= 17])

    for v in coords_venues_types:
        if v in ['play_groups', 'learning_centers']:
            venues_counts[v] = int(np.ceil(int(np.ceil(venues_per_capita[v] * kids_population))))
        else:
            venues_counts[v] = int(np.ceil(int(np.ceil(venues_per_capita[v] * total_population))))
        venues_coords[v] = uniformly_sample_locations((lat_range, lon_range), n_venues=venues_counts[v])

    # learning_centers
    LearningCenters.get_interaction(interactions_file_path)
    world.learning_centers = LearningCenters.from_coordinates(
        coordinates=venues_coords['learning_centers'],
        areas=world.areas,
        max_distance_to_area=5,
        n_shifts=4
    )
    regions_names = [r.name for r in world.regions]
    region_enrollment_female = dict.fromkeys(regions_names, flat_enrollment_rates['female_dict'])
    region_enrollment_male = dict.fromkeys(regions_names, flat_enrollment_rates['male_dict'])
    learningcenter_distributor = LearningCenterDistributor(
        learning_centers=world.learning_centers,
        female_enrollment_rates=region_enrollment_female,
        male_enrollment_rates=region_enrollment_male,
        area_region_df=area_super_area_region,  # from generate_geo_grid
        teacher_min_age=21,
        neighbour_centers=50
    )
    learningcenter_distributor.distribute_teachers_to_learning_centers(world.areas)
    learningcenter_distributor.distribute_kids_to_learning_centers(world.areas)

    # hospitals
    Hospitals.get_interaction(interactions_file_path)
    IsolationUnits.get_interaction(interactions_file_path)

    hospitals_list = []
    for h in range(venues_counts['hospitals']):
        hospital = Hospital(
            coordinates=venues_coords['hospitals'][h],
            n_beds=50,
            n_icu_beds=4,
            trust_code=None,
        )
        hospitals_list.append(hospital)
    hospitals = Hospitals(hospitals=hospitals_list, neighbour_hospitals=5)

    for hospital in hospitals:
        hospital.area = world.areas.get_closest_area(hospital.coordinates)
    world.hospitals = hospitals
    hospital_distributor = HospitalDistributor(hospitals, medic_min_age=20, patients_per_medic=10)
    hospital_distributor.assign_closest_hospitals_to_super_areas(world.super_areas)

    # remaining locations (added using from_coordinates except for pump_latrines, play_groups, informal_works)
    world.isolation_units = IsolationUnits([IsolationUnit(area=hospital.area) for hospital in world.hospitals])
    hospital_distributor.distribute_medics_from_world(world.people)

    PumpLatrines.get_interaction(interactions_file_path)
    world.pump_latrines = PumpLatrines.for_areas(world.areas)  # using default per-capita

    PlayGroups.get_interaction(interactions_file_path)
    world.play_groups = PlayGroups.for_areas(world.areas)  # using default per-capita

    DistributionCenters.get_interaction(interactions_file_path)
    world.distribution_centers = DistributionCenters.from_coordinates(
        coordinates=venues_coords['distribution_centers'],
        super_areas=world.super_areas
    )
    Communals.get_interaction(interactions_file_path)
    world.communals = Communals.from_coordinates(
        coordinates=venues_coords['communals'],
        super_areas=world.super_areas
    )
    FemaleCommunals.get_interaction(interactions_file_path)
    world.female_communals = FemaleCommunals.from_coordinates(
        coordinates=venues_coords['female_communals'],
        super_areas=world.super_areas
    )
    Religiouss.get_interaction(interactions_file_path)
    world.religiouss = Religiouss.from_coordinates(
        coordinates=venues_coords['religiouss'],
        super_areas=world.super_areas
    )
    EVouchers.get_interaction(interactions_file_path)
    world.e_vouchers = EVouchers.from_coordinates(
        coordinates=venues_coords['e_vouchers'],
        super_areas=world.super_areas
    )
    NFDistributionCenters.get_interaction(interactions_file_path)
    world.n_f_distribution_centers = NFDistributionCenters.from_coordinates(
        coordinates=venues_coords['n_f_distribution_centers'],
        super_areas=world.super_areas
    )
    InformalWorks.get_interaction(interactions_file_path)
    world.informal_works = InformalWorks.for_areas(world.areas)

    world.cemeteries = Cemeteries()

    # cluster shelters
    Shelters.get_interaction(interactions_file_path)
    world.shelters = Shelters.for_areas(world.areas)
    shelter_distributor = ShelterDistributor(sharing_shelter_ratio=0.75)  # proportion of families that share a shelter
    for area in world.areas:
        shelter_distributor.distribute_people_in_shelters(area.shelters, area.households)
    print(f"All people have been distributed to shelters.")

    return world

@pytest.fixture(name="old_camps_world", scope="module")
def generate_camp():
    
    world = generate_empty_world({"region": ["CXB-219"]})
    populate_world(world)
    # distribute people to households
    distribute_people_to_households(world)

    # learning_centers
    LearningCenters.get_interaction(interactions_file_path)
    world.learning_centers = LearningCenters.for_areas(world.areas)
    learningcenter_distributor = LearningCenterDistributor.from_file(world.learning_centers)
    learningcenter_distributor.distribute_teachers_to_learning_centers(world.areas)
    learningcenter_distributor.distribute_kids_to_learning_centers(world.areas)
    
    # hospitals
    Hospitals.get_interaction(interactions_file_path)
    IsolationUnits.get_interaction(interactions_file_path)
    
    hospitals = Hospitals.from_file(
        filename=hospitals_file_path
    )
        
    for hospital in hospitals:
        hospital.area = world.areas.get_closest_area(hospital.coordinates)
        
    world.hospitals = hospitals
    hospital_distributor = HospitalDistributor(
        hospitals, medic_min_age=20, patients_per_medic=10    )
    hospital_distributor.assign_closest_hospitals_to_super_areas(
        world.super_areas
    )

    # remaining locations
    world.isolation_units = IsolationUnits([IsolationUnit(area=hospital.area) for hospital in world.hospitals])
    hospital_distributor.distribute_medics_from_world(world.people)
    
    PumpLatrines.get_interaction(interactions_file_path)
    world.pump_latrines = PumpLatrines.for_areas(world.areas)
    
    PlayGroups.get_interaction(interactions_file_path)
    world.play_groups = PlayGroups.for_areas(world.areas)
    
    DistributionCenters.get_interaction(interactions_file_path)
    world.distribution_centers = DistributionCenters.for_areas(world.areas)
    
    Communals.get_interaction(interactions_file_path)
    world.communals = Communals.for_areas(world.areas)
    
    FemaleCommunals.get_interaction(interactions_file_path)
    world.female_communals = FemaleCommunals.for_areas(world.areas)
    
    Religiouss.get_interaction(interactions_file_path)
    world.religiouss = Religiouss.for_areas(world.areas)
    
    EVouchers.get_interaction(interactions_file_path)
    world.e_vouchers = EVouchers.for_areas(world.areas)
    
    NFDistributionCenters.get_interaction(interactions_file_path)
    world.n_f_distribution_centers = NFDistributionCenters.for_areas(world.areas)
    
    InformalWorks.get_interaction(interactions_file_path)
    world.informal_works = InformalWorks.for_areas(world.areas)

    world.cemeteries = Cemeteries()

    # cluster shelters
    Shelters.get_interaction(interactions_file_path)
    world.shelters = Shelters.for_areas(world.areas)
    shelter_distributor = ShelterDistributor(sharing_shelter_ratio = 0.75) # proportion of families that share a shelter
    for area in world.areas:
        shelter_distributor.distribute_people_in_shelters(area.shelters, area.households)

    return world

@pytest.fixture(name="camps_dummy_world", scope="session")
def make_dummy_world():
    teacher = Person.from_attributes(age=100, sex="f")
    pupil_shift_1 = Person.from_attributes(age=12, sex="f")
    pupil_shift_2 = Person.from_attributes(age=5, sex="m")
    pupil_shift_3 = Person.from_attributes(age=11, sex="f")
    learning_center = LearningCenter(coordinates=None, n_pupils_max=None)
    household = Household()
    household.add(person=teacher)
    household.add(person=pupil_shift_1)
    household.add(person=pupil_shift_2)
    household.add(person=pupil_shift_3)
    learning_center.add(
        person=teacher, shift=0, subgroup_type=learning_center.SubgroupType.teachers
    )
    learning_center.add(
        person=teacher, shift=1, subgroup_type=learning_center.SubgroupType.teachers
    )
    learning_center.add(
        person=teacher, shift=2, subgroup_type=learning_center.SubgroupType.teachers
    )
    learning_center.add(
        person=pupil_shift_1,
        shift=0,
        subgroup_type=learning_center.SubgroupType.students,
    )
    learning_center.add(
        person=pupil_shift_2,
        shift=1,
        subgroup_type=learning_center.SubgroupType.students,
    )
    learning_center.add(
        person=pupil_shift_3,
        shift=2,
        subgroup_type=learning_center.SubgroupType.students,
    )
    world = World()
    world.learning_centers = LearningCenters(
        [learning_center], learning_centers_tree=False, n_shifts=3
    )
    world.households = Households([household])
    world.people = Population([teacher, pupil_shift_1, pupil_shift_2, pupil_shift_3])
    for person in world.people.members:
        person.busy = False
    learning_center.clear()
    household.clear()
    return (
        teacher,
        pupil_shift_1,
        pupil_shift_2,
        pupil_shift_3,
        learning_center,
        household,
        world,
    )

@pytest.fixture(name="camps_selectors", scope="module")
def make_selector():
    selector = InfectionSelector.from_file()
    selector.recovery_rate = 0.05
    selector.transmission_probability = 0.7
    return InfectionSelectors([selector])

@pytest.fixture(name="camps_sim", scope="module")
def setup_sim(camps_world, camps_selectors):
    world = camps_world
    for person in world.people:
        person.immunity = Immunity()
        person.infection = None
        person.subgroups.medical_facility = None
        person.dead = False
    leisure = generate_leisure_for_config(world=world, config_filename=config_file_path)
    leisure.distribute_social_venues_to_areas(world.areas, world.super_areas)
    interaction = Interaction.from_file(config_filename=interactions_file_path)
    policies = Policies.from_file(
        policies_file_path,
        base_policy_modules=("june.policy", "camps.policy"),
    )
    epidemiology = Epidemiology(infection_selectors=camps_selectors)
    Simulator.ActivityManager = CampActivityManager
    sim = Simulator.from_file(
        world=world,
        interaction=interaction,
        leisure=leisure,
        policies=policies,
        config_filename=config_file_path,
        epidemiology=epidemiology,
    )
    
    sim.activity_manager.leisure.generate_leisure_probabilities_for_timestep(
        delta_time=3,
        working_hours=False,
        date=datetime.strptime("2020-03-01", "%Y-%m-%d"),
    )
    sim.clear_world()
    return sim
