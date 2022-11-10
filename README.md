# Operational response simulation tool for epidemics within refugee and IDP settlements

This repo contains the relevant code for our individual-based simualtion for epidemics within refugee and internally displaced person (IDP) settlements. See our [paper](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009360) for more details on the model set-up. Our model is based on the [JUNE](https://github.com/IDAS-Durham/JUNE) epidemic modelling framework originally applied to simulating the spread of COVID-19 in the UK. 

The model presented here is designed to be generalizable to any settlement, however, we initially focus on Kutupalong-Batukhali Expansion Site, part of the refugee settlement in Cox's Bazar, Banghladesh.

If you wish to adapt this to your own setting, we encourage you to do so. If you need any assistance please do get in touch with us (see Contact section below).

When using this work please cite:
```
@article {AylettBullock2021Operational,
	author = {Aylett-Bullock, Joseph and Cuesta-Lazaro, Carolina and Quera-Bofarull, Arnau and Katta, Anjali and Hoffmann Pham, Katherine and Hoover, Benjamin and Strobelt, Hendrik and Moreno Jimenez, Rebeca and Sedgewick, Aidan and Samir Evers, Egmond and Kennedy, David and Harlass, Sandra and Gidraf Kahindo Maina, Allen and Hussien, Ahmad and Luengo-Oroz, Miguel},
	title = {Operational response simulation tool for epidemics within refugee and IDP settlements: A scenario-based case study of the Cox’s Bazar settlement},
	year = {2021},
	doi = {10.1371/journal.pcbi.1009360},
	URL = {https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009360},
	journal = {PLoS Comput Biol},
    number = {17},
    volume = {10}
}
```

# Setup

Clone the repo:

```
git clone https://github.com/UNGlobalPulse/UNGP-settlement-modelling-private 
```

and install the necessary packages:

```
pip install -e .
```

**Note:** This repo uses june v1.1.2 If you want to use the latest version of JUNE-Private, install this with:

```
pip install git+https://github.com/IDAS-Durham/JUNE-private.git 
```
or with ssh

```
pip install git+ssh://git@github.com/IDAS-Durham/JUNE-private.git
```

and then install this package locally without the `requirements.txt` line installing a release version of JUNE.

# Data

Your code will now be ready to go, however, in order to run the simulation you will need the relevant data. Two folders are required to be created in order to run this simulation.

The first is the data for the base JUNE model. In the home directory run:

```
get_june_data.sh
```

This will create a data folder in `<HOME>/data/`

You need a second folder with the data for your particular adaptation (in our case, the Cox's Bazar refugee settlement). This should be in `<HOME>/camp_data/`

The data we use to run the simualtion is all derived from open-source datasets, details of which can be found in our [paper](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009360). Given the sensitivity of this project we are not open-sourcing this data, however, please get in contact with us if you would like to know more about data access (see Contact section below). 


# Quickstart

In order to introduce the user to our codebase we have created a walkthrough Notebook:

```
Notebooks/quickstart camp.ipynb
```

# Documentation

The documentation for this project is in the `docs/` folder. Currently, the user needs to build this locally to render the `html` files. Do to this make sure the relevant `sphinx` packages are installed:

```
pip install sphinx
pip install sphinx_rtd_theme
```

Then you can generate the `build/` file:

```
cd docs/
make clean
make html
```

The docs can then be viewed in a web browser:

```
open build/html/index.html
```

# Contributing

Contributions to this project are welcome. Please fork the repository and submit Pull Requests with detailed descriptions of your changes. Please consider whether this change is more appropriate to this repository or the [JUNE](https://github.com/IDAS-Durham/JUNE) repository.

# Tests

Run the tests with:

```
cd test_camps
pytest
```

**Note:** You currently need the data to be downloaded locally to run these.

# License

Epidemiological modeling is a sensitive topic and it is important that models being used to influence public health decision making are able to be reviewed and proped by the community. In the interest of scientific openness and advancement we made this code available under the GPL v3 License.

This code relies on the [JUNE](https://github.com/IDAS-Durham/JUNE) epidemic modelling framework which is licensed under GPL v3.

# Contact

For questions regarding this project please contact: joseph[at]unglobalpulse.org

# TODO

- Synthesise testing data such that pytest can be run on GitHub Actions for better CI workflow
- Update `camp_scripts/full_run_parse.py` for new version update


