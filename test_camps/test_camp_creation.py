import numpy as np
from camps.camp_creation import GenerateDiscretePDF
from camps.distributors.camp_household_distributor import CampHouseholdDistributor
from june.groups import Households, household
from june.demography import Person, Population
from june.geography import Area, Areas
import random
from scipy import stats

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
    Mean = int(np.random.uniform(60, 80))
    SD = int(np.random.uniform(5, 14))

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
    np.random.seed(5)
    random.seed(5)

    kid_max_age=17
    adult_min_age=17
    adult_max_age=99
    young_adult_max_age=49

    dummy_area = Area(name="dummy", super_area=None, coordinates=(12.0, 15.0))
    dummy_areas = Areas(areas=[dummy_area])

    P_child = 0.5
    P_adult = 0.45
    P_old = 0.05
    npeople = 10000

    people_categories = random.choices(["Child", "Adult", "Old"], [P_child,P_adult,P_old], k=npeople)
    people = []
    for person_categories in people_categories:
        if np.random.rand(1) < 0.5:
            sex = "m"
        else:
            sex = "f"

        if person_categories == "Child":
            age_i = np.random.randint(0, kid_max_age)
        elif person_categories == "Adult":
            age_i = np.random.randint(kid_max_age+1, young_adult_max_age)
        elif person_categories == "Old":
            age_i = np.random.randint(young_adult_max_age+1, adult_max_age)
        people += [Person.from_attributes(age=age_i, sex=sex)]

    for person in people:
        person.area = dummy_area
    dummy_area.people = people

    kids = [p for p in people if p.age < adult_min_age]
    world_nkids = len(kids)
    adults = [p for p in people if p.age >= adult_min_age]
    world_nadults = len(adults)
    world_npeople = len(people)
    
    ########################################################################
    # TODO: VARY THIS QUANTITIES STOCHASTICALLY
    ########################################################################
    famsize_avg = np.random.uniform(5, 10)
    max_household_size = int(famsize_avg + 10)

    _, household_size_distribution = GenerateDiscretePDF(
            datarange=[1, max_household_size],
            Mean=famsize_avg+4,
            SD=2
        )

    mean_nfamilies = npeople / famsize_avg
        
    chance_unaccompanied_children=np.random.uniform(1e-2, 1e-1)
    min_age_gap_between_children = 1 
    chance_single_parent_mf={"m": np.random.randint(1,10), "f": np.random.randint(1,10)}

    # default parameters for family composition
    mother_firstchild_gap_mean = np.random.uniform(20, 30)
    mother_firstchild_gap_STD = np.random.uniform(3, 10)
    partner_age_gap_mean = np.random.uniform(0, 5)
    partner_age_gap_mean_STD = np.random.uniform(8, 15)
    chance_single_parent = np.random.uniform(0, .3) #0.179
    chance_multigenerational = np.random.uniform(0, (npeople*P_old) / mean_nfamilies) #0.268
    chance_withchildren = np.random.uniform(.7, 1) #0.922

    ########################################################################
     
    household_distributor = CampHouseholdDistributor(
        kid_max_age=kid_max_age,
        adult_min_age=adult_min_age,
        adult_max_age=adult_max_age,
        young_adult_max_age=young_adult_max_age,
        max_household_size=max_household_size,
        household_size_distribution=household_size_distribution,
        chance_unaccompanied_children=chance_unaccompanied_children,
        min_age_gap_between_children=min_age_gap_between_children,
        chance_single_parent_mf=chance_single_parent_mf,
        ignore_orphans=False
    )

    households_total = []
    for area in dummy_areas:
        n_residents = len(area.people)
        n_families = int(n_residents / famsize_avg)

        n_children =  world_nkids / (chance_withchildren*n_families)
        n_children_STD = np.random.uniform(1, 4)

        mother_firstchild_gap_generator, dist = GenerateDiscretePDF(
            datarange=[14, 60],
            Mean=mother_firstchild_gap_mean + 0.5 + (9.0 / 12.0),
            SD=mother_firstchild_gap_STD
        )
        partner_age_gap_generator, dist = GenerateDiscretePDF(
            datarange=[-20, 20],
            Mean=partner_age_gap_mean + 0.5,
            SD=partner_age_gap_mean_STD,
            stretch=True
        )
        nchildren_generator, dist = GenerateDiscretePDF(
            datarange=[0, 10],
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
    households = Households(households_total)

    NHouseholds = len(households.members)
    metrics = {
        "unaccompaniedchildren" : 0,
        "wchildren" : 0,
        "multigen": 0,
        "singleparent": {"u":0, "m": 0, "f": 0},
        "nchildren" : 0,
        "P_AG": 0,
        "MD_AG": 0,
    }

    
    
    for H in households:
        ages_m = [p.age for p in H.people if p.sex == "m"] 
        ages_f = [p.age for p in H.people if p.sex == "f"] 

        ages = ages_f + ages_m

        H_children = [age for age in ages if age < adult_min_age]
        H_children.sort()
        H_adults_m = [age for age in ages_m if age >= adult_min_age and age <= young_adult_max_age]
        H_adults_f = [age for age in ages_f if age >= adult_min_age and age <= young_adult_max_age]
        H_adults = H_adults_f + H_adults_m
        H_adults.sort()

        H_olds_m = [age for age in ages_m if age > young_adult_max_age]
        H_olds_f = [age for age in ages_f if age > young_adult_max_age]
        H_olds = H_olds_f + H_olds_m
        H_olds.sort()

        if len(H_children) > 0:
            metrics["wchildren"] += 1 
            metrics["nchildren"] += len(H_children)
            if len(H_adults) > 0 and len(H_olds) > 0:
                metrics["multigen"] += 1 
            if len(H_adults) == 1:
                metrics["singleparent"]["u"] += 1
                if len(H_adults_m) == 1:
                    metrics["singleparent"]["m"] += 1
                if len(H_adults_f) == 1:
                    metrics["singleparent"]["f"] += 1
                



            if len(H_adults) == 0 and len(H_olds) == 0:
                metrics["unaccompaniedchildren"] += 1
            


    metrics["nchildren"] /= metrics["wchildren"]
    print("nchildren", metrics["nchildren"], n_children)
    assert np.isclose(metrics["nchildren"], n_children, rtol=0.2)
    print("Wchildrnen", metrics["wchildren"], np.round(chance_withchildren * NHouseholds))
    assert np.isclose(metrics["wchildren"], np.round(chance_withchildren * NHouseholds), rtol=.2)
    print("multi", metrics["multigen"], np.round(chance_multigenerational * NHouseholds))
    assert np.isclose(metrics["multigen"], np.round(chance_multigenerational * NHouseholds), rtol=.8)
    print("single", metrics["singleparent"]["u"], np.round(chance_single_parent * NHouseholds))
    assert np.isclose(metrics["singleparent"]["u"], np.round(chance_single_parent * NHouseholds), rtol=.8)
    print("un", metrics["unaccompaniedchildren"], np.round(chance_unaccompanied_children * NHouseholds))
    assert np.isclose(metrics["unaccompaniedchildren"], np.round(chance_unaccompanied_children * NHouseholds), rtol=1)

    print(metrics["singleparent"])
    print(chance_single_parent_mf)
    mf_ratio = metrics["singleparent"]["m"] / metrics["singleparent"]["u"]
    chance_mf_ratio = chance_single_parent_mf["m"] / (chance_single_parent_mf["m"] + chance_single_parent_mf["f"])
    print("mf", mf_ratio, chance_mf_ratio)
    assert np.isclose(mf_ratio, chance_mf_ratio, rtol = 0.4)

    # mother_firstchild_gap_mean
    # partner_age_gap_mean
  
# TODO: Add more tests to populate_world and household_distribution based on synthetic data