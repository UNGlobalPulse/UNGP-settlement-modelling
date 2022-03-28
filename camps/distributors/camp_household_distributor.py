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

from collections import OrderedDict
from collections import defaultdict
from itertools import chain
from typing import List
import logging

import numpy as np
import pandas as pd
import yaml
from scipy import stats
import numba as nb

from june import paths
from june.demography import Person
from june.geography import Area
from june.groups import Household, Households

logger = logging.getLogger(__name__)


@nb.njit(cache=True)
def random_sex():
    idx = np.random.randint(0, 2)
    if idx == 0:
        return "m"
    else:
        return "f"


@nb.njit(cache=True)
def random_age(age_min, age_max):
    return np.random.randint(age_min, age_max + 1)


@nb.njit((nb.int32, nb.int32), cache=True)
def numba_random_choice(n_total, n):
    """
    chosses n from n_total with replacement
    """
    return np.random.choice(n_total, n, replace=False)


@nb.njit((nb.int32, nb.int32), cache=True)
def numba_random_choice_replace(n_total, n):
    """
    chosses n from n_total with replacement
    """
    return np.random.choice(n_total, n, replace=True)


def get_closest_element_in_array(array, value):
    min_idx = np.argmin(np.abs(value - array))
    return array[min_idx]


"""
This file contains routines to distribute people to households
according to census data.
"""


class HouseholdError(BaseException):
    """ class for throwing household related errors """


