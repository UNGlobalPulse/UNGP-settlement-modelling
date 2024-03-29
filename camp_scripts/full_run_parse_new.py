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
import random
import numba as nb
import pandas as pd
import time
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys
import argparse
from pathlib import Path
import yaml

from collections import defaultdict

from june.geography import Geography
from june.demography.demography import (
    load_age_and_sex_generators_for_bins,
    Demography,
    Population,
    load_comorbidity_data,
    generate_comorbidity,
)
from june.paths import data_path, configs_path
from june.epidemiology.epidemiology import Epidemiology
from june.epidemiology.infection import ImmunitySetter
from june.epidemiology.infection import (
    Infection,
    HealthIndexGenerator,
    InfectionSelector,
    InfectionSelectors,
)
from june.epidemiology.infection_seed import (
    InfectionSeed,
    InfectionSeeds,
    ExactNumClusteredInfectionSeed,
    ExactNumInfectionSeed,
)
from june.interaction import Interaction
from june.groups import Hospital, Hospitals, Cemeteries
from june.distributors import HospitalDistributor
from june.hdf5_savers import generate_world_from_hdf5
from june.policy import Policy, Policies
from june.simulator import Simulator
from june.records import Record, RecordReader

from camps.activity import CampActivityManager
from camps.paths import camp_data_path, camp_configs_path
from camps.world import World
from camps.groups.leisure import generate_leisure_for_world, generate_leisure_for_config
from camps.camp_creation import (
    generate_empty_world,
    populate_world,
    distribute_people_to_households,
)  # this is loaded from the ../camp_scripts folder

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


set_random_seed(0)

# =============== Argparse =========================#

parser = argparse.ArgumentParser(description="Full run of the camp")

parser.add_argument(
    "-c",
    "--comorbidities",
    help="True to include comorbidities",
    required=False,
    default="True",
)
parser.add_argument(
    "-p",
    "--parameters",
    help="Parameter file",
    required=False,
    default="interaction_Survey.yaml",
)
parser.add_argument(
    "-hb", "--household_beta", help="Household beta", required=False, default=0.25
)
parser.add_argument(
    "-nnv",
    "--no_vaccines",
    help="Implement no vaccine policies",
    required=False,
    default="False",
)
parser.add_argument(
    "-v",
    "--vaccines",
    help="Implement vaccine policies",
    required=False,
    default="False",
)
parser.add_argument(
    "-nv", "--no_visits", help="No shelter visits", required=False, default="False"
)
parser.add_argument(
    "-ih",
    "--indoor_beta_ratio",
    help="Indoor/household beta ratio scaling",
    required=False,
    default=0.55,
)
parser.add_argument(
    "-oh",
    "--outdoor_beta_ratio",
    help="Outdoor/household beta ratio scaling",
    required=False,
    default=0.05,
)
parser.add_argument(
    "-inf",
    "--infectiousness_path",
    help="path to infectiousness parameter file",
    required=False,
    default="nature",
)
parser.add_argument(
    "-cs",
    "--child_susceptibility",
    help="Reduce child susceptibility for under 12s",
    required=False,
    default=False,
)
parser.add_argument(
    "-u",
    "--isolation_units",
    help="True to include isolation units",
    required=False,
    default="False",
)
parser.add_argument(
    "-t",
    "--isolation_testing",
    help="Mean testing time",
    required=False,
    default=3,
)
parser.add_argument(
    "-i", "--isolation_time", help="Ouput file name", required=False, default=7
)
parser.add_argument(
    "-ic",
    "--isolation_compliance",
    help="Isolation unit self reporting compliance",
    required=False,
    default=0.6,
)
parser.add_argument(
    "-m",
    "--mask_wearing",
    help="True to include mask wearing",
    required=False,
    default="False",
)
parser.add_argument(
    "-mc",
    "--mask_compliance",
    help="Mask wearing compliance",
    required=False,
    default="False",
)
parser.add_argument(
    "-mb",
    "--mask_beta_factor",
    help="Mask beta factor reduction",
    required=False,
    default=0.5,
)
parser.add_argument(
    "-lc",
    "--learning_centers",
    help="Add learning centers",
    required=False,
    default=False,
)
parser.add_argument(
    "-lcs",
    "--learning_center_shifts",
    help="Number of learning center shifts",
    required=False,
    default=4,
)
parser.add_argument(
    "-lce",
    "--extra_learning_centers",
    help="Number of learning centers to add based on enrolment",
    required=False,
    default=False,
)
parser.add_argument(
    "-lch",
    "--learning_center_beta_ratio",
    help="Learning center/household beta ratio scaling",
    required=False,
    default=False,
)
parser.add_argument(
    "-pgh",
    "--play_group_beta_ratio",
    help="Play group/household beta ratio scaling",
    required=False,
    default=False,
)

