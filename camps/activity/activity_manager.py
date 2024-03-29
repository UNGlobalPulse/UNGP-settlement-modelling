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

from typing import List, Optional

from june.exc import SimulatorError
from june.activity import ActivityManager
from june.policy import (
    IndividualPolicies,
    LeisurePolicies,
    MedicalCarePolicies,
    InteractionPolicies,
)


class CampActivityManager(ActivityManager):
    """
    Class that overrides the get_personal_subgroup method of ActivityManager, to allow
    for shifts in certain groups
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def activate_next_shift(
        self,
    ):
        for super_group in self.active_super_groups:
            if "visits" in super_group:
                continue
            super_group_instance = getattr(self.world, super_group)
            try:
                if super_group_instance.has_shifts:
                    super_group_instance.activate_next_shift(
                        n_shifts=super_group_instance.n_shifts
                    )
            except AttributeError:
                continue

    def get_personal_subgroup(self, person: "Person", activity: str):
        subgroup = getattr(person, activity)
        try:
            if subgroup.group.has_shifts:
                if (
                    person.id
                    not in subgroup.group.ids_per_shift[subgroup.group.active_shift]
                ):
                    return None
            return subgroup
        except AttributeError:
            return subgroup

    def do_timestep(self, *args, **kwargs):
        ret = super().do_timestep(*args, **kwargs)
        self.activate_next_shift()
        return ret
