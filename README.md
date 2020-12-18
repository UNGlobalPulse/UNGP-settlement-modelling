![Python package](https://github.com/IDAS-Durham/JUNE/workflows/Python%20package/badge.svg?branch=master)
[![codecov](https://codecov.io/gh/idas-durham/june/branch/master/graph/badge.svg?token=6TKUHtWxJZ)](https://codecov.io/gh/idas-durham/june)

# Policy simulation tool based on multi-agent epidemic modelling within settlements

This repo is a fork of the JUNE simulation tool originally designed for modelling the spread of COVID-19 in the UK. The model is named after [June Almeida](https://en.wikipedia.org/wiki/June_Almeida). June was the female Scottish virologist that first identified the coronavirus group of viruses. 

We focus on Cox's Bazar Kutupalong-Batukhali Expansion Site located in Banghladesh. The relevant sections of the camp under analysis can be found in the `camp_data/inputs/geography` folder (see Data section below).

# Contributing

Issues are being created and will serve as initial sources of jobs to be done.

Please create a new brach and, when done, submit a pull request and assign a reviewer. There are also tests which must pass before merging into master, you can add new ones in the ``test_camps`` folder. 

With new code additions and alterations, please write tests to ensure future consistency.

All contributions to the codebase which are specific to camps should be in the ``camps/`` folder to make it easier to merge with the main repository. For changes that concern general functionality that can be applied to other countries, please consider submitting a Pul Request to the [JUNE repo](https://github.com/IDAS-Durham/JUNE)

# Setup


### 1. 
Clone the repo, (FIX to right URL on release)
```
git clone https://github.com/JosephPB/JUNE 
```
and install Python3 header files. In Ubuntu and variants, this is the ``python3-dev`` package. You will also need an up-to-date gcc or intel compiler installed.


### 2. 

To use the package, the only requirement is to have [JUNE](https://github.com/IDAS-Durham/JUNE) installed. We currently support June 1.0

```
pip install june==1.0
```
and then you can install this repo  by doing
```
pip install -e .
```

if there are any issues, please report them to the issues page of this repo.

### 3. 
Get the data

If you just want to use the code, and do not plan on contributing more data to it, then simply download June's data folder,

```
get_june_data.sh
```

and the camps' data folder

```
bash get_camp_data.sh
```

Otherwise, if you want to contribute with data, follow the instructions on the Data section.

# Tests

Run the tests with

```
pytest test_camps
```


# Quickstart

Refer to ``Notebooks/quickstart camp.ipynb``