parser.add_argument(
    "--n_seeding_days",
    help="number of seeding days",
    default=10,
)
parser.add_argument(
    "--n_seeding_case_per_day",
    help="number of seeding cases per day",
    required=False,
    default=10,
)
parser.add_argument(
    "--comorbidity_scaling",
    help=" comorbidity_scaling",
    required=False,
    default=False,
)
parser.add_argument(
    "--male_life_expectancy",
    help=" male_life_expectancy",
    required=False,
    default=79.4,
)
parser.add_argument(
    "--female_life_expectancy",
    help=" female_life_expectancy",
    required=False,
    default=83.1,
)
parser.add_argument(
    "--cut_off_age",
    help=" cut off age for life_expectancy",
    required=False,
    default=16,
)
parser.add_argument(
    "--cluster_seeding",
    help="Whether to use cluster seeding or not",
    required=False,
    default=True,
)
parser.add_argument(
    "--nearest_venues_to_visit",
    help="nearest_venues_to_visit, override neighbours_to_consider",
    required=False,
    default=3,
)
parser.add_argument(
    "-s",
    "--save_path",
    help="Path of where to save logger",
    required=False,
    default="results",
)
args = parser.parse_args()

if args.comorbidities == "True":
    args.comorbidities = True
else:
    args.comorbidities = False

if args.child_susceptibility == "True":
    args.child_susceptibility = True
else:
    args.child_susceptibility = False
if args.no_vaccines == "True":
    args.no_vaccines = True
else:
    args.no_vaccines = False
if args.vaccines == "True":
    args.vaccines = True
else:
    args.vaccines = False

if args.no_visits == "True":
    args.no_visits = True
else:
    args.no_visits = False

if args.isolation_units == "True":
    args.isolation_units = True
else:
    args.isolation_units = False

if args.mask_wearing == "True":
    args.mask_wearing = True
else:
    args.mask_wearing = False

if args.learning_centers == "True":
    args.learning_centers = True
else:
    args.learning_centers = False

if args.extra_learning_centers == "False":
    args.extra_learning_centers = False

if args.learning_center_shifts == "False":
    args.learning_center_shifts = 4

if args.learning_center_beta_ratio == "False":
    args.learning_center_beta_ratio = False

if args.cluster_seeding == "True":
    args.cluster_seeding = True
else:
    args.cluster_seeding = False

if args.infectiousness_path == "nature":
    transmission_config_path = camp_configs_path / "defaults/transmission/nature.yaml"
elif args.infectiousness_path == "correction_nature":
    transmission_config_path = (
        camp_configs_path / "defaults/transmission/correction_nature.yaml"
    )
elif args.infectiousness_path == "nature_larger":
    transmission_config_path = (
        camp_configs_path
        / "defaults/transmission/nature_larger_presymptomatic_transmission.yaml"
    )
elif args.infectiousness_path == "nature_lower":
    transmission_config_path = (
        camp_configs_path
        / "defaults/transmission/nature_lower_presymptomatic_transmission.yaml"
    )
elif args.infectiousness_path == "xnexp":
    transmission_config_path = camp_configs_path / "defaults/transmission/XNExp.yaml"
else:
    raise NotImplementedError

print("Comorbidities set to: {}".format(args.comorbidities))
print("Comorbidities scaling set to: {}".format(args.comorbidity_scaling))
print("camp male life expectancy set to: {}".format(args.male_life_expectancy))
print("camp female life expectancy set to: {}".format(args.female_life_expectancy))
print("Reference UK life expectancy F:83.1, M:79.4")
print("Parameters path set to: {}".format(args.parameters))
print("Indoor beta ratio is set to: {}".format(args.indoor_beta_ratio))
print("Outdoor beta ratio set to: {}".format(args.outdoor_beta_ratio))
print("Infectiousness path set to: {}".format(args.infectiousness_path))
print("Child susceptibility change set to: {}".format(args.child_susceptibility))

print("Isolation units set to: {}".format(args.isolation_units))
print("Household beta set to: {}".format(args.household_beta))
if args.isolation_units:
    print("Testing time set to: {}".format(args.isolation_testing))
    print("Isolation time set to: {}".format(args.isolation_time))
    print("Isolation compliance set to: {}".format(args.isolation_compliance))

print("Mask wearing set to: {}".format(args.mask_wearing))
if args.mask_wearing:
    print("Mask compliance set to: {}".format(args.mask_compliance))
    print("Mask beta factor set up: {}".format(args.mask_beta_factor))

