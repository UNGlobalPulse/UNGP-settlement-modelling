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

from june.groups.leisure import Leisure
import yaml
from june.groups.leisure import (
    SocialVenueDistributor,
    PubDistributor,
    GroceryDistributor,
    CinemaDistributor,
    ResidenceVisitsDistributor,
)
from camps.groups import (
    PumpLatrineDistributor,
    InformalWorkDistributor,
    FemaleCommunalDistributor,
    DistributionCenterDistributor,
    CommunalDistributor,
)


def generate_leisure_for_world(list_of_leisure_groups, world):
    """
    Generates an instance of the leisure class for the specified geography and leisure groups.

    Parameters
    ----------
    list_of_leisure_groups
        list of names of the lesire groups desired. Ex: ["pubs", "cinemas"]
    """
    leisure_distributors = []
    if "pubs" in list_of_leisure_groups:
        if not hasattr(world, "pubs"):
            raise ValueError("Your world does not have pubs.")
        leisure_distributors.append(PubDistributor.from_config(world.pubs))
    if "cinemas" in list_of_leisure_groups:
        if not hasattr(world, "cinemas"):
            raise ValueError("Your world does not have cinemas.")
        leisure_distributors.append(CinemaDistributor.from_config(world.cinemas))
    if "groceries" in list_of_leisure_groups:
        if not hasattr(world, "groceries"):
            raise ValueError("Your world does not have groceries.")
        leisure_distributors.append(GroceryDistributor.from_config(world.groceries))
    if "pump_latrines" in list_of_leisure_groups:
        if not hasattr(world, "pump_latrines"):
            raise ValueError("Your world does note have pumps and latrines")
        leisure_distributors.append(
            PumpLatrineDistributor.from_config(world.pump_latrines)
        )
    if "distribution_centers" in list_of_leisure_groups:
        if not hasattr(world, "distribution_centers"):
            raise ValueError("Your world does note have distribution centers")
        leisure_distributors.append(
            DistributionCenterDistributor.from_config(world.distribution_centers)
        )
    if "communals" in list_of_leisure_groups:
        if not hasattr(world, "communals"):
            raise ValueError("Your world does note have communal spaces")
        leisure_distributors.append(CommunalDistributor.from_config(world.communals))
    if "female_communals" in list_of_leisure_groups:
        if not hasattr(world, "female_communals"):
            raise ValueError(
                "Your world does note have female friendly communal spaces"
            )
        leisure_distributors.append(
            FemaleCommunalDistributor.from_config(world.female_communals)
        )
    if "informal_works" in list_of_leisure_groups:
        if not hasattr(world, "informal_works"):
            raise ValueError("Your world does note have informal work")
        leisure_distributors.append(
            InformalWorkDistributor.from_config(world.informal_works)
        )
    if "household_visits" in list_of_leisure_groups:
        if not hasattr(world, "households"):
            raise ValueError("Your world does not have households.")
        leisure_distributors.append(
            ResidenceVisitsDistributor.from_config(world.super_areas)
        )
    if "residence_visits" in list_of_leisure_groups:
        raise NotImplementedError

    return Leisure(leisure_distributors, regions=world.regions)


def generate_leisure_for_config(world, config_filename):
    """
    Generates an instance of the leisure class for the specified geography and leisure groups.
    Parameters
    ----------
    list_of_leisure_groups
        list of names of the lesire groups desired. Ex: ["pubs", "cinemas"]
    """
    with open(config_filename) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    list_of_leisure_groups = config["activity_to_super_groups"]["leisure"]
    leisure_instance = generate_leisure_for_world(list_of_leisure_groups, world)
    return leisure_instance
