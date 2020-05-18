from typing import List, Dict, Optional

import numpy as np
import pandas as pd
import h5py
import time

from june import paths
from june.demography import Person
from june.geography import Geography
from tqdm import tqdm

default_data_path = paths.data_path / "processed/census_data/output_area/EnglandWales"
default_areas_map_path = (
    paths.data_path / "processed/geographical_data/oa_msoa_region.csv"
)

nan_integer = -999


class DemographyError(BaseException):
    pass


class AgeSexGenerator:
    def __init__(
        self,
        age_counts: list,
        sex_bins: list,
        female_fractions: list,
        ethnicity_age_bins: list,
        ethnicity_groups: list,
        ethnicity_structure: list,
        max_age=99,
    ):
        """
        age_counts is an array where the index in the array indicates the age,
        and the value indicates the number of counts in that age.
        sex_bins are the lower edges of each sex bin where we have a fraction of females from
        census data, and female_fractions are those fractions.
        Example:
            age_counts = [1, 2, 3] means 1 person of age 0, 2 people of age 1 and 3 people of age 2.
            sex_bins = [1, 3] defines two bins: (0,1) and (3, infinity)
            female_fractions = [0.3, 0.5] means that between the ages 0 and 1 there are 30% females,
                                          and there are 50% females in the bin 3+ years
        Given this information we initialize two generators for age and sex, that can be accessed
        through gen = AgeSexGenerator().age() and AgeSexGenerator().sex().

        Parameters
        ----------
        age_counts
            A list or array with the counts for each age.
        female_fractions
            A dictionary where keys are age intervals like "int-int" and the
            values are the fraction of females inside each age bin.
        """
        self.n_residents = np.sum(age_counts)
        ages = np.repeat(np.arange(0, len(age_counts)), age_counts)
        female_fraction_bins = np.digitize(ages, bins=list(map(int, sex_bins))) - 1
        sexes = (
            np.random.uniform(0, 1, size=self.n_residents)
            < np.array(female_fractions)[female_fraction_bins]
        ).astype(int)
        sexes = map(lambda x: ["m", "f"][x], sexes)

        ethnicity_age_counts, _ = np.histogram(
            ages, bins=list(map(int, ethnicity_age_bins)) + [100]
        )
        ethnicities = list()
        for age_ind, age_count in enumerate(ethnicity_age_counts):
            ethnicities.extend(
                np.random.choice(
                    np.repeat(ethnicity_groups, ethnicity_structure[age_ind]), age_count
                )
            )

        self.age_iterator = iter(ages)
        self.sex_iterator = iter(sexes)
        self.ethnicity_iterator = iter(ethnicities)
        self.max_age = max_age

    def age(self) -> int:
        try:
            return min(next(self.age_iterator), self.max_age)
        except StopIteration:
            raise DemographyError("No more people living here!")

    def sex(self) -> str:
        try:
            return next(self.sex_iterator)
        except StopIteration:
            raise DemographyError("No more people living here!")

    def ethnicity(self) -> str:
        try:
            return next(self.ethnicity_iterator)
        except StopIteration:
            raise DemographyError("No more people living here!")


