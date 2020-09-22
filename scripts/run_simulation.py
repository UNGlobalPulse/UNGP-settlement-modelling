import time
import numpy as np
import numba as nb
import random
import sys

from june.hdf5_savers import generate_world_from_hdf5, load_population_from_hdf5
from june.geography import Geography
from june.interaction import Interaction
from june.infection import Infection, InfectionSelector, HealthIndexGenerator
from june.groups import Hospitals, Schools, Companies, Households, CareHomes, Cemeteries
from june.groups.leisure import Cinemas, Pubs, Groceries, generate_leisure_for_config
from june.groups.travel import Travel
from june.simulator import Simulator
from june.infection_seed import InfectionSeed
from june.policy import Policies
from june.logger import Logger
from june.logger.read_logger import ReadLogger
from june import paths


def set_random_seed(seed=999):
    """
    Sets global seeds for testing in numpy, random, and numbaized numpy.
    """

    @nb.njit(cache=True)
    def set_seed_numba(seed):
        random.seed(seed)
        np.random.seed(seed)

    np.random.seed(seed)
    set_seed_numba(seed)
    random.seed(seed)
    return


if len(sys.argv) > 1:
    seed = int(sys.argv[1])
else:
    seed = 999
set_random_seed(seed)

world_file = "./tests.hdf5"
config_path = "./config_simulation.yaml"
save_path = f'results_nompi_{seed:02d}'

world = generate_world_from_hdf5(world_file, chunk_size=1_000_000)
print("World loaded succesfully")

logger = Logger(save_path=save_path, file_name=f'logger.0.hdf5') 
population = load_population_from_hdf5(world_file)
logger.log_population(population)


# regenerate lesiure
leisure = generate_leisure_for_config(world, config_path)
#
travel = Travel()
# health index and infection selecctor
health_index_generator = HealthIndexGenerator.from_file(asymptomatic_ratio=0.2)
infection_selector = InfectionSelector.from_file(health_index_generator=health_index_generator)

# interaction
interaction = Interaction.from_file()

# policies
policies = Policies.from_file()

# create simulator

simulator = Simulator.from_file(
   world=world,
   policies=policies,
   interaction=interaction,
   leisure=leisure,
   travel = travel,
   infection_selector=infection_selector,
   config_filename=config_path,
   logger=logger,
)
print("simulator ready to go")

# seed some cases
n_cases = 250
selected_ids = np.random.choice(population.people_ids, n_cases, replace=False)
for inf_id in selected_ids:
    person = world.people.get_from_id(inf_id)
    simulator.infection_selector.infect_person_at_time(person, 0.)

t1 = time.time()
simulator.run()
t2 = time.time()

logger = ReadLogger(save_path, n_processes=1)
logger.world_summary().to_csv(save_path + "_summary.csv")

print(f" Simulation took {t2-t1} seconds")

