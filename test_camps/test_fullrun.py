from pathlib import Path

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
from june.epidemiology.infection import Infection, HealthIndexGenerator, InfectionSelector, InfectionSelectors
from june.epidemiology.infection_seed import InfectionSeed, InfectionSeeds
from june.interaction import Interaction
from june.groups import Hospital, Hospitals, Cemeteries
from june.distributors import HospitalDistributor
from june.hdf5_savers import generate_world_from_hdf5
from june.policy import Policy, Policies
from june.records import Record
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
) 

results_path = Path("results")
config_file_path = camp_configs_path / "config_demo.yaml"
interactions_file_path = camp_configs_path / "defaults/interaction/interaction_Survey.yaml"
policies_file_path = camp_configs_path / "defaults/policy/simple_policy.yaml"
comorbidity_multipliers_path = camp_configs_path / "defaults/comorbidities.yaml"
male_comorbidity_reference_prevalence_path = data_path / "input/demography/uk_male_comorbidities.csv"
female_comorbidity_reference_prevalence_path = data_path / "input/demography/uk_female_comorbidities.csv"

def test__full_run(camps_world):
    world = camps_world
    selector = InfectionSelector.from_file()
    selectors = InfectionSelectors([selector])

    interaction = Interaction.from_file(
        config_filename=interactions_file_path,
    )

    policies = Policies.from_file(
        policies_file_path,
        base_policy_modules=("june.policy", "camps.policy"),
    )

    infection_seed = InfectionSeed.from_uniform_cases(
        world=world,
        infection_selector=selector,
        cases_per_capita=0.01,
        date="2020-05-24 9:00",
        seed_past_infections=False,
    )
    infection_seeds = InfectionSeeds([infection_seed])

    immunity_setter = ImmunitySetter.from_file_with_comorbidities(
        comorbidity_multipliers_path= comorbidity_multipliers_path,
        male_comorbidity_reference_prevalence_path= male_comorbidity_reference_prevalence_path,
        female_comorbidity_reference_prevalence_path = female_comorbidity_reference_prevalence_path,   
    )

    epidemiology = Epidemiology(
        infection_selectors=selectors,
        infection_seeds=infection_seeds,
        immunity_setter=immunity_setter,
    )

    
    leisure = generate_leisure_for_config(world=world, config_filename=config_file_path)
    leisure.distribute_social_venues_to_areas(world.areas, world.super_areas)

    record = Record(
        record_path=results_path, 
        record_static_data=True
    )

    Simulator.ActivityManager = CampActivityManager
    simulator = Simulator.from_file(
        world=world,
        interaction=interaction,
        leisure=leisure,
        policies=policies,
        config_filename=config_file_path,
        epidemiology=epidemiology,
        record=record,
    )

    simulator.run()
    for region in world.regions:
        region.policy["local_closed_venues"] = set()
        region.policy["global_closed_venues"] = set()

    del world
