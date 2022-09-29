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

def test__close_venues(camps_sim):
    sim = camps_sim
    close_venues = CloseLeisureVenue(
        start_time="2020-05-01", end_time="2021-01-01", venues_to_close=["pump_latrine", "distribution_center"]
    )
    policies = Policies([close_venues])
    sim.activity_manager.policies = policies
    sim.clear_world()
    activities = ["leisure", "residence"]
    leisure = sim.activity_manager.leisure

    time_before_policy = datetime(2019, 2, 5, 10)
    time_during_policy = datetime(2020, 5, 5, 10)
    time_after_policy = datetime(2021, 5, 5, 10)

    # Before policy
    sim.activity_manager.policies.leisure_policies.apply(date=time_before_policy, leisure=leisure)
    sim.activity_manager.leisure.generate_leisure_probabilities_for_timestep(
        delta_time=10000,
        working_hours=False,
        date=datetime.strptime("2019-03-02-10", "%Y-%m-%d-%H"),
    )
    sim.activity_manager.move_people_to_active_subgroups(
        activities, time_before_policy, 0.0
    )
    specs = []
    for person in sim.world.people.members:
        if person.leisure is not None:
            specs.append(person.leisure.group.spec)
    assert "pump_latrine" in specs
    assert "distribution_center" in specs
    sim.clear_world()

    # During policy
    sim.activity_manager.policies.leisure_policies.apply(date=time_during_policy, leisure=leisure)
    sim.activity_manager.leisure.generate_leisure_probabilities_for_timestep(
        delta_time=10000,
        working_hours=False,
        date=datetime.strptime("2019-03-02-10", "%Y-%m-%d-%H"),
    )
    sim.activity_manager.move_people_to_active_subgroups(
            activities, time_during_policy, 0.0
    )
    specs = []
    for person in sim.world.people.members:
        if person.leisure is not None:
            specs.append(person.leisure.group.spec)
    assert "pump_latrine" not in specs
    assert "distribution_center" not in specs
    sim.clear_world()

    # After policy
    sim.activity_manager.policies.leisure_policies.apply(date=time_after_policy, leisure=leisure)
    sim.activity_manager.leisure.generate_leisure_probabilities_for_timestep(
        delta_time=10000,
        working_hours=False,
        date=datetime.strptime("2019-03-02-10", "%Y-%m-%d-%H"),
    )
    sim.activity_manager.move_people_to_active_subgroups(
        activities, time_after_policy, 0.0
    )
    specs = []
    for person in sim.world.people.members:
        if person.leisure is not None:
            specs.append(person.leisure.group.spec)
    assert "pump_latrine" in specs
    assert "distribution_center" in specs
    sim.clear_world()
