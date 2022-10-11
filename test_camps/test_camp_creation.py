import numpy as np
from camps.camp_creation import GenerateDiscretePDF

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

# TODO: Add more tests to populate_world and household_distribution based on synthetic data