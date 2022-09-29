import pytest
from datetime import datetime

from june.interaction import Interaction
from june.epidemiology.infection import Immunity
from june.epidemiology.epidemiology import Epidemiology
from june.simulator import Simulator
from june.policy import Policies, CloseLeisureVenue

from camps.activity import CampActivityManager
from camps.paths import camp_data_path, camp_configs_path
from camps.groups.leisure import generate_leisure_for_world, generate_leisure_for_config
from camps.camp_creation import (
    generate_empty_world,
    populate_world,
    distribute_people_to_households,
)  # this is loaded from the ../camp_scripts folder

config_file_path = camp_configs_path / "config_demo.yaml"
interactions_file_path = camp_configs_path / "defaults/interaction/interaction_Survey.yaml"

@pytest.fixture(name="policy_simulator")
def make_policy_simulator(camps_world, camps_selectors):
    world = camps_world
    for person in world.people:
        person.immunity = Immunity()
        person.infection = None
        person.subgroups.medical_facility = None
        person.dead = False
    interaction = Interaction.from_file(config_filename=interactions_file_path)
    epidemiology = Epidemiology(infection_selectors=camps_selectors)
    Simulator.ActivityManager = CampActivityManager
    sim = Simulator.from_file(
        world=world,
        interaction=interaction,
        leisure=None,
        policies=None,
        config_filename=config_file_path,
        epidemiology=epidemiology,
    )
    return sim

def test__close_venues(camps_world, policy_simulator):
    world = camps_world
    sim = policy_simulator
    close_venues = CloseLeisureVenue(
        start_time="2020-3-1", end_time="2020-3-30", venues_to_close=["pump_latrine"]
    )
    policies = Policies([close_venues])
    leisure = generate_leisure_for_config(world=world, config_filename=config_file_path)
    leisure.distribute_social_venues_to_areas(
        world.areas, super_areas=world.super_areas
    )
    sim.activity_manager.leisure = leisure
    sim.activity_manager.policies = policies
    sim.clear_world()
    time_before_policy = datetime(2019, 2, 1)
    activities = ["leisure", "residence"]
    leisure.generate_leisure_probabilities_for_timestep(
        delta_time=10000,
        working_hours=False,
        date=datetime.strptime("2020-03-02", "%Y-%m-%d"),
    )
    sim.activity_manager.move_people_to_active_subgroups(
        activities, time_before_policy, 0.0
    )
    n_pump_latrines = 0
    repetitions = 10
    for _ in range(repetitions):
        camps_sim.clear_world()
        camps_sim.activity_manager.move_people_to_active_subgroups(["leisure", "residence"])
        for person in camps_sim.world.people.members:
            if person.leisure is not None:
                n_leisure += 1
                if person.leisure.group.spec == "pump_latrine":
                    n_pump_latrines += 1
                    
    assert n_pump_latrines == 0