class Population:
    def __init__(self, people: Optional[List[Person]] = None):
        """
        A population of people.

        Behaves mostly like a list but also has the name of the area attached.

        Parameters
        ----------
        people
            A list of people generated to match census data for that area
        """
        self.people = people or list()

    def __len__(self):
        return len(self.people)

    def __iter__(self):
        return iter(self.people)

    def __getitem__(self, index):
        return self.people[index]

    def extend(self, people):
        self.people.extend(people)

    @property
    def members(self):
        return self.people

    @property
    def total_people(self):
        return len(self.members)

    @property
    def infected(self):
        return [person for person in self.people if person.health_information.infected]

    @property
    def susceptible(self):
        return [
            person for person in self.people if person.health_information.susceptible
        ]

    @property
    def recovered(self):
        return [person for person in self.people if person.health_information.recovered]

    def to_hdf5(self, file_path: str):
        n_people = len(self.people)
        dt = h5py.vlen_dtype(np.dtype("int32"))
        ids = []
        ages = []
        sexes = []
        ethns = []
        areas = []
        group_ids = []
        group_specs = []
        subgroup_types = []
        housemates = []
        for person in self.people:
            ids.append(person.id)
            ages.append(person.age)
            sexes.append(person.sex.encode("ascii", "ignore"))
            ethns.append(person.ethnicity.encode("ascii", "ignore"))
            if person.area is not None:
                areas.append(person.area.id)
            else:
                areas.append(nan_integer)
            gids = []
            stypes = []
            specs = []
            for subgroup in person.subgroups:
                if subgroup is None:
                    gids.append(nan_integer)
                    stypes.append(nan_integer)
                    specs.append(" ".encode("ascii", "ignore"))
                else:
                    gids.append(subgroup.group.id)
                    stypes.append(subgroup.subgroup_type)
                    specs.append(subgroup.group.spec.encode("ascii", "ignore"))
            group_specs.append(np.array(specs, dtype="S10"))
            group_ids.append(np.array(gids, dtype=np.int))
            subgroup_types.append(np.array(stypes, dtype=np.int))
            hmates = [mate.id for mate in person.housemates]
            if len(hmates) == 0:
                housemates.append(np.array([nan_integer], dtype=np.int))
            else:
                housemates.append(np.array(hmates, dtype=np.int))

        ids = np.array(ids, dtype=np.int)
        ages = np.array(ages, dtype=np.int)
        sexes = np.array(sexes, dtype="S10")
        ethns = np.array(ethns, dtype="S10")
        areas = np.array(areas, dtype=np.int)
        group_ids = np.array(group_ids, dtype=np.int)
        subgroup_types = np.array(subgroup_types, dtype=np.int)
        group_specs = np.array(group_specs, dtype="S10")

        with h5py.File(file_path, "a", libver="latest") as f:
            people_dset = f.create_group("population")
            people_dset.attrs["n_people"] = n_people
            people_dset.create_dataset("id", data=ids)
            people_dset.create_dataset("age", data=ages)
            people_dset.create_dataset("sex", data=sexes)
            people_dset.create_dataset("ethnicity", data=ethns)
            people_dset.create_dataset("group_ids", data=group_ids)
            people_dset.create_dataset("group_specs", data=group_specs)
            people_dset.create_dataset("subgroup_types", data=subgroup_types)
            people_dset.create_dataset("area", data=areas)
            people_dset.create_dataset("housemates", data=housemates, dtype=dt)

    @classmethod
    def from_hdf5(cls, file_path: str):
        with h5py.File(file_path, "r") as f:
            people = list()
            population = f["population"]
            # read in chunks of 100,000 people
            chunk_size = 50000
            n_people = population.attrs["n_people"]
            n_chunks = int(np.ceil(n_people / chunk_size))
            for chunk in range(n_chunks):
                idx1 = chunk * chunk_size
                idx2 = min((chunk + 1) * chunk_size, n_people)
                ids = population["id"][idx1:idx2]
                ages = population["age"][idx1:idx2]
                sexes = population["sex"][idx1:idx2]
                ethns = population["ethnicity"][idx1:idx2]
                group_ids = population["group_ids"][idx1:idx2]
                group_specs = population["group_specs"][idx1:idx2]
                subgroup_types = population["subgroup_types"][idx1:idx2]
                areas = population["area"][idx1:idx2]
                housemates = population["housemates"][idx1:idx2]
                for k in range(idx2 - idx1):
                    person = Person()
                    person.id = ids[k]
                    person.age = ages[k]
                    person.sex = sexes[k].decode()
                    person.ethnicity = ethns[k].decode()
                    subgroups = []
                    for group_id, subgroup_type, group_spec in zip(
                        group_ids[k], subgroup_types[k], group_specs[k]
                    ):
                        if group_id == nan_integer:
                            group_id = None
                            subgroup_type = None
                            group_spec = None
                        else:
                            group_spec = group_spec.decode()
                        subgroups.append([group_spec, group_id, subgroup_type])
                    person.subgroups = subgroups
                    person.area = areas[k]
                    person.housemates = housemates[k]
                    if person.housemates[0] == nan_integer:
                        person.housemates = []
                    people.append(person)
        return cls(people)


