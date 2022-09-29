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
import random
from collections import defaultdict

from june.demography import Person, Population
from june.groups import Household, Households, Hospital, Hospitals, Cemeteries
from june.distributors import HospitalDistributor
from june.world import World
from june.epidemiology.infection import Immunity, InfectionSelector, InfectionSelectors

from camps.paths import camp_data_path, camp_configs_path
from camps.camp_creation import (
    generate_empty_world,
    populate_world,
    distribute_people_to_households,
)
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


@pytest.fixture(name="camps_world", scope="module")
def generate_camp():
    
    interactions_file_path = camp_configs_path / "defaults/interaction/interaction_Survey.yaml"
    hospitals_file_path = camp_data_path / "input/hospitals/hospitals.csv"
    
    world = generate_empty_world({"region": ["CXB-219"]})
    populate_world(world)
    # distribute people to households
    distribute_people_to_households(world)

    # learning_centers
    LearningCenters.Get_Interaction(interactions_file_path)
    world.learning_centers = LearningCenters.for_areas(world.areas)
    learningcenter_distributor = LearningCenterDistributor.from_file(world.learning_centers)
    learningcenter_distributor.distribute_teachers_to_learning_centers(world.areas)
    learningcenter_distributor.distribute_kids_to_learning_centers(world.areas)
    
    # hospitals
    Hospitals.Get_Interaction(interactions_file_path)
    IsolationUnits.Get_Interaction(interactions_file_path)
    
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
    
    PumpLatrines.Get_Interaction(interactions_file_path)
    world.pump_latrines = PumpLatrines.for_areas(world.areas)
    
    PlayGroups.Get_Interaction(interactions_file_path)
    world.play_groups = PlayGroups.for_areas(world.areas)
    
    DistributionCenters.Get_Interaction(interactions_file_path)
    world.distribution_centers = DistributionCenters.for_areas(world.areas)
    
    Communals.Get_Interaction(interactions_file_path)
    world.communals = Communals.for_areas(world.areas)
    
    FemaleCommunals.Get_Interaction(interactions_file_path)
    world.female_communals = FemaleCommunals.for_areas(world.areas)
    
    Religiouss.Get_Interaction(interactions_file_path)
    world.religiouss = Religiouss.for_areas(world.areas)
    
    EVouchers.Get_Interaction(interactions_file_path)
    world.e_vouchers = EVouchers.for_areas(world.areas)
    
    NFDistributionCenters.Get_Interaction(interactions_file_path)
    world.n_f_distribution_centers = NFDistributionCenters.for_areas(world.areas)
    
    InformalWorks.Get_Interaction(interactions_file_path)
    world.informal_works = InformalWorks.for_areas(world.areas)

    world.cemeteries = Cemeteries()

    # cluster shelters
    Shelters.Get_Interaction(interactions_file_path)
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
    return selector
