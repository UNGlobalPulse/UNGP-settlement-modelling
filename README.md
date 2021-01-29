# Operational response simulation tool for epidemics within refugee and IDP settlements

This repo contains the relevant code for our individual-based simualtion for epidemics within refugee and internally displaced person (IDP) settlements. See our [paper](https://www.medrxiv.org/content/10.1101/2021.01.27.21250611v1) for more details on the model. Our model is based on the [JUNE](https://github.com/IDAS-Durham/JUNE) epidemic modeling framework originally applied to simulating the spread of COVID-19 in the UK. 

The model presented here is designed to be generalizable to any settlement, however, we focus on Kutupalong-Batukhali Expansion Site, part of the refugee settlement in Cox's Bazar, Banghladesh.

If you wish to adapt this to your own setting, we encourage you to do so. If you need any assistance please do get in touch with us (see Contact section below)

When using this work please cite:
```
@article {Bullock2021.01.27.21250611,
	author = {Bullock, Joseph and Cuesta-Lazaro, Carolina and Quera-Bofarull, Arnau and Katta, Anjali and Hoffmann Pham, Katherine and Hoover, Benjamin and Strobelt, Hendrik and Moreno Jimenez, Rebeca and Sedgewick, Aidan and Samir Evers, Egmond and Kennedy, David and Harlass, Sandra and Gidraf Kahindo Maina, Allen and Hussien, Ahmad and Luengo-Oroz, Miguel},
	title = {Operational response simulation tool for epidemics within refugee and IDP settlements},
	elocation-id = {2021.01.27.21250611},
	year = {2021},
	doi = {10.1101/2021.01.27.21250611},
	publisher = {Cold Spring Harbor Laboratory Press},
	URL = {https://www.medrxiv.org/content/early/2021/01/29/2021.01.27.21250611},
	eprint = {https://www.medrxiv.org/content/early/2021/01/29/2021.01.27.21250611.full.pdf},
	journal = {medRxiv}
}

```

# Setup

Clone the repo:

```
git clone https://github.com/UNGlobalPulse/UNGP-settlement-modelling 
```

and install the necessary packages:

```
cd UNGP-settlement-modelling
pip install -e .
```

# Data

Your code will now be ready to go, however, in order to run the simulation you will need the relevant data. Two folders are required to be created in order to run this simulation.

The first is the data for the base JUNE model. In the home directory run:

```
get_june_data.sh
```

This will create a data folder in `<HOME>/data/`

You need a second folder with the data for your particular adaptation (in our case, the Cox's Bazar refugee settlement). This should be in `<HOME>/camp_data/`

The data we use to run the simualtion is all derived from open-source datasets, details of which can be found in our [paper](https://www.medrxiv.org/content/10.1101/2021.01.27.21250611v1). Given the sensitivity of this project we are not open-sourcing this data, however, please get in contact with us if you would like to know more about data access (see Contact section below). 


# Quickstart

In order to introduce the user to our codebase we have created a walkthrough Notebook:

```
Notebooks/quickstart camp.ipynb
```

# Contributing

Contributions to this project are welcome. Please fork the repository and submit Pull Requests with detailed descriptions of your changes. Please consider whether this change is more appropriate to this repository or the [JUNE](https://github.com/IDAS-Durham/JUNE) repository.

# Tests

Run the tests with:

```
cd test_camps
pytest
```

# License

Epidemiological modeling is a sensitive topic and it is important that models being used to influence public health decision making are able to be reviewed and proped by the community. In the interest of scientific openness and advancement we made this code available under the GPL v3 License.

This code relies on the [JUNE](https://github.com/IDAS-Durham/JUNE) epidemic modelling framework which is licensed under GPL v3.

# Contact

For questions regarding this project please contact: joseph[at]unglobalpulse.org



