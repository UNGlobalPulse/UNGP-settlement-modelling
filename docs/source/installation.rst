Getting Started
===============

.. _installation:

Installation
------------

The package has not been published on PyPi, but the source code can be
cloned and locally installed using ``pip``.

To install the package first clone the repository::

  git clone https://github.com/UNGlobalPulse/UNGP-settlement-modelling


Then install the necessary dependencies::
  
  cd UNGP-settlement-modelling
  pip install -e .

Your code will now be ready to go, however, in order to run the
simulation you will need the relevant data. Two folders are required
to be created in order to run this simulation.

The first is the data for the base JUNE model. In the home directory
run::

  get_june_data.sh

You need a second folder with the data for your particular adaptation
(in our case, the Cox's Bazar refugee settlement). This should be in
``$BASE/camp_data/``

The data we use to run the simualtion for the Cox's Bazar settlements
(the default setup this package is published to simulate) is all derived from open-source
datasets, details of which can be found in our `paper <https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009360>`_. Given the
sensitivity of this project we are not open-sourcing t his data,
however, please get in contact with us if you would like to know more
about data access: ``joseph[at]unglobalpulse.org``.

The model can, however, be run using synthetic data. Examples of how
to generate this can be found in ``test_camps/conftest.py``.

Quickstart
----------

In order to introduce the user to our codebase we have created a
walkthrough Notebook::
  Notebooks/quickstart camp.ipynb

Once the data is in the ``camp_data`` folder, this notebook should run
out of the box. Alternatively, a pre-run version is published on the
`repository's GitHub <https://github.com/UNGlobalPulse/UNGP-settlement-modelling/blob/master/Notebooks/quickstart%20camp.ipynb>`_.

Troubleshooting
---------------

The `JUNE Setup <https://github.com/IDAS-Durham/JUNE#setup>`_ documentation has information on troubleshooting the
installation of this package. This is the only dependency of ``camps``.

