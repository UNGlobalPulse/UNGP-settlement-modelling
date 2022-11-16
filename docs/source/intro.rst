Introduction
============

``camps`` is a python package for disease modelling in refugee and
internally displaces people settlements. The package is based on the
`JUNE <https://github.com/IDAS-Durham/JUNE>`_ package - a framework for
agent-based disease modelling.

The current default version of ``camps`` is set up to model the spread of
COVID-19 in the Cox's Bazar
refugee settlement in Bangladesh, however, can simply be
modified to other settings as necessary.

This documentation is designed to give an overview of the code in the
``camps`` package, with only limited documentation of the JUNE
framework - leaving this to the JUNE code itself to be
documented.

We lay out the documentation in the following way:

1. First, we address the minmal high level changes needed to run the
   model for a new location - the :ref:`data inputs <data-inputs>` (how to construct
   the input data necessary to run the model), the :ref:`config file <configs>` changes which specify how the model is setup, and
   then how to :ref:`run the model <model-running>` model without changing anything else.

2. Once we have covered the higher level changes which can be made to
   the model, we turn to the lower level. Here, we address
   the operation of the code, and how they are used to provide a greater
   understanding of the underlying mechanics of the disease spread. We
   will also cover which bits
   might be changed to allow for more fine-grained control over the
   model. This includes a overview of the :ref:`model setup <model-setup>` and a dive into the way the :ref:`disease characteristics
   <disease-characteristics>` are handled.
3. Finally, we have some examples on changing or running particular
   parts of the code such as changing the disease from COVID-19 to
   :ref:`another airborne disease <new-airborne-disease>`.

Details of the use of this package are presened in our `paper
<https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009360>`_
which serves as a secondary source of documentation to add details to
those included here.

Please cite::


  @article{AylettBullock2021Operational,
    author = {Aylett-Bullock, Joseph and Cuesta-Lazaro, Carolina and Quera-Bofarull, Arnau and Katta, Anjali and Hoffmann Pham, Katherine and Hoover, Benjamin and Strobelt, Hendrik and Moreno Jimenez, Rebeca and Sedgewick, Aidan and Samir Evers, Egmond and Kennedy, David and Harlass, Sandra and Gidraf Kahindo Maina, Allen and Hussien, Ahmad and Luengo-Oroz, Miguel},
    title = {Operational response simulation tool for epidemics within refugee and IDP settlements: A scenario-based case study of the Cox’s Bazar settlement},
    year = {2021},
    doi = {10.1371/journal.pcbi.1009360},
    URL = {https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009360},
    journal = {PLoS Comput Biol},
    number = {17},
    volume = {10}
  }
