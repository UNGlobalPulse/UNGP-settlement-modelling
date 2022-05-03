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
    DistributionCenterDistributor,
    ReligiousDistributor,
    ShelterDistributor,
    InformalWorkDistributor,
    FemaleCommunalDistributor,
    NFDistributionCenterDistributor,
    EVoucherDistributor,
    PlayGroupDistributor,
    DistributionCenterDistributor,
    CommunalDistributor,
    SheltersVisitsDistributor
)


def generate_leisure_for_world(list_of_leisure_groups, world, daytypes):
    """
    Generates an instance of the leisure class for the specified geography and leisure groups.

    Parameters
    ----------
    list_of_leisure_groups
        list of names of the lesire groups desired. Ex: ["pubs", "cinemas"]
    """
    leisure_distributors = {}

    if "pump_latrines" in list_of_leisure_groups:
        if not hasattr(world, "pump_latrines"):
            raise ValueError("Your world does note have pumps and latrines")
        leisure_distributors["pump_latrine"]=PumpLatrineDistributor.from_config(world.pump_latrines, daytypes=daytypes)
    
    if "play_groups" in list_of_leisure_groups:
        if not hasattr(world, "play_groups"):
            raise
        leisure_distributors["play_group"]=PlayGroupDistributor.from_config(world.play_groups,  daytypes=daytypes)

    if "distribution_centers" in list_of_leisure_groups:
        if not hasattr(world, "distribution_centers"):
            raise ValueError("Your world does note have distribution centers")
        leisure_distributors["distribution_center"] = DistributionCenterDistributor.from_config(world.distribution_centers,  daytypes=daytypes)
        
    if "communals" in list_of_leisure_groups:
        if not hasattr(world, "communals"):
            raise ValueError("Your world does note have communal spaces")
        leisure_distributors["communal"]=CommunalDistributor.from_config(world.communals,  daytypes=daytypes)

    if "e_vouchers" in list_of_leisure_groups:
        if not hasattr(world, "e_vouchers"):
            raise ValueError("Your world does note have e_vouchers spaces")
        leisure_distributors["e_voucher"]=EVoucherDistributor.from_config(world.e_vouchers,  daytypes=daytypes)

    if "n_f_distribution_centers" in list_of_leisure_groups:
        if not hasattr(world, "n_f_distribution_centers"):
            raise ValueError("Your world does note have non food distribution centers")
        leisure_distributors["n_f_distribution_center"]=NFDistributionCenterDistributor.from_config(world.n_f_distribution_centers,  daytypes=daytypes)
        
    if "female_communals" in list_of_leisure_groups:
        if not hasattr(world, "female_communals"):
            raise ValueError(
                "Your world does note have female friendly communal spaces"
            )
        leisure_distributors["female_communal"]=FemaleCommunalDistributor.from_config(world.female_communals,  daytypes=daytypes)

    if "religiouss" in list_of_leisure_groups:
        if not hasattr(world, "religiouss"):
            raise ValueError(
                "Your world does note have female friendly communal spaces"
            )
        leisure_distributors["religious"] = ReligiousDistributor.from_config(world.religiouss,  daytypes=daytypes)

    if "informal_works" in list_of_leisure_groups:
        if not hasattr(world, "informal_works"):
            raise ValueError("Your world does note have informal work")
        leisure_distributors["informal_work"]=InformalWorkDistributor.from_config(world.informal_works,  daytypes=daytypes)
        
    if "shelters_visits" in list_of_leisure_groups:
        if not hasattr(world, "shelters"):
            raise ValueError("Your world does not have shelters.")
        leisure_distributors["shelters_visits"]=SheltersVisitsDistributor.from_config(daytypes=daytypes)
        leisure_distributors["shelters_visits"].link_shelters_to_shelters(world.super_areas)
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
    if "weekday" in config.keys() and "weekend" in config.keys():
        daytypes = {
            "weekday": config["weekday"],
            "weekend": config["weekend"]
        }
    else:
        daytypes = {
            "weekday":["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "weekend": ["Saturday", "Sunday"]
        }
    leisure_instance = generate_leisure_for_world(list_of_leisure_groups, world, daytypes)
    return leisure_instance