print("Learning centers set to: {}".format(args.learning_centers))
if args.learning_centers:
    print(
        "Learning center beta ratio set to: {}".format(args.learning_center_beta_ratio)
    )
    print("Learning center shifts set to: {}".format(args.learning_center_shifts))
    print("Extra learning centers is set to: {}".format(args.extra_learning_centers))

print("Plag group beta ratio set to: {}".format(args.play_group_beta_ratio))
print("Save path set to: {}".format(args.save_path))

print("\n", args.__dict__, "\n")
time.sleep(10)

# =============== world creation =========================#
CONFIG_PATH = camp_configs_path / "config_example.yaml"

# create empty world's geography
# world = generate_empty_world({"super_area": ["CXB-219-C"]})
# world = generate_empty_world({"region": ["CXB-219", "CXB-217", "CXB-209"]})
world = generate_empty_world({"region": ["CXB-219"]})
# world = generate_empty_world()

# populate empty world
populate_world(world)

# distribute people to households
distribute_people_to_households(world)

# medical facilities
hospitals = Hospitals.from_file(
    filename=camp_data_path / "input/hospitals/hospitals.csv"
)
for hospital in hospitals:
    hospital.area = world.areas.get_closest_area(hospital.coordinates)
world.hospitals = hospitals
hospital_distributor = HospitalDistributor(
    hospitals, medic_min_age=20, patients_per_medic=10
)
hospital_distributor.assign_closest_hospitals_to_super_areas(world.super_areas)

if args.isolation_units:
    world.isolation_units = IsolationUnits([IsolationUnit(area=world.areas[0])])

hospital_distributor.distribute_medics_from_world(world.people)

if args.learning_centers:
    world.learning_centers = LearningCenters.for_areas(
        world.areas, n_shifts=int(args.learning_center_shifts)
    )
    learning_center_distributor = LearningCenterDistributor.from_file(
        learning_centers=world.learning_centers
    )
    learning_center_distributor.distribute_kids_to_learning_centers(world.areas)
    learning_center_distributor.distribute_teachers_to_learning_centers(world.areas)

    if args.extra_learning_centers:
        # add extra learning centers based on enrollment
        enrolled = []
        learning_centers = []
        # find current enrollment rates
        for learning_center in world.learning_centers:
            total = 0
            for i in range(4):
                total += len(learning_center.ids_per_shift[i])
            enrolled.append(total)
            learning_centers.append(learning_center)
        learning_centers = np.array(learning_centers)
        learning_centers_sorted = learning_centers[np.argsort(enrolled)]

        # find top k most filled learning centers
        top_k = learning_centers_sorted[-int(args.extra_learning_centers) :]
        for learning_center in top_k:
            extra_lc = LearningCenter(
                coordinates=learning_center.super_area.coordinates
            )
            extra_lc.area = learning_center.area
            world.learning_centers.members.append(extra_lc)
        world.learning_centers = LearningCenters(
            world.learning_centers.members, n_shifts=4
        )

        # clear and redistirbute kids to learning centers
        for learning_center in world.learning_centers:
            learning_center.ids_per_shift = defaultdict(list)
        learning_center_distributor = LearningCenterDistributor.from_file(
            learning_centers=world.learning_centers
        )
        learning_center_distributor.distribute_kids_to_learning_centers(world.areas)
        learning_center_distributor.distribute_teachers_to_learning_centers(world.areas)

    CONFIG_PATH = camp_configs_path / "learning_center_config.yaml"

if args.no_visits:
    CONFIG_PATH = camp_configs_path / "no_visits_config.yaml"

world.pump_latrines = PumpLatrines.for_areas(world.areas)
world.play_groups = PlayGroups.for_areas(world.areas)
world.distribution_centers = DistributionCenters.for_areas(world.areas)
world.communals = Communals.for_areas(world.areas)
world.female_communals = FemaleCommunals.for_areas(world.areas)
world.religiouss = Religiouss.for_areas(world.areas)
world.e_vouchers = EVouchers.for_areas(world.areas)
world.n_f_distribution_centers = NFDistributionCenters.for_areas(world.areas)

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

if args.comorbidities:

    comorbidity_data = load_comorbidity_data(
        camp_data_path / "input/demography/myanmar_male_comorbidities.csv",
        camp_data_path / "input/demography/myanmar_female_comorbidities.csv",
    )
    for person in world.people:
        person.comorbidity = generate_comorbidity(person, comorbidity_data)

else:
    print("WARNING: no comorbidities. All people are super health as ini conditon")
    # health_index_generator = HealthIndexGenerator.from_file()

