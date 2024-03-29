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
from june.epidemiology.infection_seed import InfectionSeed, InfectionSeeds
from june.interaction import Interaction
from june.groups import Hospital, Hospitals, Cemeteries
from june.distributors import HospitalDistributor
from june.hdf5_savers import generate_world_from_hdf5
from june.policy import Policy, Policies
from june.records import Record
from june.simulator import Simulator
from june.records import Record, RecordReader

from june.tracker.tracker import Tracker
from june.tracker.tracker_plots import PlotClass

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
    "-con",
    "--config",
    help="Config file",
    required=False,
    default=camp_configs_path / "config_example.yaml",
)
parser.add_argument(
    "-p",
    "--parameters",
    help="Parameter file",
    required=False,
    default=camp_configs_path / "defaults/interaction/interaction_Survey.yaml",
)

parser.add_argument(
    "-tr",
    "--tracker",
    help="Activate Tracker for CM tracing",
    required=False,
    default="False",
)

parser.add_argument(
    "-ro", "--region_only", help="Run only one region", required=False, default="False"
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
    default="False",
)
parser.add_argument(
    "-u",
    "--isolation_units",
    help="True to include isolation units",
    required=False,
    default="False",
)
parser.add_argument(
    "-t", "--isolation_testing", help="Mean testing time", required=False, default=3
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
    default="True",
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
    default="True",
)
parser.add_argument(
    "-lch",
    "--learning_center_beta_ratio",
    help="Learning center/household beta ratio scaling",
    required=False,
    default="False",
)
parser.add_argument(
    "-pgh",
    "--play_group_beta_ratio",
    help="Play group/household beta ratio scaling",
    required=False,
    default="False",
)
parser.add_argument(
    "-s",
    "--save_path",
    help="Path of where to save logger",
    required=False,
    default="results",
)

parser.add_argument(
    "--n_seeding_days", help="number of seeding days", required=False, default=10
)
parser.add_argument(
    "--n_seeding_case_per_day",
    help="number of seeding cases per day",
    required=False,
    default=10,
)

args = parser.parse_args()
args.save_path = Path(args.save_path)

counter = 1
OG_save_path = args.save_path
while args.save_path.is_dir() is True:
    args.save_path = Path(str(OG_save_path) + "_%s" % counter)
    counter += 1
args.save_path.mkdir(parents=True, exist_ok=False)

if args.region_only == "False":
    args.region_only = False
elif args.region_only == "True":
    args.region_only = ["CXB-219"]
else:
    args.region_only = [args.region_only]


if args.tracker == "True":
    args.tracker = True
else:
    args.tracker = False

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

if args.extra_learning_centers == "True":
    args.extra_learning_centers = True
else:
    args.extra_learning_centers = False


if args.learning_center_shifts == "False":
    args.learning_center_shifts = 4

if args.learning_center_beta_ratio == "True":
    args.learning_center_beta_ratio = True
else:
    args.learning_center_beta_ratio = False

if args.play_group_beta_ratio == "True":
    args.play_group_beta_ratio = True
else:
    args.play_group_beta_ratio = False


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

if args.region_only is False:
    print("Running on all regions")
else:
    print("Running on regions: {}".format(args.region_only))

print("Play group beta ratio set to: {}".format(args.play_group_beta_ratio))
print("Save path set to: {}".format(args.save_path))

print("\n", args.__dict__, "\n")


time.sleep(10)

# =============== world creation =========================#
CONFIG_PATH = args.config

# create empty world's geography
# world = generate_empty_world({"super_area": ["CXB-219-C"]})
# world = generate_empty_world({"region": ["CXB-219", "CXB-217", "CXB-209"]})
if args.region_only is False:
    world = generate_empty_world()
else:
    world = generate_empty_world({"region": args.region_only})

print("Now populate")
# populate empty world
populate_world(world)

# distribute people to households
print("Now Distribute")
distribute_people_to_households(world)

# medical facilities
Hospitals.Get_Interaction(args.parameters)
IsolationUnits.Get_Interaction(args.parameters)

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
world.isolation_units = IsolationUnits(
    [IsolationUnit(area=hospital.area) for hospital in world.hospitals]
)

hospital_distributor.distribute_medics_from_world(world.people)

if args.learning_centers:
    LearningCenters.Get_Interaction(args.parameters)
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

    # CONFIG_PATH = camp_configs_path / "learning_center_config.yaml"

if args.no_visits:
    pass
    # CONFIG_PATH = camp_configs_path / "no_visits_config.yaml"

PumpLatrines.Get_Interaction(args.parameters)
world.pump_latrines = PumpLatrines.for_areas(world.areas)

PlayGroups.Get_Interaction(args.parameters)
world.play_groups = PlayGroups.for_areas(world.areas)

DistributionCenters.Get_Interaction(args.parameters)
world.distribution_centers = DistributionCenters.for_areas(world.areas)

Communals.Get_Interaction(args.parameters)
world.communals = Communals.for_areas(world.areas)

FemaleCommunals.Get_Interaction(args.parameters)
world.female_communals = FemaleCommunals.for_areas(world.areas)

Religiouss.Get_Interaction(args.parameters)
world.religiouss = Religiouss.for_areas(world.areas)

EVouchers.Get_Interaction(args.parameters)
world.e_vouchers = EVouchers.for_areas(world.areas)

NFDistributionCenters.Get_Interaction(args.parameters)
world.n_f_distribution_centers = NFDistributionCenters.for_areas(world.areas)

