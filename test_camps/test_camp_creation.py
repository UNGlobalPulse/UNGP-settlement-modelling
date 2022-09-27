

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
        
    
