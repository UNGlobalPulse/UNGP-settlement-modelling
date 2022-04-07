Introduction
============

The ``camps`` is a python package for disease modelling in refugee and
internally displaces people settlements. The package is based on the
`JUNE <https://github.com/IDAS-Durham/JUNE>`_ package - a framework for
agent-based modelling.

The current version of ``camps`` is set up to model the spread of
COVID-19 in the Cox's Bazar
refugee settlement in Bangladesh by default, however, can simply be
modified to other settings as necessary.

This documentation is designed to give an overview of the code in the
``camps`` package, with only limited documentation of the JUNE
framework - leaving this to the JUNE code itself to be
documented.

We lay out the documentation such that we first address the data
inputs - how to construct the input data necessary to run the
model. Next we cover the config file set ups which specify how the
model is setup, how the disease spreads, and which interventions
(e.g. lockdowns, vaccines etc.) are turned on in the model.

Once we have covered the higher level changes to the model, we cover
the code operations and how they are used before discussing how to run
the model. Finally, we cover the outputs of the model.

Details of the use of this package are presened in our `paper
<https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009360>`_
which serves as a secondary source of documentation to add details to
those included here.

Please cite::


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
