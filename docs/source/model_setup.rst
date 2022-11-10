.. _modelsetup:

Model Setup
===========

Geography/World


``JUNE`` operates on a threetiered geographical hierarchy:
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

On the :ref:`datainputs` page we discussed the :ref:`datageography` data required. Here we set up the heirarchy and provide the
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
this the :ref:`setupdemography` section.

.. _setupdemography: 

Demography


TODO:
 Reference back to data inputs
 Add something on code to set up demography

Households/Shelters


TODO:
 Reference back to data inputs page

The households in the camp are initialised based the data contained within camp_data/input/households/.
This folder contains three files;

**1.** area_residents_families.csv informs the distributor of the demography of the population
**2.** area_household_structure.csv informs the distributor of household types and household properties 
   in each area
**3.** household_structure.yaml informs the distributor of the distribution of household sizes across the camp

Given the number of households provided in area_household_structure.csv per venue we initialise empty households of sizes
of the correct frequency determined by household_structure.yaml household_sizes distribution. Each of these households
is placed into a sublists of each household type::
   Houses with children
   Houses without children
   Houses with single occupants
   Houses with multigenerational families
The length of each of these lists is proportionate to the relevent fractions of households of each type determined from 
area_household_structure.csv. For each household we generate the following parameters (where appropitate for the household type)
   Spousal age gap (area_household_structure.csv "avgAgeDiff")
   First child mother age gap (area_household_structure.csv "MotherFirst Child Age Diff")
   Number of children (area_household_structure.csv "children per family")
   mother grandmother age gap (First child mother age gap)
   Age gap between children = 1 year
In each of these parameters we allow for a small deviation. First we place random young adults, and if appropiate add a spousal 
partner of the oposite sex. Then children are distributed obeying the appropiate age gaps between children and parents and siblings.
Lastly we distribute older adults to multigenerational households.

After this procedure there can be a small number of leftover individuals which we place in households randomly in which there remains 
space.

To form shelters we randomly combine two of 75% of the total households to form a shared multiple family shelter of two households. The remaining 25% of households form 
a single household shelter. 



Activities/Locations


TODO:
 Reference back to data inputs page
 Add something on construction of locations  referencing back to
  main JUNE

.. _setupinteractions:
  
Interactions


Policies