class CampHouseholdDistributor:
    
    def __init__(
        self,
        kid_max_age=16,
        adult_min_age=17,
        adult_max_age=99,
        max_household_size=8,
        household_size_distribution=None,
    ):
        """
        Cluters people into households
        
        Parameters
        ----------
        kid_max_age : int
            Maximum age of people categorised as 'children'
        adult_min_age : int
            Minimum age of people categorised as 'adults'
        adult_max_age : int
            Maximum age of adults
        max_household_size : int
            Maximum size of a household/family
        household_size_distribution : dict
            Optional dict specifying percentage distribution of households by integer size.
            If not set then default taken.
        """
        self.kid_max_age = kid_max_age
        self.adult_min_age = adult_min_age
        self.adult_max_age = adult_max_age
        self.max_household_size = max_household_size
        if household_size_distribution is None:
            household_size_distribution = {
                1: 0.07,
                2: 0.11,
                3: 0.15,
                4: 0.18,
                5: 0.16,
                6: 0.13,
                7: 0.08,
                8: 0.07,
                9: 0.03,
                10: 0.02,
            }
        self.household_size_generator = stats.rv_discrete(
            values=[
                list(household_size_distribution.keys()),
                list(household_size_distribution.values()),
            ]
        )

    def _create_people_dicts(self, area: Area):
        """
        Creates dictionaries with the men and women per age key living in the area.

        Parameters
        ----------
        area
            Area class in which to cluster households

        Returns
        -------
        kids
            List of people categorised as children
        men_by_age
            Dictionary of lists of men indexed by age
        women_by_age
            Dictionary of lists of women indexed by age
        """
        kids = []
        men_by_age = defaultdict(list)
        women_by_age = defaultdict(list)
        for person in area.people:
            if person.age <= self.kid_max_age:
                kids.append(person)
            else:
                if person.sex == "m":
                    men_by_age[person.age].append(person)
                else:
                    women_by_age[person.age].append(person)
        return kids, men_by_age, women_by_age

    def _create_household(self, area, max_size):
        """
        Creates household classes for a given area
        
        Parameters
        ----------
        area
            Area Class in which to assign a Household class
        max_size
            Maximum size of the household created

        Returns
        -------
        Household
            Household class returned with attributes passed
        """
        return Household(area=area, type="family", max_size=max_size)

    def clear_dictionary(self, dictionary, age):
        """ Clears dictionary object indexed by a given age"""
        if not dictionary[age]:
            del dictionary[age]

    def get_closest_person_of_age(self, men_by_age, women_by_age, age, sex):
        """
        For a given person, find someone of a given gender closest to their age
        
        Parameters
        ----------
        men_by_age : dict
            Dictionary of lists of men indexed by age
        women_by_age : dict
            Dictionary of lists of women indexed by age
        age : int
            Age of reference person
        sex: str
            Sex of reference person
        
        Returns
        -------
        person
            If a suitable person is found then they are returned, if not then None is returned
        """
        if sex == "m":
            if men_by_age:
                available_ages = np.array(list(men_by_age.keys()))
                age = get_closest_element_in_array(available_ages, age)
                person = men_by_age[age].pop()
                self.clear_dictionary(men_by_age, age)
                return person

            elif women_by_age:
                available_ages = np.array(list(women_by_age.keys()))
                age = get_closest_element_in_array(available_ages, age)
                person = women_by_age[age].pop()
                self.clear_dictionary(women_by_age, age)
                return person
            else:
                return None
        elif sex == "f":
            if women_by_age:
                available_ages = np.array(list(women_by_age.keys()))
                age = get_closest_element_in_array(available_ages, age)
                person = women_by_age[age].pop()
                self.clear_dictionary(women_by_age, age)
                return person
            elif men_by_age:
                available_ages = np.array(list(men_by_age.keys()))
                age = get_closest_element_in_array(available_ages, age)
                person = men_by_age[age].pop()
                self.clear_dictionary(men_by_age, age)
                return person
            else:
                return None

    def distribute_people_to_households(
        self, area: Area, n_families: int,
    ) -> Households:
        """
        Distributes people to household given an area with a given number of families
        
        Parameters
        ----------
        area
            Area class in which people are to be clustered into households
        n_families : int
            Number of families in the area
        
        Returns
        -------
        households
            List of households in the area
        """

        household_sizes = self.household_size_generator.rvs(size=n_families)
        households = [
            self._create_household(area, max_size=household_sizes[i])
            for i in range(n_families)
        ]
        households_with_space = households.copy()
        kids, men_by_age, women_by_age = self._create_people_dicts(area)
        n_men = len([person for age in men_by_age for person in men_by_age[age]])
        n_women = len([person for age in women_by_age for person in women_by_age[age]])
        assert n_men + n_women + len(kids) == len(area.people)
        # put one adult per household
        for household in households_with_space:
            sex = random_sex()
            age = random_age(age_min=self.adult_min_age, age_max=self.adult_max_age)
            person = self.get_closest_person_of_age(men_by_age, women_by_age, age, sex)
            if person is None:
                break
            household.add(person, subgroup_type=household.SubgroupType.adults)
            if household.size == household.max_size:
                households_with_space.remove(household)

        # distribute kids
        counter = 0
        while True:
            if not kids:
                break
            if households_with_space:
                index = counter % len(households_with_space)
                household = households_with_space[index]
            else:
                index = np.random.randint(len(households))
                household = households[index]
            kid = kids.pop()
            household.add(kid, subgroup_type=household.SubgroupType.kids)
            if household.size == household.max_size:
                households_with_space.remove(household)
            counter += 1

        # put other adults trying to mix sex and match age.
        counter = 0
        while True:
            if not men_by_age and not women_by_age:
                break
            if households_with_space:  # empty_households:
                index = counter % len(households_with_space)
                household = households_with_space[index]
            else:
                idx = np.random.randint(0, len(households))
                household = households[idx]
            person = None
            for person in household.people:
                if person.age >= self.adult_min_age:
                    break
            if person is None:
                sex = random_sex()
                age = np.random.randint(self.adult_min_age, self.adult_max_age)
                person = self.get_closest_person_of_age(
                    men_by_age, women_by_age, age, sex
                )
                if person is None:
                    raise ValueError
                household.add(person, subgroup_type=household.SubgroupType.adults)
            else:
                target = self.get_closest_person_of_age(
                    men_by_age, women_by_age, person.age, person.sex
                )
                if target is None:
                    raise ValueError
                else:
                    household.add(target, subgroup_type=household.SubgroupType.adults)
            if household.size == household.max_size:
                households_with_space.remove(household)
            counter += 1

        # check everyone has a house
        people_in_households = len(
            [person for household in households for person in household.people]
        )
        assert people_in_households == len(area.people)
        # remove empty households
        households = [household for household in households if household.size != 0]
        return households