# ============================================================================#

# =================================== policies ===============================#

if args.isolation_units:
    policies = Policies.from_file(
        camp_configs_path / "defaults/policy/isolation.yaml",
        base_policy_modules=("june.policy", "camps.policy"),
    )

    policies.policies[3].n_quarantine_days = int(args.isolation_time)
    policies.policies[3].testing_mean_time = int(args.isolation_testing)
    policies.policies[3].compliance = float(args.isolation_compliance)

elif args.mask_wearing:
    policies = Policies.from_file(
        camp_configs_path / "defaults/policy/mask_wearing.yaml",
        base_policy_modules=("june.policy", "camps.policy"),
    )

    policies.policies[7].compliance = float(args.mask_compliance)
    policies.policies[7].beta_factor = float(args.mask_beta_factor)

elif args.no_vaccines:
    policies = Policies.from_file(
        camp_configs_path / "vaccine_tests/no_vaccine.yaml",
        base_policy_modules=("june.policy", "camps.policy"),
    )

elif args.vaccines:
    policies = Policies.from_file(
        camp_configs_path / "vaccine_tests/vaccine.yaml",
        base_policy_modules=("june.policy", "camps.policy"),
    )

else:
    policies = Policies.from_file(
        camp_configs_path / "defaults/policy/home_care_policy.yaml",
        base_policy_modules=("june.policy", "camps.policy"),
    )

# ============================================================================#

# =================================== betas ===============================#

interaction = Interaction.from_file(
    config_filename=camp_configs_path / "defaults/interaction/" / args.parameters
)

if args.household_beta:
    interaction.betas["household"] = float(args.household_beta)
    interaction.betas["hospital"] = float(args.household_beta) * 0.1
    interaction.betas["shelter"] = float(args.household_beta)

if args.outdoor_beta_ratio:
    interaction.betas["play_group"] = interaction.betas["household"] * float(
        args.outdoor_beta_ratio
    )
    interaction.betas["pump_latrine"] = interaction.betas["household"] * float(
        args.outdoor_beta_ratio
    )

if args.indoor_beta_ratio:
    interaction.betas["communal"] = interaction.betas["household"] * float(
        args.indoor_beta_ratio
    )
    interaction.betas["female_communal"] = interaction.betas["household"] * float(
        args.indoor_beta_ratio
    )
    interaction.betas["religious"] = interaction.betas["household"] * float(
        args.indoor_beta_ratio
    )
    interaction.betas["distribution_center"] = interaction.betas["household"] * float(
        args.indoor_beta_ratio
    )
    interaction.betas["n_f_distribution_center"] = interaction.betas[
        "household"
    ] * float(args.indoor_beta_ratio)
    interaction.betas["e_voucher"] = interaction.betas["household"] * float(
        args.indoor_beta_ratio
    )
    interaction.betas["learning_center"] = interaction.betas["household"] * float(
        args.indoor_beta_ratio
    )

if args.learning_centers and args.learning_center_beta_ratio:
    interaction.betas["learning_center"] = interaction.betas["household"] * float(
        args.learning_center_beta_ratio
    )

if args.play_group_beta_ratio:
    interaction.betas["play_group"] = interaction.betas["household"] * float(
        args.play_group_beta_ratio
    )

# ============================ infection ============================#
HealthIndex = HealthIndexGenerator.from_file(
    m_exp=float(args.male_life_expectancy),
    f_exp=float(args.female_life_expectancy),
    cutoff_age=np.round(float(args.cut_off_age)),
)
selector = InfectionSelector(
    transmission_config_path=transmission_config_path,
    health_index_generator=HealthIndex,
)
selectors = InfectionSelectors([selector])

# =================================== seeding ================================#
# read out start date
with open(CONFIG_PATH) as file:
    config_temp = yaml.load(file, Loader=yaml.FullLoader)


start_date = datetime.strptime(config_temp["time"]["initial_day"], "%Y-%m-%d %H:%M")

#### read daytypes from config
default_daytypes = {}
default_daytypes["weekend"] = config_temp["weekend"]
default_daytypes["weekday"] = config_temp["weekday"]
####

# generate seeding dataframe
N_seeding_days = int(args.n_seeding_days)

seeding_date_list = [
    start_date + timedelta(days=iday) for iday in range(N_seeding_days)
]
mi = pd.MultiIndex.from_product([seeding_date_list, ["0-100"]], names=["date", "age"])
df = pd.DataFrame(index=mi, columns=["all"])
# df = pd.DataFrame(index=mi, columns=["CXB-207"])
df[:] = int(args.n_seeding_case_per_day)

print("#### seeding df:")
print(df)
print("####")

