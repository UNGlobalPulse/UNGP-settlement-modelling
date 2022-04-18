.. _model-setup:

Model Setup
===========

Geography/World
---------------

``JUNE`` operates on a three-tiered geographical hierarchy:
1. Regions: the highest level
2. Super areas: the middle level
3. Areas: the lowest level

As an example, in the case of the Cox's Bazar settlement: regions
correspond to the ~20 camps which make up the settlements; super areas
refer to the UNHCR deliniated blocks in whach camp; and areas refer to
the Majhee blocks.

Much of the code handling the creation of the geography is using that
of the ``JUNE`` code. Some modifications have been made to allow for a
simpler input format.

On the :ref:`data-inputs` page we discussed the :ref:`data-geography` data required. Here we set up the heirarchy and provide the
coordinates for the super areas and areas.

These files are utilised by the :class:`.CampGeography` class which
generates the geography. This class inherits from the make ``JUNE``
class ``Geography``. If you want to only generate a subset of the
possible geographic areas then the ``filter_key`` option can be used
to pass a list of areas, super areas or regions which you want to
initialise. An example of doing this is in the ``Notebooks/quickstart camps.ipynb`` notebook.

Once the geography class is created we can create the ``world`` which
is where everything is eventually stored (geography, popualation,
locations etc.).

The :class:`.CampWorld` class sets up the ``world`` and the
geographical areas are created. A simple example of setting this up is
in the :func:`.generate_empty_world` function which also initialises
an empty ``Population`` class (imported from ``JUNE``). We will cover
this the :ref:`setup-demography` section.

.. _setup-demography: 

Demography
----------

TODO:
- Reference back to data inputs
- Add something on code to set up demography

Households/Shelters
-------------------

TODO:
- Reference back to data inputs page
- Add something on construction of households
- Add something on construction of shelters

Activities/Locations
--------------------

TODO:
- Reference back to data inputs page
- Add something on construction of locations - referencing back to
  main JUNE

Policies
--------



