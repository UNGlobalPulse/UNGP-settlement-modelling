

@pytest.fixture(name="policy_simulator")
def make_policy_simulator(camps_world):
    config_name = paths.configs_path / "tests/test_simulator_simple.yaml"
    travel = Travel()
    sim = Simulator.from_file(
        dummy_world,
        interaction,
        epidemiology=epidemiology,
        config_filename=config_name,
        record=None,
        travel=travel,
        policies=None,
        leisure=None,
    )
    return sim
