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
from datetime import datetime

from june.policy import MedicalCarePolicy
from june.demography import Person
from june.epidemiology.infection.symptoms import SymptomTag

from camps.groups import IsolationUnits


class Isolation(MedicalCarePolicy):
    def __init__(
        self,
        start_time="1900-01-01",
        end_time="2500-01-01",
        testing_mean_time=None,
        testing_std_time=None,
        n_quarantine_days=None,
        compliance=1.0,
    ):
        super().__init__(start_time=start_time, end_time=end_time)
        self.testing_mean_time = testing_mean_time
        self.testing_std_time = testing_std_time
        self.n_quarantine_days = n_quarantine_days
        self.compliance = compliance

    def _generate_time_from_symptoms_to_testing(self):
        return max(
            0, np.random.normal(loc=self.testing_mean_time, scale=self.testing_std_time)
        )

    def _generate_time_of_testing(self, person: Person):
        try:
            if person.infection.time_of_symptoms_onset is not None:
                return (
                    person.infection.time_of_symptoms_onset
                    + self._generate_time_from_symptoms_to_testing()
                )
            else:
                return np.inf
        except AttributeError:
            raise ValueError(
                f"Trying to generate time of testing for a non infected person."
            )

    def apply(
        self, person: Person, medical_facilities: IsolationUnits, days_from_start: float
    ):
        isolation_units = [
            medical_facility
            for medical_facility in medical_facilities
            if isinstance(medical_facility, IsolationUnits)
        ][0]
        if person.infected:
            if person.infection.time_of_testing is None:
                if np.random.rand() > self.compliance:
                    isolation_units.refused_to_go_ids.add(person.id)
                person.infection.time_of_testing = self._generate_time_of_testing(
                    person
                )
        else:
            return False
        if (
            not person.hospitalised
            and not person.intensive_care
            and person.id not in isolation_units.refused_to_go_ids
        ):
            if person.symptoms.tag.value >= SymptomTag.mild.value:  # mild or more
                if (
                    person.infection.time_of_testing
                    <= days_from_start
                    <= person.infection.time_of_testing + self.n_quarantine_days
                ):
                    isolation_unit = isolation_units.get_closest()
                    isolation_unit.add(person)
                    return True
        return False
