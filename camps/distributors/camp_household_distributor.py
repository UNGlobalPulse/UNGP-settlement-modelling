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
from matplotlib.style import available

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
def oposite_sex(sex):
    if sex == "m":
        return "f"
    elif sex == "f":
        return "m"


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
    """class for throwing household related errors"""


class CampHouseholdDistributor:
    def __init__(
        self,
        kid_max_age=17,
        adult_min_age=17,
        adult_max_age=99,
        young_adult_max_age=49,
        max_household_size=8,
        household_size_distribution=None,
        chance_unaccompanied_childen=None,
        min_age_gap_between_childen=None,
        chance_single_parent_mf=None,
        ignore_orphans: bool = False,
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
        self.young_adult_max_age = young_adult_max_age
        self.max_household_size = max_household_size
        self.ignore_orphans = ignore_orphans

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

        if chance_unaccompanied_childen is None:
            self.chance_unaccompanied_childen = 0.01
        else:
            self.chance_unaccompanied_childen = chance_unaccompanied_childen

        if min_age_gap_between_childen is None:
            self.min_age_gap_between_childen = 1
        else:
            self.min_age_gap_between_childen = min_age_gap_between_childen

        if chance_single_parent_mf is None:
            self.chance_single_parent_mf = {"m": 1, "f": 10}
        else:
            self.chance_single_parent_mf = chance_single_parent_mf

    ######################################################################
    def P_IsAdult(self, age):
        tanh_halfpeak_age = 15  # 17.1
        tanh_width = 0.7  # 1

        minageadult = 18
        maxagechild = 17
        if age < minageadult:
            return 0
        elif age > maxagechild:
            return 1

        else:
            return (np.tanh(tanh_width * (age - tanh_halfpeak_age)) + 1) / 2

    def P_IsChild(self, age):
        return 1 - self.P_IsAdult(age)

    def AorC(self, age):
        r = np.random.rand(1)[0]
        if r < self.P_IsAdult(age):
            return "Adult"
        else:
            return "Child"

    ######################################################################

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
        kids_by_age = defaultdict(list)
        men_by_age = defaultdict(list)
        women_by_age = defaultdict(list)
        for person in area.people:

            AorC_value = self.AorC(person.age)
            if AorC_value == "Child":
                kids_by_age[person.age].append(person)
            elif AorC_value == "Adult":

                if person.sex == "m":
                    men_by_age[person.age].append(person)
                else:
                    women_by_age[person.age].append(person)

            # if person.age <= self.kid_max_age:
            #     kids_by_age[person.age].append(person)
            # else:
            #     if person.sex == "m":
            #         men_by_age[person.age].append(person)
            #     else:
            #         women_by_age[person.age].append(person)
        return kids_by_age, men_by_age, women_by_age

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
        """Clears dictionary object indexed by a given age"""
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

    def get_closest_child_of_age(self, kids_by_age, age):
        if kids_by_age:
            available_ages = np.array(list(kids_by_age.keys()))
            age = get_closest_element_in_array(available_ages, age)
            person = kids_by_age[age].pop()
            self.clear_dictionary(kids_by_age, age)
            return person
        else:
            return None

    def distribute_people_to_households(
        self,
        area: Area,
        n_families: int,
        n_families_wchildren: int,
        n_families_multigen: int,
        n_families_singleparent: int,
        partner_age_gap_generator,
        mother_firstchild_gap_generator,
        nchildren_generator,
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

        def SingleHousePickSex():
            pick = ["m" for i in range(self.chance_single_parent_mf["m"])] + [
                "f" for i in range(self.chance_single_parent_mf["f"])
            ]
            idx = np.random.randint(0, len(pick))
            return pick[idx]

        def intersection(list_A, list_B, permute=True):
            Intersection = np.array(list(set(list_A) & set(list_B)))
            if permute:
                return list(Intersection[np.random.permutation(len(Intersection))])
            else:
                return list(Intersection)

        def not_in(list_A, list_B, permute=True):
            not_in_set = np.array(list(set(list_A) - set(list_B)))
            if permute:
                return list(not_in_set[np.random.permutation(len(not_in_set))])
            else:
                return list(not_in_set)

        household_sizes = self.household_size_generator.rvs(size=n_families)
        households = [
            self._create_household(area, max_size=household_sizes[i])
            for i in range(n_families)
        ]

        if sum(household_sizes >= 2) < n_families_wchildren:
            n_families_wchildren = sum(household_sizes >= 2)

        # Get households with children
        Houses_W_Children = list(
            np.random.choice(
                np.array(households)[household_sizes >= 2],
                size=n_families_wchildren,
                replace=False,
            )
        )

        household_W_Children_sizes = np.array(
            [household.max_size for household in Houses_W_Children]
        )
        for h in Houses_W_Children:
            h.type = "Children"

        # Get households without children
        Houses_WO_Children = list(set(households).difference(Houses_W_Children))
        household_WO_Children_sizes = np.array(
            [household.max_size for household in Houses_WO_Children]
        )
        for h in Houses_WO_Children:
            h.type = "NoChildren"

        # Get households with single parents
        indexes = []
        for i in range(self.max_household_size):
            indexes += list(np.argwhere(household_W_Children_sizes == i).flatten())
            if len(indexes) > n_families_singleparent:
                break

        Houses_Single = list(
            np.random.choice(
                np.array(Houses_W_Children)[indexes],
                size=n_families_singleparent,
            )
        )
        household_Single_sizes = np.array(
            [household.max_size for household in Houses_Single]
        )
        for h in Houses_Single:
            h.type = "Single"

        # Get households with grandparents
        Houses_Multigen = list(
            np.random.choice(np.array(Houses_W_Children), size=n_families_multigen)
        )
        household_Multigen_sizes = np.array(
            [household.max_size for household in Houses_Multigen]
        )
        for h in Houses_Multigen:
            h.type = "Multigen"

        # Find the spares
        Houses_Left = [
            household
            for household in households
            if household
            not in Houses_W_Children
            + Houses_WO_Children
            + Houses_Single
            + Houses_Multigen
        ]
        if len(Houses_Left) != 0:
            print("House unasigned to house classifications")
            print(len(Houses_Left))

        households_with_space = households.copy()

        kids_by_age, men_by_age, women_by_age = self._create_people_dicts(area)

        n_kids = len([person for age in kids_by_age for person in kids_by_age[age]])
        n_men = len([person for age in men_by_age for person in men_by_age[age]])
        n_women = len([person for age in women_by_age for person in women_by_age[age]])
        assert n_men + n_women + n_kids == len(area.people)
        # print(f"Distributing {len(area.people)} people to {area.name}")

        # put adults households with kids start
        Intersection = intersection(Houses_W_Children, households_with_space)
        for household in Intersection:
            # Single House
            if household in Houses_Single:
                sex = SingleHousePickSex()
                age = random_age(
                    age_min=self.adult_min_age, age_max=self.young_adult_max_age
                )
                person = self.get_closest_person_of_age(
                    men_by_age, women_by_age, age, sex
                )
                if person is None:
                    continue
                household.add(person, subgroup_type=household.SubgroupType.adults)
            else:
                adult_M_age = random_age(
                    age_min=self.adult_min_age, age_max=self.young_adult_max_age
                )
                adult_F_age = adult_M_age - partner_age_gap_generator.rvs(size=1)[0]

                adult_F = self.get_closest_person_of_age(
                    men_by_age, women_by_age, adult_F_age, "f"
                )
                if adult_F is None:
                    continue
                household.add(adult_F, subgroup_type=household.SubgroupType.adults)

                adult_M = self.get_closest_person_of_age(
                    men_by_age, women_by_age, adult_M_age, "m"
                )
                if adult_M is None:
                    continue
                household.add(adult_M, subgroup_type=household.SubgroupType.adults)

            # House now full?
            if household.size >= household.max_size:
                households_with_space.remove(household)
        # print("Parents done")

        # Distribute all the children
        Loop_1 = True
        while True:
            squeeze = False
            if not kids_by_age:
                break

            if Loop_1:
                Intersection = intersection(Houses_W_Children, households_with_space)
            else:
                Intersection = intersection(not_in(Houses_W_Children,Houses_Single), households_with_space)

            if len(Intersection) == 0:
                # Need to find space for final children we sqeeze them into Houses_W_Children even if full
                squeeze = True
                Intersection = intersection(Houses_W_Children, Houses_W_Children)

            for household in Intersection:
                NKids = len(household.kids)
                NAdults = len(household.adults)

                if NKids > nchildren_generator.rvs(size=1)[0]:
                    continue

                # if NAdults == 0:
                #    continue

                # Single Adult with no children YET
                if NAdults == 1 and NKids == 0:
                    adult_a_sex = household.adults[0].sex
                    adult_a_age = household.adults[0].age
                    if adult_a_sex == "f":
                        age_kid = (
                            adult_a_age - mother_firstchild_gap_generator.rvs(size=1)[0]
                        )
                    elif adult_a_sex == "m":
                        # Need a dead(?) mother so generate the appropiate age gap
                        couple_age_gap = partner_age_gap_generator.rvs(size=1)[0]
                        mother_age_gap = mother_firstchild_gap_generator.rvs(size=1)[0]
                        age_kid = adult_a_age - (couple_age_gap + mother_age_gap)

                # Couple with no children YET
                if NAdults == 2 and NKids == 0:
                    adult_a_sex = household.adults[0].sex
                    if adult_a_sex == "f":
                        mother = household.adults[0]
                        father = household.adults[1]
                    elif adult_a_sex == "m":
                        mother = household.adults[1]
                        father = household.adults[0]
                    couple_age_gap = father.age - mother.age
                    age_kid = (
                        mother.age - mother_firstchild_gap_generator.rvs(size=1)[0]
                    )

                # If a family not orphans need a minimum age gap for next kid
                if NKids != 0 and NAdults != 0:
                    age_kid = (
                        min([kid_i.age for kid_i in household.kids])
                        - self.min_age_gap_between_childen
                    )

                # Find a child to add
                if NAdults != 0:  # There are adults
                    kid = self.get_closest_child_of_age(kids_by_age, age_kid)
                else:  # Orphans
                    age_kid = random_age(age_min=0, age_max=self.adult_min_age)
                    kid = self.get_closest_child_of_age(kids_by_age, age_kid)

                household.add(kid, subgroup_type=household.SubgroupType.kids)
                if household.size >= household.max_size and not squeeze:
                    households_with_space.remove(household)
                # Check if we finished up the kids
                if not kids_by_age:
                    break

            Loop_1 = False
        # print("Kids done")

        while True:
            if not men_by_age and not women_by_age:
                break
            Intersection = intersection(Houses_Multigen, households_with_space)
            if len(Intersection) == 0:
                break

            for household in Intersection:
                NKids = len(household.kids)
                NAdults = len(household.adults)

                if (
                    NAdults > 0
                ):  # If there is an adult already try to preference adding parents!
                    # Get random adult
                    idx = np.random.randint(0, len(household.adults))
                    rand_adult = household.adults[idx]

                    sex = random_sex()
                    # Generate the appropiate age gaps
                    couple_age_gap = partner_age_gap_generator.rvs(size=1)
                    mother_age_gap = mother_firstchild_gap_generator.rvs(size=1)
                    if sex == "m":
                        age_gap = couple_age_gap + mother_age_gap
                    elif sex == "f":
                        age_gap = mother_age_gap
                    parent = self.get_closest_person_of_age(
                        men_by_age, women_by_age, rand_adult.age + age_gap, sex
                    )
                    if parent is None:
                        raise ValueError
                    else:
                        household.add(
                            parent, subgroup_type=household.SubgroupType.adults
                        )

                else:  # If there is no adult
                    sex = random_sex()
                    age = np.random.randint(self.adult_min_age, self.adult_max_age)
                    person = self.get_closest_person_of_age(
                        men_by_age, women_by_age, age, sex
                    )
                    if person is None:
                        raise ValueError
                    household.add(person, subgroup_type=household.SubgroupType.adults)

                # If we're trying to maintain household sizes still
                if household.size >= household.max_size:
                    households_with_space.remove(household)
                # Check if we finished up adults
                if not men_by_age and not women_by_age:
                    break
        # print("All multigen adults done")

        while True:
            sqeeze = False
            if not men_by_age and not women_by_age:
                break
            Intersection = intersection(households_with_space, Houses_WO_Children)
            if len(Intersection) == 0:
                # Try placing in Multigen houses
                if len(Houses_Multigen) > 0:
                    Intersection = intersection(Houses_Multigen, households_with_space)
                    if len(Intersection) == 0:
                        sqeeze = True
                        Intersection = intersection(Houses_Multigen, Houses_Multigen)

                #Find houses with space
                if len(households_with_space) > 0:
                    Intersection = intersection(households_with_space, households_with_space)
                else:
                    # Sqeeze in the final adults
                    sqeeze = True
                    Intersection = intersection(Houses_WO_Children, Houses_WO_Children)

            for household in Intersection:
                NAdults = len(household.adults)

                if (
                    NAdults > 0
                ):  # If there is an adult already try to preference adding parents!
                    # Get random adult
                    if NAdults >= 2:
                        idx = np.random.randint(0, len(household.adults))
                        rand_adult = household.adults[idx]

                        sex = random_sex()
                        # Generate the appropiate age gaps
                        couple_age_gap = partner_age_gap_generator.rvs(size=1)
                        mother_age_gap = mother_firstchild_gap_generator.rvs(size=1)
                        if sex == "m":
                            age_gap = couple_age_gap + mother_age_gap
                        elif sex == "f":
                            age_gap = mother_age_gap
                        parent = self.get_closest_person_of_age(
                            men_by_age, women_by_age, rand_adult.age + age_gap, sex
                        )
                        if parent is None:
                            raise ValueError
                        else:
                            household.add(
                                parent, subgroup_type=household.SubgroupType.adults
                            )
                    else:
                        idx = np.random.randint(0, len(household.adults))
                        rand_adult = household.adults[idx]

                        sex = random_sex()
                        # Generate the appropiate age gaps
                        auntuncle = self.get_closest_person_of_age(
                            men_by_age, women_by_age, rand_adult.age, sex
                        )
                        if auntuncle is None:
                            raise ValueError
                        else:
                            household.add(
                                auntuncle, subgroup_type=household.SubgroupType.adults
                            )

                else:  # If there is no adult
                    sex = random_sex()
                    age = np.random.randint(self.adult_min_age, self.adult_max_age)
                    person = self.get_closest_person_of_age(
                        men_by_age, women_by_age, age, sex
                    )
                    if person is None:
                        raise ValueError
                    household.add(person, subgroup_type=household.SubgroupType.adults)

                # If we're trying to maintain household sizes still
                if household.size >= household.max_size and not sqeeze:
                    households_with_space.remove(household)
                # Check if we finished up adults
                if not men_by_age and not women_by_age:
                    break
        # print("All adults only houses done")

        # check everyone has a house
        people_in_households = len(
            [person for household in households for person in household.people]
        )
        assert people_in_households == len(area.people)
        # remove empty households
        households = [household for household in households if household.size != 0]
        return households
