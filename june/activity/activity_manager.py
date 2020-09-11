import logging
from datetime import datetime
from itertools import chain
from typing import List, Optional
from collections import defaultdict
import numpy as np
from time import perf_counter
from time import time as wall_clock

from june.demography import Person
from june.exc import SimulatorError
from june.groups import Subgroup
from june.groups.commute.commutecityunit_distributor import CommuteCityUnitDistributor
from june.groups.commute.commuteunit_distributor import CommuteUnitDistributor
from june.groups.leisure import Leisure
from june.groups.travel.travelunit_distributor import TravelUnitDistributor

from june.policy import (
    IndividualPolicies,
    LeisurePolicies,
    MedicalCarePolicies,
    InteractionPolicies,
)
from june.mpi_setup import (
    mpi_comm,
    mpi_size,
    mpi_rank,
    MovablePeople,
    count_people_in_dict,
)

logger = logging.getLogger(__name__)

activity_hierarchy = [
    "box",
    "medical_facility",
    "rail_travel_out",
    "rail_travel_back",
    "commute",
    "primary_activity",
    "leisure",
    "residence",
]


class ActivityManager:
    def __init__(
        self,
        world,
        policies,
        timer,
        all_activities,
        activity_to_super_groups: dict,
        leisure: Optional[Leisure] = None,
        min_age_home_alone: int = 15,
    ):
        self.logger = logger
        self.policies = policies
        self.world = world
        self.timer = timer
        self.leisure = leisure
        self.all_activities = all_activities

        if self.world.box_mode:
            self.activity_to_super_group_dict = {
                "box": ["boxes"],
            }
        else:
            self.activity_to_super_group_dict = {
                "medical_facility": activity_to_super_groups.get(
                    "medical_facility", []
                ),
                "primary_activity": activity_to_super_groups.get(
                    "primary_activity", []
                ),
                "leisure": activity_to_super_groups.get("leisure", []),
                "residence": activity_to_super_groups.get("residence", []),
                "commute": activity_to_super_groups.get("commute", []),
                "rail_travel": activity_to_super_groups.get("rail_travel", []),
            }
        self.min_age_home_alone = min_age_home_alone

        if (
            "rail_travel_out" in self.all_activities
            or "rail_travel_back" in self.all_activities
        ):
            travel_options = activity_to_super_groups["rail_travel"]
            if "travelunits" in travel_options:
                self.travelunit_distributor = TravelUnitDistributor(
                    self.world.travelcities.members, self.world.travelunits.members
                )

        self.furlough_ratio = 0
        self.key_ratio = 0
        self.random_ratio = 0
        for person in self.world.people:
            if person.lockdown_status == "furlough":
                self.furlough_ratio += 1
            elif person.lockdown_status == "key_worker":
                self.key_ratio += 1
            elif person.lockdown_status == "random":
                self.random_ratio += 1
        if self.furlough_ratio != 0 and self.key_ratio != 0 and self.random_ratio != 0:
            self.furlough_ratio /= (
                self.furlough_ratio + self.key_ratio + self.random_ratio
            )
            self.key_ratio /= self.furlough_ratio + self.key_ratio + self.random_ratio
            self.random_ratio /= (
                self.furlough_ratio + self.key_ratio + self.random_ratio
            )
        else:
            self.furlough_ratio = None
            self.key_ratio = None
            self.random_ratio = None

    @property
    def all_super_groups(self):
        return self.activities_to_super_groups(self.all_activities)

    @property
    def active_super_groups(self):
        return self.activities_to_super_groups(self.timer.activities)

    def distribute_rail_out(self):
        if hasattr(self, "travelunit_distributor"):
            self.travelunit_distributor.distribute_people_out()

    def distribute_rail_back(self):
        if hasattr(self, "travelunit_distributor"):
            self.travelunit_distributor.distribute_people_back()

    @staticmethod
    def apply_activity_hierarchy(activities: List[str]) -> List[str]:
        """
        Returns a list of activities with the right order, obeying the permanent activity hierarcy
        and shuflling the random one.

        Parameters
        ----------
        activities:
            list of activities that take place at a given time step
        Returns
        -------
        Ordered list of activities according to hierarchy
        """
        activities.sort(key=lambda x: activity_hierarchy.index(x))
        return activities

    def activities_to_super_groups(self, activities: List[str]) -> List[str]:
        """
        Converts activities into Supergroups, the interaction will run over these Groups.

        Parameters
        ---------
        activities:
            list of activities that take place at a given time step
        Returns
        -------
        List of groups that are active.
        """

        super_groups = [
            self.activity_to_super_group_dict[activity] for activity in activities
        ]
        return list(chain.from_iterable(super_groups))

    def move_to_active_subgroup(
        self, activities: List[str], person: Person, to_send_abroad=None
    ) -> Optional["Subgroup"]:
        """
        Given the hierarchy of activities and a person, decide what subgroup
        should they go to

        Parameters
        ----------
        activities:
            list of activities that take place at a given time step
        person:
            person that is looking for a subgroup to go to
        Returns
        -------
        Subgroup to which person has to go, given the hierarchy of activities
        """
        for activity in activities:
            if activity == "leisure" and person.leisure is None:
                subgroup = self.leisure.get_subgroup_for_person_and_housemates(
                    person=person, to_send_abroad=to_send_abroad
                )
            elif person.mode_of_transport is not None and person.mode_of_transport.is_public and activity == "commute":
                for commutecity in self.world.commutecities:
                    if person in commutecity.commuters:
                        subgroup = commutecity.get_commute_subgroup(person=person)
            else:
                subgroup = self.get_personal_subgroup(person=person, activity=activity)
            if subgroup is not None:
                if subgroup.external:
                    person.busy = True
                    # this person goes to another MPI domain
                    return subgroup
                subgroup.append(person)
                return
        raise SimulatorError(
            "Attention! Some people do not have an activity in this timestep."
        )

    def get_personal_subgroup(self, person: "Person", activity: str) -> "Subgroup":
        """
        Find the subgroup a person belongs to for a particular activity.
        
        Parameters
        ----------
        person:
            person that is looking for a subgroup 
        activity:
            the activity the person wants to find a subgroup for
        Returns
        -------
        Subgroup for activity
        """
        return getattr(person, activity)

    def do_timestep(self):
        activities = self.timer.activities
        if "rail_travel_out" in activities:
            self.distribute_rail_out()
        if "rail_travel_back" in activities:
            self.distribute_rail_back()
        if self.leisure is not None:
            if self.policies is not None:
                self.policies.leisure_policies.apply(
                    date=self.timer.date, leisure=self.leisure,
                )
            self.leisure.generate_leisure_probabilities_for_timestep(
                delta_time=self.timer.duration,
                is_weekend=self.timer.is_weekend,
                working_hours="primary_activity" in activities,
            )
        to_send_abroad = self.move_people_to_active_subgroups(
            activities, self.timer.date, self.timer.now,
        )
        (
            people_from_abroad,
            n_people_from_abroad,
            n_people_going_abroad,
        ) = self.send_and_receive_people_from_abroad(to_send_abroad)
        return people_from_abroad, n_people_from_abroad, n_people_going_abroad

    def move_people_to_active_subgroups(
        self,
        activities: List[str],
        date: datetime = datetime(2020, 2, 2),
        days_from_start=0,
    ):
        """
        Sends every person to one subgroup. If a person has a mild illness,
        they stay at home

        Parameters
        ----------

        """
        active_individual_policies = self.policies.individual_policies.get_active(
            date=date
        )
        activities = self.apply_activity_hierarchy(activities)
        to_send_abroad = MovablePeople()
        for person in self.world.people.members:
            if person.dead or person.busy:
                continue
            allowed_activities = self.policies.individual_policies.apply(
                active_policies=active_individual_policies,
                person=person,
                activities=activities,
                days_from_start=days_from_start,
                furlough_ratio=self.furlough_ratio,
                key_ratio=self.key_ratio,
                random_ratio=self.random_ratio,
            )
            external_subgroup = self.move_to_active_subgroup(
                allowed_activities, person, to_send_abroad
            )
            if external_subgroup is not None:
                to_send_abroad.add_person(person, external_subgroup)

        return to_send_abroad

    def send_and_receive_people_from_abroad_old(self, to_send_abroad):
        # send people abroad
        tick, tickw = perf_counter(), wall_clock()
        people_from_abroad = {}
        n_people_from_abroad = 0
        for rank in range(mpi_size):
            if rank == mpi_rank:
                # my turn to send my data
                for rank_receiving in range(mpi_size):
                    if rank == rank_receiving:
                        continue
                    if rank_receiving in to_send_abroad:
                        n_people_this_rank = count_people_in_dict(
                            to_send_abroad[rank_receiving]
                        )
                        mpi_comm.send(
                            to_send_abroad[rank_receiving],
                            dest=rank_receiving,
                            tag=rank_receiving,
                        )
                        print(
                            f"I am rank {mpi_rank} and I just sent {n_people_this_rank} to {rank_receiving}"
                        )
                        continue
                    mpi_comm.send(None, dest=rank_receiving, tag=rank_receiving)
            else:
                # I have to listen
                data = mpi_comm.recv(source=rank, tag=mpi_rank)
                if data is not None:
                    n_people_this_rank = count_people_in_dict(data)
                    print(
                        f"I am rank {mpi_rank} and I just received {n_people_this_rank} from {rank}"
                    )
                    update_data(people_from_abroad, data)
                    n_people_from_abroad += n_people_this_rank
        tock,tockw = perf_counter(), wall_clock()
        logger.info(f'CMS: People COMS for rank {mpi_rank}/{mpi_size} - {tock - tick},{tockw-tickw} - {self.timer.date}')
        return people_from_abroad, n_people_from_abroad

    def send_and_receive_people_from_abroad(self, movable_people):
        """
        Deal with the MPI comms.
        """
        n_people_going_abroad = 0
        n_people_from_abroad = 0
        tick, tickw = perf_counter(), wall_clock()
        reqs = []

        for rank in range(mpi_size):

            if mpi_rank == rank:
                continue
            keys, data, n_this_rank = movable_people.serialise(rank)
            if n_this_rank:
                reqs.append(mpi_comm.isend(keys, dest=rank, tag=100))
                reqs.append(mpi_comm.isend(data, dest=rank, tag=200))
                n_people_going_abroad += n_this_rank
            else:
                reqs.append(mpi_comm.isend(None, dest=rank, tag=100))
                reqs.append(mpi_comm.isend(None, dest=rank, tag=200))

        # now it has all been sent, we can start the receiving.

        for rank in range(mpi_size):

            if rank == mpi_rank:
                continue
            keys = mpi_comm.recv(source=rank, tag=100)
            data = mpi_comm.recv(source=rank, tag=200)

            if keys is not None:
                movable_people.update(rank, keys, data)
                n_people_from_abroad += data.shape[0]

        for r in reqs:
            r.wait()

        tock, tockw = perf_counter(), wall_clock()
        logger.info(
            f'CMS: People COMS for rank {mpi_rank}/{mpi_size} - {tock - tick},{tockw - tickw} - {self.timer.date}')
        return movable_people.skinny_in, n_people_from_abroad, n_people_going_abroad
