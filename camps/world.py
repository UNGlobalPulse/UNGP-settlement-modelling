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

from june.world import World


class CampWorld(World):
    """
    This Class creates the world that will later be simulated.
    The world will be stored in pickle, but a better option needs to be found.
    
    Note: BoxMode = Demography +- Sociology - Geography
    """

    def __init__(self):
        """
        Initializes a world given a geography and a demography. For now, households are
        a special group because they require a mix of both groups (we need to fix
        this later). 
        """
        self.areas = None
        self.super_areas = None
        self.regions = None
        self.people = None
        self.households = None
        self.schools = None
        self.hospitals = None
        self.cemeteries = None
        self.box_mode = False
        self.pump_latrines = None
        self.distribution_centers = None
        self.communals = None
        self.female_communals = None
        self.religiouss = None
        self.shelters = None
        self.e_vouchers = None
        self.n_f_distribution_centers = None
