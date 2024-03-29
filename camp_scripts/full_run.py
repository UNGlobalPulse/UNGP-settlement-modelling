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
import matplotlib.pyplot as plt
import pandas as pd
import time
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import sys

from june.demography.geography import Geography
from june.demography.demography import (
    load_age_and_sex_generators_for_bins,
    Demography,
    Population,
    load_comorbidity_data,
    generate_comorbidity,
)
from june.paths import data_path, configs_path
from june.infection import Infection, HealthIndexGenerator
from june.infection_seed import InfectionSeed
from june.infection.infection import InfectionSelector
from june.interaction import Interaction
from june.groups import Hospital, Hospitals
from june.distributors import HospitalDistributor
from june.world import generate_world_from_hdf5
from june.groups import Cemeteries
from june.policy import Policy, Policies
from june.logger.read_logger import ReadLogger
from june.simulator import Simulator

from camps.activity import CampActivityManager
from camps.paths import camp_data_path, camp_configs_path
from camps.world import World
from camps.groups.leisure import generate_leisure_for_world, generate_leisure_for_config
from camp_creation import (
    generate_empty_world,
    populate_world,
    distribute_people_to_households,
)  # this is loaded from the ../camp_scripts folder

from camps.groups import PumpLatrines, PumpLatrineDistributor
from camps.groups import PlayGroups, PlayGroupDistributor
from camps.groups import DistributionCenters, DistributionCenterDistributor
from camps.groups import Communals, CommunalDistributor
from camps.groups import FemaleCommunals, FemaleCommunalDistributor
from camps.groups import Religiouss, ReligiousDistributor
from camps.groups import Shelter, Shelters, ShelterDistributor
from camps.groups import IsolationUnit, IsolationUnits
from camps.groups import LearningCenters
from camps.distributors import LearningCenterDistributor
from june.groups.leisure import HouseholdVisitsDistributor

# =============== world creation =========================#

# create empty world's geography
# world = generate_empty_world({"super_area": ["CXB-219-C"]})
# world = generate_empty_world({"region": ["CXB-219", "CXB-217"]})
world = generate_empty_world()

# populate empty world
populate_world(world)

# distribute people to households
distribute_people_to_households(world)

# medical facilities
hospitals = Hospitals.from_file(
    filename=camp_data_path / "input/hospitals/hospitals.csv"
)
world.hospitals = hospitals
hospital_distributor = HospitalDistributor(
    hospitals, medic_min_age=20, patients_per_medic=10
)
world.isolation_units = IsolationUnits([IsolationUnit()])

hospital_distributor.distribute_medics_from_world(world.people)

world.learning_centers = LearningCenters.for_areas(world.areas, n_shifts=4)
learning_center_distributor = LearningCenterDistributor.from_file(
    learning_centers=world.learning_centers
)
learning_center_distributor.distribute_kids_to_learning_centers(world.areas)
learning_center_distributor.distribute_teachers_to_learning_centers(world.areas)
world.pump_latrines = PumpLatrines.for_areas(world.areas)
world.play_groups = PlayGroups.for_areas(world.areas)
world.distribution_centers = DistributionCenters.for_areas(world.areas)
world.communals = Communals.for_areas(world.areas)
world.female_communals = FemaleCommunals.for_areas(world.areas)
world.religiouss = Religiouss.for_areas(world.areas)

print("Total people = ", len(world.people))
print("Mean age = ", np.mean([person.age for person in world.people]))
# world.box_mode = False
world.cemeteries = Cemeteries()

world.shelters = Shelters.for_areas(world.areas)
shelter_distributor = ShelterDistributor(
    sharing_shelter_ratio=0.75
)  # proportion of families that share a shelter
for area in world.areas:
    shelter_distributor.distribute_people_in_shelters(area.shelters, area.households)

# ============================================================================#

# =================================== comorbidities ===============================#


comorbidity_data = load_comorbidity_data(
    camp_data_path / "input/demography/myanmar_male_comorbidities.csv",
    camp_data_path / "input/demography/myanmar_female_comorbidities.csv",
)
for person in world.people:
    person.comorbidity = generate_comorbidity(person, comorbidity_data)

health_index_generator = HealthIndexGenerator.from_file_with_comorbidities(
    camp_configs_path / "defaults/comorbidities.yaml",
    camp_data_path / "input/demography/uk_male_comorbidities.csv",
    camp_data_path / "input/demography/uk_female_comorbidities.csv",
    asymptomatic_ratio=0.2,
)


# UNCOMMENT THE BELOW AND COMMENT THE ABOVE TO REMOVE COMORBIDITIES

# health_index_generator = HealthIndexGenerator.from_file(asymptomatic_ratio=0.2)

# ============================================================================#

# =================================== policies ===============================#

policies = Policies.from_file(
    camp_configs_path / "defaults/policy/home_care_policy.yaml",
    base_policy_modules=("june.policy", "camps.policy"),
)

# ============================================================================#

# =================================== infection ===============================#


selector = InfectionSelector.from_file(health_index_generator=health_index_generator)

interaction = Interaction.from_file(
    config_filename=camp_configs_path
    / "defaults/interaction/ContactInteraction_med_low_low_low.yaml"
)


cases_detected = {
    "CXB-202": 3,
    "CXB-204": 6,
    "CXB-208": 8,
    "CXB-203": 1,
    "CXB-207": 2,
    "CXB-213": 2,
}  # By the 24th May

print("Detected cases = ", sum(cases_detected.values()))

msoa_region_filename = camp_data_path / "input/geography/area_super_area_region.csv"
msoa_region = pd.read_csv(msoa_region_filename)[["super_area", "region"]]
infection_seed = InfectionSeed(
    super_areas=world.super_areas, selector=selector, msoa_region=msoa_region
)

for key, n_cases in cases_detected.items():
    infection_seed.unleash_virus_regional_cases(key, n_cases * 10)
# Add some extra random cases
infection_seed.unleash_virus(n_cases=100)

print("Infected people in seed = ", len(world.people.infected))

CONFIG_PATH = camp_configs_path / "learning_center_config.yaml"

# ==================================================================================#

# =================================== leisure config ===============================#
leisure_instance = generate_leisure_for_config(world=world, config_filename=CONFIG_PATH)
leisure_instance.leisure_distributors = {}
leisure_instance.leisure_distributors[
    "pump_latrines"
] = PumpLatrineDistributor.from_config(pump_latrines=world.pump_latrines)
leisure_instance.leisure_distributors["play_groups"] = PlayGroupDistributor.from_config(
    play_groups=world.play_groups
)
leisure_instance.leisure_distributors[
    "distribution_centers"
] = DistributionCenterDistributor.from_config(
    distribution_centers=world.distribution_centers
)
leisure_instance.leisure_distributors["communals"] = CommunalDistributor.from_config(
    communals=world.communals
)
leisure_instance.leisure_distributors[
    "female_communals"
] = FemaleCommunalDistributor.from_config(female_communals=world.female_communals)

# associate social activities to shelters
leisure_instance.distribute_social_venues_to_households(world.shelters)

# ==================================================================================#

# =================================== simulator ===============================#
Simulator.ActivityManager = CampActivityManager
simulator = Simulator.from_file(
    world=world,
    interaction=interaction,
    leisure=leisure_instance,
    policies=policies,
    config_filename=CONFIG_PATH,
    infection_selector=selector,
    save_path="results_no_comorbidities",
)

leisure_instance.leisure_distributors

simulator.timer.reset()

simulator.run()

# ==================================================================================#