InformalWorks.Get_Interaction(args.parameters)
world.informal_works = InformalWorks.for_areas(world.areas)


print("Total people = ", len(world.people))
print("Mean age = ", np.mean([person.age for person in world.people]))
# world.box_mode = False
world.cemeteries = Cemeteries()

Shelters.Get_Interaction(args.parameters)
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

male_comorbidity_reference_prevalence_path = (
    camp_data_path / "input/demography/uk_male_comorbidities.csv"
)
female_comorbidity_reference_prevalence_path = (
    camp_data_path / "input/demography/uk_female_comorbidities.csv"
)
comorbidities_multipliers_path = camp_configs_path / "defaults/comorbidities.yaml"

immunity_setter = ImmunitySetter.from_file_with_comorbidities(
    comorbidity_multipliers_path=comorbidities_multipliers_path,
    male_comorbidity_reference_prevalence_path=male_comorbidity_reference_prevalence_path,
    female_comorbidity_reference_prevalence_path=female_comorbidity_reference_prevalence_path,
)
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
    print("Policy path set to: {}".format("defaults/policy/isolation.yaml"))

elif args.mask_wearing:
    policies = Policies.from_file(
        camp_configs_path / "defaults/policy/mask_wearing.yaml",
        base_policy_modules=("june.policy", "camps.policy"),
    )

    policies.policies[7].compliance = float(args.mask_compliance)
    policies.policies[7].beta_factor = float(args.mask_beta_factor)
    print("Policy path set to: {}".format("defaults/policy/mask_wearing.yaml"))

elif args.no_vaccines:
    policies = Policies.from_file(
        camp_configs_path / "vaccine_tests/no_vaccine.yaml",
        base_policy_modules=("june.policy", "camps.policy"),
    )
    print("Policy path set to: {}".format("vaccine_tests/no_vaccine.yaml"))

elif args.vaccines:
    policies = Policies.from_file(
        camp_configs_path / "vaccine_tests/vaccine.yaml",
        base_policy_modules=("june.policy", "camps.policy"),
    )
    print("Policy path set to: {}".format("vaccine_tests/vaccine.yaml"))

else:
    policies = Policies.from_file(
        camp_configs_path / "defaults/policy/simple_policy.yaml",
        base_policy_modules=("june.policy", "camps.policy"),
    )

    print(
        "Policy path set to: {}".format(
            camp_configs_path / "defaults/policy/simple_policy.yaml"
        )
    )

# ============================================================================#

# =================================== infection ===============================#

interaction = Interaction.from_file(config_filename=args.parameters)

selector = InfectionSelector.from_file(
    transmission_config_path=transmission_config_path
)

selectors = InfectionSelectors([selector])


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

# ============================================================================#

# =================================== seeding ================================#
# read out start date
with open(CONFIG_PATH) as file:
    config_temp = yaml.load(file, Loader=yaml.FullLoader)
    start_date = datetime.strptime(config_temp["time"]["initial_day"], "%Y-%m-%d %H:%M")

# generate seeding dataframe
N_seeding_days = int(args.n_seeding_days)

seeding_date_list = [
    start_date + timedelta(days=iday) for iday in range(N_seeding_days)
]
mi = pd.MultiIndex.from_product([seeding_date_list, ["0-100"]], names=["date", "age"])
df = pd.DataFrame(index=mi, columns=["all"])
# df = pd.DataFrame(index=mi, columns=["CXB-207"])
df[:] = args.n_seeding_case_per_day / len(world.people)

infection_seed = InfectionSeed(
    world=world,
    infection_selector=selector,
    daily_cases_per_capita_per_age_per_region=df,
)
infection_seeds = InfectionSeeds([infection_seed])

# ==================================================================================#
epidemiology = Epidemiology(
    infection_selectors=selectors,
    infection_seeds=infection_seeds,
    immunity_setter=immunity_setter,
)

# ==================================================================================#

# =================================== leisure config ===============================#
leisure = generate_leisure_for_config(world=world, config_filename=CONFIG_PATH)
# Check if shelters visits not in?

# associate social activities to shelters
leisure.distribute_social_venues_to_areas(world.areas, world.super_areas)

# ==================================================================================#

# =================================== tracker ===============================#
if args.tracker:
    group_types = [
        world.hospitals,
        world.distribution_centers,
        world.communals,
        world.female_communals,
        world.pump_latrines,
        world.religiouss,
        world.play_groups,
        world.e_vouchers,
        world.n_f_distribution_centers,
        world.shelters,
        world.learning_centers,
        world.informal_works,
        world.isolation_units,
    ]

    tracker = Tracker(
        world=world,
        record_path=args.save_path,
        group_types=group_types,
        load_interactions_path=args.parameters,
        contact_sexes=["unisex", "male", "female"],
    )
else:
    tracker = None


# ==================================================================================#

# =================================== simulator ===============================#

# records
record = Record(record_path=args.save_path, record_static_data=True)
# record.static_data(world=world)


Simulator.ActivityManager = CampActivityManager
simulator = Simulator.from_file(
    world=world,
    interaction=interaction,
    tracker=tracker,
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

locations_df.to_csv(args.save_path / "locations.csv")

# ==================================================================================#

# =================================== tracker figures ===============================#

if args.tracker:
    simulator.tracker.contract_matrices("AC", np.array([0, 18, 60]))
    simulator.tracker.contract_matrices("All", np.array([0, 100]))
    simulator.tracker.post_process_simulation(save=True)
