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
import pytest

from june.demography import Person
from june.epidemiology.infection import InfectionSelector
from june.epidemiology.infection.symptoms import SymptomTag
from june.policy.medical_care_policies import Hospitalisation
from june import paths
from june.groups.hospital import MedicalFacility, MedicalFacilities
from june.policy import Policies

from camps.groups import IsolationUnit, IsolationUnits
from camps.policy import Isolation


@pytest.fixture(name="selector")
def make_selector():
    selector_file = (
        paths.configs_path
        / "defaults/epidemiology/infection/transmission/TransmissionConstant.yaml"
    )
    return InfectionSelector.from_file(transmission_config_path=selector_file)


@pytest.fixture(name="isolation")
def make_iso_pol():
    return Isolation(testing_mean_time=3, testing_std_time=1, n_quarantine_days=7)


def infect_person(person, selector, symptom_tag="mild"):
    selector.infect_person_at_time(person, 0.0)
    person.infection.symptoms.tag = getattr(SymptomTag, symptom_tag)
    person.infection.symptoms.time_of_symptoms_onset = 5.3


def test__isolation_unit_group():
    iso_unit = IsolationUnit(area=None)
    iso_units = IsolationUnits([iso_unit])
    assert iso_units.get_closest() == iso_unit
    assert isinstance(iso_unit, MedicalFacility)
    assert isinstance(iso_units, MedicalFacilities)


def test__isolation_policy(isolation):
    assert isolation.testing_mean_time == 3
    assert isolation.testing_std_time == 1
    assert isolation.n_quarantine_days == 7
    testing_times = []
    for _ in range(1000):
        testing_times.append(isolation._generate_time_from_symptoms_to_testing())
    assert np.isclose(np.mean(testing_times), 3, atol=0.1)
    assert np.isclose(np.std(testing_times), 1, atol=0.1)


def test__time_of_testing(selector, isolation):
    person = Person.from_attributes(sex="m", age=27)
    infect_person(person, selector, symptom_tag="mild")
    testing_times = []
    for _ in range(1000):
        testing_times.append(isolation._generate_time_of_testing(person))
    assert np.isclose(np.mean(testing_times), 3 + 5.3, atol=0.1)
    assert np.isclose(np.std(testing_times), 1, atol=0.1)


def test__send_to_isolation(selector, isolation):
    person = Person.from_attributes(sex="m", age=27)
    infect_person(person, selector, symptom_tag="mild")
    person.infection.time_of_testing = isolation._generate_time_of_testing(person)
    isolation_units = IsolationUnits([IsolationUnit(area=None)])
    for day in range(0, 100):
        isolation.apply(
            person, medical_facilities=[isolation_units], days_from_start=day
        )
        if 0 < day < person.infection.time_of_testing:
            assert person not in isolation_units[0].people
        elif (
            person.infection.time_of_testing
            < day
            < person.infection.time_of_testing + isolation.n_quarantine_days
        ):

            assert person in isolation_units[0].people
        else:
            assert person not in isolation_units[0].people
        isolation_units[0].clear()


def test__isolation_compliance(selector):
    isolation = Isolation(
        testing_mean_time=3, testing_std_time=1, n_quarantine_days=7, compliance=0.5
    )
    go_isolation = set()
    for _ in range(1000):
        person = Person.from_attributes()
        infect_person(person, selector, symptom_tag="mild")
        isolation_units = IsolationUnits([IsolationUnit(area=None)])
        for day in range(0, 100):
            isolation.apply(
                person, medical_facilities=[isolation_units], days_from_start=day
            )
            if 0 < day < person.infection.time_of_testing:
                assert person not in isolation_units[0].people
            elif (
                person.infection.time_of_testing
                < day
                < person.infection.time_of_testing + isolation.n_quarantine_days
            ):
                if person in isolation_units[0].people:
                    go_isolation.add(person.id)
            else:
                assert person not in isolation_units[0].people
            isolation_units[0].clear()
    assert np.isclose(len(go_isolation), 500, rtol=0.1)


def test__hospitalisation_takes_preference(selector):
    isolation = Isolation(
        testing_mean_time=3, testing_std_time=1, n_quarantine_days=7, compliance=0.5
    )
    hospitalisation = Hospitalisation()
    policies = Policies([isolation, hospitalisation])
