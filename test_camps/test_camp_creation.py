import numpy as np
from camps.camp_creation import GenerateDiscretePDF
from camps.distributors.camp_household_distributor import CampHouseholdDistributor
from june.groups import Households
from june.demography import Person, Population
from june.geography import Area, Areas

def test__populate_world(camps_world):
    world = camps_world

    population = world.people
    assert len(population) > 0

    adults = [person for person in population if person.age >= 17]
    kids = [person for person in population if person.age < 17]

    assert len(adults) > 0
    assert len(kids) > 0

def test__household_distribution(camps_world):
    world = camps_world

    households = world.households

    assert len(households) > 0

    for household in households:
        assert household.contains_people == True
        assert household.n_residents == len(household.people)
        
def test__GenerateDiscretePDF():
    #Type="Gaussian", datarange=[0, 100], Mean=0, SD=1, stretch=False

    #Test distribution for nice integer mean and sd
    datarange = [-10,10]
    Mean = 3
    SD = 1
    _, dist = GenerateDiscretePDF(datarange=datarange, Mean=Mean, SD=SD)
    assert dist[Mean-1] == dist[Mean] #Bins [Mean-1:Mean][Mean:Mean+1] Should be equal as symmetric around Mean (if integer mean)
    
    #Check total probabilities within range of standard deviation are correct.
    SD_Multi = 1
    P_within_1SD = np.array([dist[i] for i in np.arange(-SD*SD_Multi,SD*SD_Multi,1) + Mean]).sum()
    assert np.isclose(P_within_1SD, 0.6827, rtol=0.05)

    #Check total probabilities within range of 2 standard deviations are correct.
    SD_Multi = 2
    P_within_2SD = np.array([dist[i] for i in np.arange(-SD*SD_Multi,SD*SD_Multi,1) + Mean]).sum()
    assert np.isclose(P_within_2SD, 0.9545, rtol=0.05)

    #Check total probabilities within range of 3 standard deviations are correct.
    SD_Multi = 3
    P_within_3SD = np.array([dist[i] for i in np.arange(-SD*SD_Multi,SD*SD_Multi,1) + Mean]).sum()
    assert np.isclose(P_within_3SD, 0.9973, rtol=0.1)

    #Test distribution for arbitrary values 
    Min = 0
    Max = 150
    datarange = [Min,Max]
    Mean = (np.random.rand(1) + np.random.randint(60,80))[0]
    SD = (np.random.rand(1) + np.random.randint(5,14))[0]

    generator, dist = GenerateDiscretePDF(datarange=datarange, Mean=Mean, SD=SD)
    assert np.isclose(sum(dist.values()),  1.0, rtol=1e-3) #Normalized

    Randoms = generator.rvs(size=10000)

    Randoms_Mean = np.mean(Randoms)
    Randoms_SD = np.std(Randoms,ddof=1)
    assert np.isclose(Randoms_Mean, Mean, rtol=0.2) #Have to be quite relaxed here
    assert np.isclose(Randoms_SD, SD, rtol=0.2)
    assert np.min(Randoms) >= Min
    assert np.max(Randoms) <= Max

def test__HouseholdDistributor():
    basecamp_famsize_avg = 5.5
     
    dummy_area = Area(name="dummy", super_area=None, coordinates=(12.0, 15.0))
    dummy_areas = Areas(areas=[dummy_area])
    people = [Person.from_attributes(sex="f", age=age) for age in range(100)]
    for person in people:
        person.area = dummy_area
    dummy_area.people = people

    household_distributor = CampHouseholdDistributor(
        kid_max_age=17,
        adult_min_age=17,
        adult_max_age=99,
        young_adult_max_age=49,
        max_household_size=10,
        household_size_distribution={
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
            },
        chance_unaccompanied_children=0.01,
        min_age_gap_between_children=1,
        chance_single_parent_mf={"m": 1, "f": 10},
        ignore_orphans=False
    )

    households_total = []
    for area in dummy_areas:
        n_residents = len(area.people)
        n_families = n_residents / basecamp_famsize_avg

        # default parameters for family composition
        mother_firstchild_gap_mean = 22
        mother_firstchild_gap_STD = 8
        partner_age_gap_mean = 0
        partner_age_gap_mean_STD = 10
        chance_single_parent = 0.179
        chance_multigenerational = 0.268
        chance_withchildren = 0.922
        n_children = 2.5
        n_children_STD = 2
        stretch = True

        mother_firstchild_gap_generator, dist = GenerateDiscretePDF(
            datarange=[14, 60],
            Mean=mother_firstchild_gap_mean + 0.5 + (9.0 / 12.0),
            SD=mother_firstchild_gap_STD
        )
        partner_age_gap_generator, dist = GenerateDiscretePDF(
            datarange=[-20, 20],
            Mean=partner_age_gap_mean + 0.5,
            SD=partner_age_gap_mean_STD,
            stretch=stretch
        )
        nchildren_generator, dist = GenerateDiscretePDF(
            datarange=[0, 8],
            Mean=n_children,
            SD=n_children_STD,
        )

        area.households = household_distributor.distribute_people_to_households(
            area=area,
            n_families=n_families,
            n_families_wchildren=int(np.round(chance_withchildren * n_families)),
            n_families_multigen=int(np.round(chance_multigenerational * n_families)),
            n_families_singleparent=int(np.round(chance_single_parent * n_families)),
            partner_age_gap_generator=partner_age_gap_generator,
            mother_firstchild_gap_generator=mother_firstchild_gap_generator,
            nchildren_generator=nchildren_generator,
        )
        households_total += area.households
    dummy_areas.households = Households(households_total)

    assert 1 == 1
    

# TODO: Add more tests to populate_world and household_distribution based on synthetic data