from june.geography import Areas, SuperAreas, Regions
from june.demography import Population
from june.groups import Household, Households, Hospital, Hospitals, Cemeteries

from camps.groups import PumpLatrines, PumpLatrineDistributor
from camps.groups import DistributionCenters, DistributionCenterDistributor
from camps.groups import Communals, CommunalDistributor
from camps.groups import FemaleCommunals, FemaleCommunalDistributor
from camps.groups import Religiouss, ReligiousDistributor
from camps.groups import Shelter, Shelters, ShelterDistributor
from camps.groups import IsolationUnit, IsolationUnits
from camps.groups import LearningCenter, LearningCenters
from camps.distributors import LearningCenterDistributor
from camps.groups import PlayGroups, PlayGroupDistributor
from camps.groups import EVouchers, EVoucherDistributor
from camps.groups import NFDistributionCenters, NFDistributionCenterDistributor
from camps.groups import SheltersVisitsDistributor
from camps.groups import InformalWorks, InformalWorkDistributor


def test__world_has_everything(camps_world):

    world = camps_world
    assert isinstance(world.areas, Areas)
    assert isinstance(world.super_areas, SuperAreas)
    assert isinstance(world.regions, Regions)
    assert isinstance(world.people, Population)
    assert isinstance(world.households, Households)
    assert isinstance(world.learning_centers, LearningCenters)
    assert isinstance(world.cemeteries, Cemeteries)
    assert isinstance(world.isolation_units, IsolationUnits)
    assert isinstance(world.households, Households)
    assert isinstance(world.hospitals, Hospitals)
    assert isinstance(world.shelters, Shelters)
    assert isinstance(world.pump_latrines, PumpLatrines)
    assert isinstance(world.play_groups, PlayGroups)
    assert isinstance(world.distribution_centers, DistributionCenters)
    assert isinstance(world.communals, Communals)
    assert isinstance(world.female_communals, FemaleCommunals)
    assert isinstance(world.religiouss, Religiouss)
    assert isinstance(world.e_vouchers, EVouchers)
    assert isinstance(world.n_f_distribution_centers, NFDistributionCenters)
    assert isinstance(world.informal_works, InformalWorks)

def test__people_in_world_right_subgroups(camps_world):
    dummy_people = camps_world.people.members[:40]

    for dummy_person in dummy_people:
        for subgroup in dummy_person.subgroups.iter():
            if subgroup is not None:
                assert dummy_person in subgroup.people
