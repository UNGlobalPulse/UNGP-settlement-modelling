import random
from datetime import datetime

import pytest
from june import paths
from june.activity import activity_hierarchy
from june.epidemiology.epidemiology import Epidemiology
from june.epidemiology.infection import Immunity, InfectionSelector, InfectionSelectors
from june.groups.leisure import leisure
from june.groups.travel import Travel
from june.interaction import Interaction
from june.policy import Hospitalisation, MedicalCarePolicies, Policies
from june.simulator import Simulator

from camps.activity import CampActivityManager
from camps.paths import camp_data_path, camp_configs_path
from camps.world import World
from camps.groups.leisure import generate_leisure_for_world, generate_leisure_for_config
from camps.camp_creation import (
    generate_empty_world,
    populate_world,
    distribute_people_to_households,
)  # this is loaded from the ../camp_scripts folder

config_file_path = camp_configs_path / "config_demo.yaml"
interactions_file_path = camp_configs_path / "defaults/interaction/interaction_Survey.yaml"

@pytest.fixture(name="camps_selectors", scope="module")
def make_selector():
    selector = InfectionSelector.from_file()
    selector.recovery_rate = 0.05
    selector.transmission_probability = 0.7
    return InfectionSelectors([selector])
    return selector

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
    policies = Policies.from_file()
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

def test__everyone_has_an_activity(camps_sim):
    for person in camps_sim.world.people.members:
        assert person.subgroups.iter().count(None) != len(person.subgroups.iter())

def test__apply_activity_hierarchy(camps_sim):
    unordered_activities = random.sample(activity_hierarchy, len(activity_hierarchy))
    ordered_activities = camps_sim.activity_manager.apply_activity_hierarchy(
        unordered_activities
    )
    assert ordered_activities == activity_hierarchy

def test__clear_world(camps_sim: Simulator):
    camps_sim.clear_world()
    for group_name in camps_sim.activity_manager.activities_to_super_groups(
        camps_sim.activity_manager.all_activities
    ):
        if group_name in ["shelter_visits"]:
            continue
        grouptype = getattr(camps_sim.world, group_name)
        for group in grouptype.members:
            for subgroup in group.subgroups:
                assert len(subgroup.people) == 0

    for person in camps_sim.world.people.members:
        assert person.busy is False

def test__move_to_active_subgroup(camps_sim: Simulator):
    camps_sim.activity_manager.move_to_active_subgroup(
        ["residence"], camps_sim.world.people.members[0]
    )
    assert camps_sim.world.people.members[0].residence.group.spec in ("shelter")

def test__move_people_to_leisure(camps_sim: Simulator):
    n_leisure = 0
    n_pump_latrines = 0
    n_e_vouchers = 0
    n_distributions = 0
    n_informal_works = 0
    n_n_f_distribution_centers = 0
    n_play_groups = 0
    n_religiouss = 0
    repetitions = 100
    for _ in range(repetitions):
        camps_sim.clear_world()
        camps_sim.activity_manager.move_people_to_active_subgroups(["leisure", "residence"])
        for person in camps_sim.world.people.members:
            if person.leisure is not None:
                n_leisure += 1
                if person.leisure.group.spec == "pump_latrine":
                    n_pump_latrines += 1
                elif person.leisure.group.spec == "e_voucher":
                    n_e_vouchers += 1
                elif person.leisure.group.spec == "distribution_center":
                    n_distributions += 1
                elif person.leisure.group.spec == "informal_work":
                    n_informal_works += 1
                elif person.leisure.group.spec == "n_f_distribution_center":
                    n_n_f_distribution_centers += 1
                elif person.leisure.group.spec == "play_group":
                    n_play_groups += 1
                elif person.leisure.group.spec == "religious":
                    n_religiouss += 1
                if person not in person.residence.people:
                    assert person in person.leisure.people
    assert n_leisure > 0
    assert n_pump_latrines > 0
    assert n_e_vouchers > 0
    assert n_distributions > 0
    assert n_informal_works > 0
    assert n_n_f_distribution_centers > 0
    assert n_play_groups > 0
    assert n_religiouss > 0
    camps_sim.clear_world()

def test__bury_the_dead(camps_sim: Simulator):
    dummy_person = camps_sim.world.people.members[0]
    camps_sim.epidemiology.infection_selectors.infect_person_at_time(dummy_person, 0.0)
    camps_sim.epidemiology.bury_the_dead(camps_sim.world, dummy_person)
    assert dummy_person in camps_sim.world.cemeteries.members[0].people
    assert dummy_person.dead
    assert dummy_person.infection is None