###################################################################################
if args.cluster_seeding:
    infection_seed = ExactNumClusteredInfectionSeed(
        world=world,
        infection_selector=selector,
        daily_cases_per_capita_per_age_per_region=df,
    )
else:
    infection_seed = ExactNumInfectionSeed(
        world=world,
        infection_selector=selector,
        daily_cases_per_capita_per_age_per_region=df,
    )
infection_seeds = InfectionSeeds([infection_seed])

######################### comorbidity scaling ################################
male_comorbidity_reference_prevalence_path = (
    camp_data_path / "input/demography/uk_male_comorbidities.csv"
)
female_comorbidity_reference_prevalence_path = (
    camp_data_path / "input/demography/uk_female_comorbidities.csv"
)

comorbidities_multipliers_path = camp_configs_path / "defaults/comorbidities.yaml"
if args.comorbidity_scaling:
    with open(comorbidities_multipliers_path) as file:
        config_temp = yaml.load(file, Loader=yaml.FullLoader)
    for key in config_temp:
        config_temp[key] *= float(args.comorbidity_scaling)
    config_temp["no_condition"] = 1.0
    comorbidities_multipliers_path = args.save_path + "/comorbidities_multipliers.yaml"
    with open(comorbidities_multipliers_path, "w") as file:
        yaml.dump(config_temp, file)


###################################################################################
print(comorbidities_multipliers_path)
print(male_comorbidity_reference_prevalence_path)
print(female_comorbidity_reference_prevalence_path)
print("####")

immunity_setter = ImmunitySetter.from_file_with_comorbidities(
    comorbidity_multipliers_path=comorbidities_multipliers_path,
    male_comorbidity_reference_prevalence_path=male_comorbidity_reference_prevalence_path,
    female_comorbidity_reference_prevalence_path=female_comorbidity_reference_prevalence_path,
)
####
epidemiology = Epidemiology(
    infection_selectors=selectors,
    infection_seeds=infection_seeds,
    immunity_setter=immunity_setter,
)

# =================================== leisure config ===============================#
group_config_override = {
    "maximum_distance": 1.0,
    "nearest_venues_to_visit": int(args.nearest_venues_to_visit),
}
####
leisure = generate_leisure_for_config(world=world, config_filename=CONFIG_PATH)
leisure.leisure_distributors = {}
leisure.leisure_distributors["pump_latrine"] = PumpLatrineDistributor.from_config(
    world.pump_latrines
)
leisure.leisure_distributors["play_group"] = PlayGroupDistributor.from_config(
    world.play_groups
)
leisure.leisure_distributors[
    "distribution_center"
] = DistributionCenterDistributor.from_config(
    world.distribution_centers, config_override=group_config_override
)
leisure.leisure_distributors["communal"] = CommunalDistributor.from_config(
    world.communals, config_override=group_config_override
)
leisure.leisure_distributors["female_communal"] = FemaleCommunalDistributor.from_config(
    world.female_communals, config_override=group_config_override
)
leisure.leisure_distributors["religious"] = ReligiousDistributor.from_config(
    world.religiouss, config_override=group_config_override
)
leisure.leisure_distributors["e_voucher"] = EVoucherDistributor.from_config(
    world.e_vouchers, config_override=group_config_override
)
leisure.leisure_distributors[
    "n_f_distribution_center"
] = NFDistributionCenterDistributor.from_config(
    world.n_f_distribution_centers, config_override=group_config_override
)
if not args.no_visits:
    leisure.leisure_distributors[
        "shelters_visits"
    ] = SheltersVisitsDistributor.from_config(daytypes=default_daytypes)
    leisure.leisure_distributors["shelters_visits"].link_shelters_to_shelters(
        world.super_areas
    )
# associate social activities to shelters
leisure.distribute_social_venues_to_areas(world.areas, world.super_areas)

# ==================================================================================#

# =================================== simulator ===============================#

# records
record = Record(record_path=args.save_path, record_static_data=True)
# record.static_data(world=world)


Simulator.ActivityManager = CampActivityManager
simulator = Simulator.from_file(
    world=world,
    interaction=interaction,
    leisure=leisure,
    policies=policies,
    config_filename=CONFIG_PATH,
    epidemiology=epidemiology,
    record=record,
)

leisure.leisure_distributors

simulator.timer.reset()

simulator.run()

# ==================================================================================#

# =================================== read logger ===============================#

read = RecordReader(args.save_path)

infections_df = read.get_table_with_extras("infections", "infected_ids")

locations_df = infections_df.groupby(["location_specs", "timestamp"]).size()

locations_df.to_csv(args.save_path + "/locations.csv")
