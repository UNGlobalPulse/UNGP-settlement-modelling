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

import logging
from typing import List, Tuple, Dict

import numpy as np
import pandas as pd
import random
import yaml
from scipy import stats

from camps import paths
from june.utils import parse_age_probabilities

default_data_path = paths.camp_data_path / "input/learning_centers/enrollment_rates.csv"
default_config_path = (
    paths.camp_configs_path / "defaults/distributors/learning_center_distributor.yaml"
)
default_area_region_path = (
    paths.camp_data_path / "input/geography/area_super_area_region.csv"
)


class LearningCenterDistributor:
    """
    Distributes students in areas to learning centers
    """

    def __init__(
        self,
        learning_centers: "LearningCenters",
        female_enrollment_rates: Dict[str, float],
        male_enrollment_rates: Dict[str, float],
        area_region_df: pd.DataFrame,
        teacher_min_age: int = 21,
        neighbour_centers: int = 20,
    ):
        """
        Parameters
        ----------
        learning_centers:
            instance of LearningCenters, containing all learning centers in the world
        female_enrollment_rates:
            dictionary with enrollment rates as a function of age for females
        male_enrollment_rates:
            dictionary with enrollment rates as a function of age for males
        teacher_min_age:
            minimum age of teachers
        """
        self.learning_centers = learning_centers
        self.female_enrollment_rates = self.parse_dictionaries(female_enrollment_rates)
        self.male_enrollment_rates = self.parse_dictionaries(male_enrollment_rates)
        self.area_region_df = area_region_df
        self.teacher_min_age = teacher_min_age
        self.neighbour_centers = neighbour_centers
        self.n_shifts = self.learning_centers.n_shifts

    @classmethod
    def from_file(
        cls,
        learning_centers: "LearningCenters",
        data_path: str = default_data_path,
        config_path: str = default_config_path,
        area_region_path: str = default_area_region_path,
    ) -> "LearningCenterDistributor":
        """
        Initialize LearningCenterDistributor from path to its config file

        Parameters
        ----------
        learning_centers
            instance of LearningCenters, containing all learning centers in the world
        data_path
            path to config dictionary

        Returns
        -------
        LearningCenterDistributor
            Instance of the LearningCenterDistributor
        """
        enrollment_df = pd.read_csv(data_path, index_col=0)
        enrollment_df = enrollment_df[["Gender", "CampID", "Age", "Enrollment"]]
        female_enrollment_df = enrollment_df[enrollment_df["Gender"] == "Female"]
        female_enrollment_dict = cls.convert_df_to_nested_dict(
            cls, female_enrollment_df
        )
        male_enrollment_df = enrollment_df[enrollment_df["Gender"] == "Male"]
        male_enrollment_dict = cls.convert_df_to_nested_dict(cls, male_enrollment_df)
        area_region_df = pd.read_csv(area_region_path, index_col=0)
        with open(config_path) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return cls(
            learning_centers,
            female_enrollment_rates=female_enrollment_dict,
            male_enrollment_rates=male_enrollment_dict,
            area_region_df=area_region_df,
            **config
        )

    def parse_dictionaries(self, dct):
        for key in dct.keys():
            dct[key] = parse_age_probabilities(dct[key])
        return dct

    def convert_df_to_nested_dict(self, df):
        return {
            k: f.groupby("Age")["Enrollment"].apply(lambda x: x.iloc[0]).to_dict()
            for k, f in df.groupby("CampID")
        }

    def distribute_kids_to_learning_centers(self, areas: "Areas"):
        """
        Given a list of areas, distribute kids in the area to the ```self.neighbour_centers``` closest
        learning centers. Kids will be distributed according to the enrollment rates of their sex and age cohort.
        If a chosen learning center is already over capacity, find another one. If all the closest ones
        are full, pick one at random. Shifts are also assigned uniformly

        Parameters
        ----------
        areas
            areas object where people to be distributed live

        Returns
        -------
        None
        """

        for area in areas.members:
            region = self.area_region_df[self.area_region_df["area"] == area.name][
                "region"
            ].iloc[0]
            closest_centers_idx = self.learning_centers.get_closest(
                coordinates=area.coordinates, k=self.neighbour_centers
            )
            for person in area.people:
                if (
                    person.sex == "m"
                    and self.male_enrollment_rates[region][person.age] != 0
                ):
                    if (
                        random.random()
                        <= self.male_enrollment_rates[region][person.age]
                    ):
                        self.send_kid_to_closest_center_with_availability(
                            person, closest_centers_idx
                        )
                elif (
                    person.sex == "f"
                    and self.female_enrollment_rates[region][person.age] != 0
                ):
                    if (
                        random.random()
                        <= self.female_enrollment_rates[region][person.age]
                    ):
                        self.send_kid_to_closest_center_with_availability(
                            person, closest_centers_idx
                        )
                else:
                    continue

    def send_kid_to_closest_center_with_availability(
        self, person: "Person", closest_centers_idx: List[int]
    ):
        """
        Sends a given person to one of their closest learning centers. If full, send to a
        different one. If all full, pick one at random.

        Parameters
        ----------
        person
            person to be sent to learning center
        closest_centers_idx
            ids of the closest centers

        Returns
        -------
        None
        """
        for i in closest_centers_idx:
            center = self.learning_centers.members[i]
            if len(center.teachers) == 0:
                continue
            if len(center.students) >= center.n_pupils_max:
                continue
            else:
                center.add(
                    person=person,
                    shift=random.randint(0, self.n_shifts - 1),
                    subgroup_type=center.SubgroupType.students,
                )
                return

        center = self.learning_centers[random.choice(closest_centers_idx)]
        center.add(
            person=person,
            shift=random.randint(0, self.n_shifts - 1),
            subgroup_type=center.SubgroupType.students,
        )
        return

    def distribute_teachers_to_learning_centers(self, areas: "Areas"):
        """
        Distribute teachers from closest area to the learning center. There is only
        one teacher per learning center currently

        Parameters
        ----------
        areas
            Instance of the Areas class (group of Area classes)

        Returns
        -------
        None
        """
        area_k_max = 5
        if len(areas) < area_k_max:
            area_k_max = len(areas)

        for learning_center in self.learning_centers.members:
            # Find closest area to learning center
            area = areas.get_closest_areas(
                coordinates=learning_center.coordinates,
                k=area_k_max,
                return_distance=False,
            )
            area_k = 0
            while True:
                # get someone in working age
                old_people = [
                    person
                    for person in area[area_k].people
                    if person.age >= self.teacher_min_age
                    and person.primary_activity is None
                ]
                if len(old_people) > 0:
                    break

                if len(old_people) == 0:
                    area_k += 1
                    if area_k >= area_k_max or area_k == len(area):
                        break

            if len(old_people) == 0:
                continue

            NTeachers = int(np.random.poisson(3) + 1)
            if NTeachers > len(old_people):
                NTeachers = len(old_people)
            teachers = np.random.choice(old_people, NTeachers, replace=False)
            # add the teacher to all shifts in the school
            for teacher in teachers:
                for shift in range(self.n_shifts):
                    learning_center.add(
                        person=teacher,
                        shift=shift,
                        subgroup_type=learning_center.SubgroupType.teachers,
                    )
