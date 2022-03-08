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
    """ class for throwing household related errors """


class CampHouseholdDistributor:
    def __init__(
        self,
        kid_max_age=17,
        adult_min_age=17,
        adult_max_age=99,
        young_adult_max_age=45,
        max_household_size=8,
        household_size_distribution=None,
        chance_unaccompanied_childen=None,
        min_age_gap_between_childen=None,
        chance_single_parent_mf=None,
        ignore_orphans: bool = False,
    ):
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
                10: 0.02
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

    def _create_people_dicts(self, area: Area):
        """
        Creates dictionaries with the men and women per age key living in the area.
        """
        kids_by_age = defaultdict(list)
        men_by_age = defaultdict(list)
        women_by_age = defaultdict(list)
        for person in area.people:
            if person.age <= self.kid_max_age:
                kids_by_age[person.age].append(person)
            else:
                if person.sex == "m":
                    men_by_age[person.age].append(person)
                else:
                    women_by_age[person.age].append(person)
        return kids_by_age, men_by_age, women_by_age

    def _create_household(self, area, max_size):
        return Household(area=area, type="family", max_size=max_size)

    def clear_dictionary(self, dictionary, age):
        if not dictionary[age]:
            del dictionary[age]

    def get_closest_person_of_age(self, men_by_age, women_by_age, age, sex):
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
        self, area: Area, 

        n_families: int,
        n_families_wchildren: int,
        n_families_multigen: int,
        n_families_singleparent: int,

        partner_age_gap_generator,
        mother_firstchild_gap_generator,
    ) -> Households:

        def SingleHousePickSex():
            pick = ["m" for i in range(self.chance_single_parent_mf["m"])] + ["f" for i in range(self.chance_single_parent_mf["f"])] 
            idx = np.random.randint(0, len(pick))
            return pick[idx]

        def intersection(list_A, list_B, permute=True):
            Intersection = np.array(list(set(list_A) & set(list_B)))
            if permute:
                return list(Intersection[np.random.permutation(len(Intersection))])
            else:
                return list(Intersection)

        household_sizes = self.household_size_generator.rvs(size=n_families)
        households = [
            self._create_household(area, max_size=household_sizes[i])
            for i in range(n_families)
        ]

        #Preferance larger houses for households with kids.
        for N in range(0, self.max_household_size):
            if sum(household_sizes>N) < n_families_wchildren:
                householdcut = N-1
                break
    
        #Get households with children   
        Houses_W_Children = list(np.random.choice(np.array(households)[household_sizes>=householdcut], size=n_families_wchildren, replace=False))
        household_W_Children_sizes = np.array([household.max_size for household in Houses_W_Children])

        #Get households without children
        Houses_WO_Children = list(set(households).difference(Houses_W_Children))
        household_WO_Children_sizes = np.array([household.max_size for household in Houses_WO_Children])

        #Preferance smaller houses for households with single parents.
        for N in range(0, self.max_household_size):
            if sum(household_W_Children_sizes>N) < n_families_singleparent:
                householdcut = N-1
                break

        #Get households with single parents
        Houses_Single = list(np.random.choice(np.array(Houses_W_Children)[household_W_Children_sizes<=householdcut], size=n_families_singleparent))
        household_Single_sizes = np.array([household.max_size for household in Houses_Single])

        #Get households with grandparents
        Houses_Multigen = list(np.random.choice(np.array(Houses_W_Children), size=n_families_multigen))
        household_Multigen_sizes = np.array([household.max_size for household in Houses_Multigen])

        # print("Families", n_families, len(households))
        # print("Families with children", n_families_wchildren,len(Houses_W_Children), np.median(household_W_Children_sizes))
        # print("Families without children", n_families - n_families_wchildren, len(Houses_WO_Children), np.median(household_WO_Children_sizes))
        # print("Families with multi", n_families_multigen,len(Houses_Multigen), np.median(household_Multigen_sizes))
        # print("Families with single", n_families_singleparent,len(Houses_Single), np.median(household_Single_sizes))

        # from matplotlib import pyplot as plt
        # plt.figure()
        # plt.hist(household_W_Children_sizes, bins=np.arange(12)-0.5)
        # plt.title("With children")
        # plt.show

        # plt.figure()
        # plt.hist(household_WO_Children_sizes, bins=np.arange(12)-0.5)
        # plt.title("Without children")
        # plt.show

        # plt.figure()
        # plt.hist(household_Multigen_sizes, bins=np.arange(12)-0.5)
        # plt.title("multigen")
        # plt.show

        # plt.figure()
        # plt.hist(household_Single_sizes, bins=np.arange(12)-0.5)
        # plt.title("With children single")
        # plt.show

        #Find the spares
        Houses_Left = [household for household in households
            if household not in Houses_W_Children+Houses_WO_Children+Houses_Single+Houses_Multigen
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
        print(f"Distributing {len(area.people)} people to {area.name}")
        
        # put adults households with kids start
        Intersection = intersection(Houses_W_Children, households_with_space)
        for household in Intersection:
            #Single House
            if household in Houses_Single:
                sex = SingleHousePickSex()
                age = random_age(age_min=self.adult_min_age, age_max=self.young_adult_max_age)
                person = self.get_closest_person_of_age(men_by_age, women_by_age, age, sex)
                if person is None:
                    break
                household.add(person, subgroup_type=household.SubgroupType.adults)
            else:
                adult_M_age = random_age(age_min=self.adult_min_age, age_max=self.young_adult_max_age) 
                adult_F_age = adult_M_age - partner_age_gap_generator.rvs(size=1)

                
                adult_F = self.get_closest_person_of_age(men_by_age, women_by_age, adult_F_age, "f")
                if adult_F is None:
                    break
                household.add(adult_F, subgroup_type=household.SubgroupType.adults)

                adult_M = self.get_closest_person_of_age(men_by_age, women_by_age, adult_M_age, "m")
                if adult_M is None:
                    break
                household.add(adult_M, subgroup_type=household.SubgroupType.adults)

            #House now full?
            if household.size >= household.max_size:
                households_with_space.remove(household)
        print("Parents done")

        #Distribute all the children
        while True:
            squeeze = False
            if not kids_by_age:
                break
            Intersection = intersection(Houses_W_Children, households_with_space)
            if len(Intersection) == 0:
                #Need to find space for final children we sqeeze them into Houses_W_Children even if full
                squeeze = True 
                Intersection = intersection(Houses_W_Children,Houses_W_Children) 

            for household in Intersection:
                NKids = len(household.kids.people)
                NAdults = len(household.adults.people)

                #if NAdults == 0:
                #    continue

                #Single Adult with no children YET
                if NAdults == 1 and NKids == 0:
                    adult_a_sex = household.adults.people[0].sex
                    adult_a_age = household.adults.people[0].age
                    if adult_a_sex == "f":
                        age_kid = adult_a_age - mother_firstchild_gap_generator.rvs(size=1)
                    elif adult_a_sex == "m":
                        #Need a dead(?) mother so generate the appropiate age gap
                        couple_age_gap = partner_age_gap_generator.rvs(size=1) 
                        mother_age_gap = mother_firstchild_gap_generator.rvs(size=1)
                        age_kid = adult_a_age - ( couple_age_gap + mother_age_gap)

                #Couple with no children YET
                if NAdults == 2 and NKids == 0:
                    adult_a_sex = household.adults.people[0].sex
                    if adult_a_sex == "f":
                        mother = household.adults.people[0]
                        father = household.adults.people[1]
                    elif adult_a_sex == "m":
                        mother = household.adults.people[1]
                        father = household.adults.people[0]
                    couple_age_gap = father.age - mother.age
                    age_kid = mother.age - mother_firstchild_gap_generator.rvs(size=1)

                #If a family not orphans need a minimum age gap for next kid
                if NKids != 0 and NAdults != 0:
                    age_kid = min([kid_i.age for kid_i in household.kids.people]) - self.min_age_gap_between_childen

                
                #Find a child to add
                if NAdults != 0: #There are adults
                    kid = self.get_closest_child_of_age(kids_by_age, age_kid)
                else: #Orphans
                    age_kid = random_age(age_min=0, age_max=self.adult_min_age)
                    kid = self.get_closest_child_of_age(kids_by_age, age_kid)

                household.add(kid, subgroup_type=household.SubgroupType.kids)
                if household.size >= household.max_size and not squeeze:
                    households_with_space.remove(household)
                #Check if we finished up the kids
                if not kids_by_age:
                    break
        print("Kids done")

        while True:
            if not men_by_age and not women_by_age:
                break
            Intersection = intersection(Houses_Multigen, households_with_space)
            if len(Intersection) == 0:
                break

            for household in Intersection:
                NKids = len(household.kids.people)
                NAdults = len(household.adults.people)

                if NAdults > 0: #If there is an adult already try to preference adding parents!
                    #Get random adult
                    idx = np.random.randint(0, len(household.adults.people))
                    rand_adult = household.adults.people[idx]

                    sex = random_sex()
                    #Generate the appropiate age gaps
                    couple_age_gap = partner_age_gap_generator.rvs(size=1) 
                    mother_age_gap = mother_firstchild_gap_generator.rvs(size=1)
                    if sex == "m":
                        age_gap = couple_age_gap + mother_age_gap
                    elif sex == "f":
                        age_gap = mother_age_gap
                    parent = self.get_closest_person_of_age(men_by_age, women_by_age, rand_adult.age+age_gap, sex)
                    if parent is None:
                        raise ValueError
                    else:
                        household.add(parent, subgroup_type=household.SubgroupType.adults)

                else: #If there is no adult
                    sex = random_sex()
                    age = np.random.randint(self.adult_min_age, self.adult_max_age)
                    person = self.get_closest_person_of_age(
                        men_by_age, women_by_age, age, sex
                    )
                    if person is None:
                        raise ValueError
                    household.add(person, subgroup_type=household.SubgroupType.adults)

                #If we're trying to maintain household sizes still
                if household.size >= household.max_size:
                    households_with_space.remove(household)
                #Check if we finished up adults
                if not men_by_age and not women_by_age:
                    break
        print("All multigen adults done")

        while True:
            sqeeze = False
            if not men_by_age and not women_by_age:
                break
            Intersection = intersection(households_with_space, households_with_space)
            if len(Intersection) == 0:
                sqeeze = True
                #Sqeeze in the final adults
                Intersection = intersection(households, households)

            for household in Intersection:
                NAdults = len(household.adults.people)

                if NAdults > 0: #If there is an adult already try to preference adding parents!
                    #Get random adult
                    idx = np.random.randint(0, len(household.adults.people))
                    rand_adult = household.adults.people[idx]

                    sex = random_sex()
                    #Generate the appropiate age gaps
                    couple_age_gap = partner_age_gap_generator.rvs(size=1) 
                    mother_age_gap = mother_firstchild_gap_generator.rvs(size=1)
                    if sex == "m":
                        age_gap = couple_age_gap + mother_age_gap
                    elif sex == "f":
                        age_gap = mother_age_gap
                    parent = self.get_closest_person_of_age(men_by_age, women_by_age, rand_adult.age+age_gap, sex)
                    if parent is None:
                        raise ValueError
                    else:
                        household.add(parent, subgroup_type=household.SubgroupType.adults)

                else: #If there is no adult
                    sex = random_sex()
                    age = np.random.randint(self.adult_min_age, self.adult_max_age)
                    person = self.get_closest_person_of_age(
                        men_by_age, women_by_age, age, sex
                    )
                    if person is None:
                        raise ValueError
                    household.add(person, subgroup_type=household.SubgroupType.adults)

                #If we're trying to maintain household sizes still
                if household.size >= household.max_size and not sqeeze:
                    households_with_space.remove(household)
                #Check if we finished up adults
                if not men_by_age and not women_by_age:
                    break
        print("All adults only houses done")

        # check everyone has a house
        people_in_households = len(
            [person for household in households for person in household.people]
        )
        assert people_in_households == len(area.people)
        # remove empty households
        households = [household for household in households if household.size != 0]
        return households