class Demography:
    def __init__(self, area_names, age_sex_generators: Dict[str, AgeSexGenerator]):
        """
        Tool to generate population for a certain geographical regin.

        Parameters
        ----------
        age_sex_generators
            A dictionary mapping area identifiers to functions that generate
            age and sex for individuals.
        """
        self.area_names = area_names
        self.age_sex_generators = age_sex_generators

    def populate(self, area_name: str,) -> Population:
        """
        Generate a population for a given area. Age, sex and number of residents
        are all based on census data for that area.

        Parameters
        ----------
        area_name
            The name of an area a population should be generated for

        Returns
        -------
        A population of people
        """
        people = list()
        age_and_sex_generator = self.age_sex_generators[area_name]
        for _ in range(age_and_sex_generator.n_residents):
            person = Person(
                age=age_and_sex_generator.age(),
                sex=age_and_sex_generator.sex(),
                ethnicity=age_and_sex_generator.ethnicity(),
                # TODO socioeconomic_generators.socioeconomic_index()
            )
            people.append(person)  # add person to population
        return Population(people=people)

    @classmethod
    def for_geography(
        cls,
        geography: Geography,
        data_path: str = default_data_path,
        config: Optional[dict] = None,
    ) -> "Demography":
        """
        Initializes demography from an existing geography.

        Parameters
        ----------
        geography
            an instance of the geography class
        """
        if len(geography.areas) == 0:
            raise DemographyError("Empty geography!")
        area_names = [area.name for area in geography.areas]
        return cls.for_areas(area_names, data_path, config)

    @classmethod
    def for_zone(
        cls,
        filter_key: Dict[str, list],
        data_path: str = default_data_path,
        areas_maps_path: str = default_areas_map_path,
        config: Optional[dict] = None,
    ) -> "Demography":
        """
        Initializes a geography for a specific list of zones. The zones are
        specified by the filter_dict dictionary where the key denotes the
        kind of zone, and the value is a list with the different zone names. 
        
        Example
        -------
            filter_key = {"region" : "North East"}
            filter_key = {"msoa" : ["EXXXX", "EYYYY"]}
        """
        if len(filter_key.keys()) > 1:
            raise NotImplementedError("Only one type of area filtering is supported.")
        geo_hierarchy = pd.read_csv(areas_maps_path)
        zone_type, zone_list = filter_key.popitem()
        area_names = geo_hierarchy[geo_hierarchy[zone_type].isin(zone_list)]["oa"]
        if len(area_names) == 0:
            raise DemographyError("Region returned empty area list.")
        return cls.for_areas(area_names, data_path, config)

    @classmethod
    def for_areas(
        cls,
        area_names: List[str],
        data_path: str = default_data_path,
        config: Optional[dict] = None,
    ) -> "Demography":
        """
        Load data from files and construct classes capable of generating demographic
        data for individuals in the population.

        Parameters
        ----------
        area_names
            List of areas for which to create a demographic generator.
        data_path
            The path to the data directory
        config
            Optional configuration. At the moment this just gives an asymptomatic
            ratio.

        Returns
        -------
            A demography representing the super area
        """
        area_names = area_names
        age_structure_path = data_path / "age_structure_single_year.csv"
        female_fraction_path = data_path / "female_ratios_per_age_bin.csv"
        ethnicity_structure_path = data_path / "ethnicity_broad_structure.csv"
        # TODO socioecon_structure_path = data_path / "socioecon_structure.csv"
        age_sex_generators = _load_age_and_sex_generators(
            age_structure_path,
            female_fraction_path,
            ethnicity_structure_path,
            # TODO socioecon_structure_path
            area_names,
        )
        return Demography(age_sex_generators=age_sex_generators, area_names=area_names)


def _load_age_and_sex_generators(
    age_structure_path: str,
    female_ratios_path: str,
    ethnicity_structure_path: str,
    # TODO socioecon_strucuture_path,
    area_names: List[str],
):
    """
    A dictionary mapping area identifiers to a generator of age and sex.
    """
    age_structure_df = pd.read_csv(age_structure_path, index_col=0)
    age_structure_df = age_structure_df.loc[area_names]
    age_structure_df.sort_index(inplace=True)

    female_ratios_df = pd.read_csv(female_ratios_path, index_col=0)
    female_ratios_df = female_ratios_df.loc[area_names]
    female_ratios_df.sort_index(inplace=True)

    ethnicity_structure_df = pd.read_csv(
        ethnicity_structure_path, index_col=[0, 1]
    )  # pd MultiIndex!!!
    ethnicity_structure_df = ethnicity_structure_df.loc[pd.IndexSlice[area_names]]
    ethnicity_structure_df.sort_index(level=0, inplace=True)
    ## "sort" is required as .loc slicing a multi_index df doesn't work as expected --
    ## it preserves original order, and ignoring "repeat slices".

    # socioecon_structure_df = pd.read_csv(socioecon_structure_path,index_col=[0,1])
    # socioecon_structure_df = socioecon_structure_df[area_names]

    ret = {}
    for (_, age_structure), (index, female_ratios), (_, ethnicity_df) in zip(
        age_structure_df.iterrows(),
        female_ratios_df.iterrows(),
        ethnicity_structure_df.groupby(level=0),
    ):
        ethnicity_structure = [ethnicity_df[col].values for col in ethnicity_df.columns]
        ret[index] = AgeSexGenerator(
            age_structure.values,
            female_ratios.index.values,
            female_ratios.values,
            ethnicity_df.columns,
            ethnicity_df.index.get_level_values(1),
            ethnicity_structure,
        )

    return ret
