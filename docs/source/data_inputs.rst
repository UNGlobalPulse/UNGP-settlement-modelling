Data Inputs
===========

**Note:** There are two sources of data required to run the model -
the data for the camps (stored in ``$BASE/camp_data/``) and the data
for the ``JUNE`` more broedly which is set up to model the UK by
default. The latter comes already downloaded with the ``JUNE`` code
but can be added to the repository in ``$BASE/data/``. If configuring
``JUNE`` to use this data then modifications can be made to the
underlying ``JUNE`` data which is useful for editing disease parameter
characteristics. In this section we will only cover data in the
``camp_data`` folder which is related to the set up of the digital
twin of the camp in question.

The data to run the model is stored in the ``$BASE/camp_data/``
folder. There are multiple ways to structure the data folder, however,
the simplest way is to keep a consistent setup and naming convention
of files as there are defaults set in the code where appropriate. In
addition, each file is expected to be confingured in a certain way to
be read in by the necessary functions. The structure of the data
folder, the minimum input requirements will be covered here.

**Note:** This covers the contents of the ``camp_data`` folder and
does not cover configuration changes which could also be considered as
`input` data. See the 

The default data folder setup is as follows::

  camp_data
  ├── input
  │   ├── geography
  │   │   ├── area_coordinates.csv
  │   │   ├── super_area_coordinates.csv
  │   │	  └── area_super_area_region.csv
  │   ├── demography
  │   │   ├── age_structure_super_area.csv
  │   │   ├── area_residents_families.csv
  │   │   ├── [location, e.g. myanmar]_female_comorbidities.csv
  │   │	  ├── [location, e.g. myanmar]_male_comorbidities.csv
  │   │	  ├── uk_female_comorbidities.csv
  │   │	  └── uk_male_comorbidities.csv
  │   ├── activities
  │   │   └── [csv files with lat/lon coordinates]
  │   ├── hospitals
  │   │   └── hospitals.csv
  └── └── [other specilist locations, e.g. learning_centers]
  
We now go through each of these data elements to describe the
necessary input data.

.. _data-geography:

Geography
---------

In the ``geography/`` folder we include information about the
geogrpahy of the ``world`` we are modelling - e.g. a refugee settlement.

``JUNE`` operates on a three-tiered geographical hierarchy:
1. Regions: the highest level
2. Super areas: the middle level
3. Areas: the lowest level

As an example, in the case of the Cox's Bazar settlement: regions
correspond to the ~20 camps which make up the settlements; super areas
refer to the UNHCR deliniated blocks in whach camp; and areas refer to
the Majhee blocks. How to choose the components of the hierarchy
depends on the availablility of geo-tagged data, as well as the
availability of other data at these levels of geographical
disaggregation. For example, as described in later sections, we will
need data on the demographics of the population, however, these might
be available at only a specific set of geographical granularity
scales. Therefore, this might help make the decision about the
geographical areas considered in the hierarchy.

More details on the geographical heirarchy can be found in both the
original `JUNE-UK paper <https://royalsocietypublishing.org/doi/full/10.1098/rsos.210506>`_ and the `our paper
<https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009360>`_
describing JUNE's application to Cox's Bazar.

The following files are required to create the geography:

``area_coordinates.csv``

+--------------+----------+-----------+
|    area      | latitude | longitude |
+--------------+----------+-----------+
|  [area1_id]  |  [coord] |  [coord]  | 
+--------------+----------+-----------+
|  [area2_id]  |  [coord] |  [coord]  |
+--------------+----------+-----------+

where the area IDs are unique identifiers for each area in the world.

``super_area_coordinates.csv``

+-----------------+----------+-----------+
|    super_area   | latitude | longitude |
+-----------------+----------+-----------+
|[super_area1_id] |  [coord] |  [coord]  | 
+-----------------+----------+-----------+
|[super_area2_id] |  [coord] |  [coord]  |
+-----------------+----------+-----------+

``area_super_area_region.csv``

Once the coordinates of the areas and super areas have been given, we
just need to provide the hierarchical mapping of the geography. The
region coordinates don't need to be given explicitly, as they are
calculated implicitly from knowledge of the heirarchy.

The following is an example of the hierarchy:

+-----------+-------------------+----------------+
|    area   |     super_area    |     region     |
+-----------+-------------------+----------------+
|[area1_id] |  [super_area1_id] |  [region1_id]  | 
+-----------+-------------------+----------------+
|[area2_id] |  [super_area1_id] |  [region1_id]  |
+-----------+-------------------+----------------+
|[area3_id] |  [super_area2_id] |  [region1_id]  |
+-----------+-------------------+----------------+
|[area4_id] |  [super_area3_id] |  [region2_id]  |
+-----------+-------------------+----------------+

where in the above example, there area 4 unique areas - the first 2
are part of one super area, the 3rd and 4th are each then part of
their own super areas. The first three areas, and the first two super
areas are part of the first region, and the final area and super area
are part of another region.


Demography
----------

In the ``demography/`` folder we include information about the world's
population. This is generally derived from census-type data, or other
literature.

In addition, to data on e.g. age and sex characteristics, we will also
include data on the comorbidities of the popualation. For the case of
Cox's Bazar, we use data on the comorbidity prevalence rates in
Myanmar (as a proxy for the Rohingya refugees). Data on the UK
population (which is the reference population in the ``JUNE``
framework) is also required ro correct the symptomatic progression
probabilities.

**Note:** If data is not availability at the granularities dpecified
in this documentation, then the available data may need to
preprocessed outside the model to project up and/or down (aggregate or
disaggregate) in
granularities. Indeed, if the user so wishes, they can edit the
appropriate source code to accomodate the different levels of granularity.
 
The following files are required to initialise the population:

``age_structure_super_area.csv``

Contains information on the population by age and sex at the super
area level. Any age bins can be used, disggregated by females and
males. The following is an example of the formatting of the file:

+-----------------+--------+--------+---------+---------+---------+---------+
|   super_area    | F 0-20 | M 0-20 | F 21-60 | M 21-60 | F 61-99 | M 61-99 |
+-----------------+--------+--------+---------+---------+---------+---------+
|[super_area1_id] |  #     |  #     |   #     |   #     |   #     |  #      |
+-----------------+--------+--------+---------+---------+---------+---------+
|[super_area2_id] |  #     |  #     |   #     |   #     |   #     |   #     |
+-----------------+--------+--------+---------+---------+---------+---------+

where ``F []-[]`` denotes the number of females between the ages in
brackets and ``#`` is a placeholder for the number of people in each
column by super area.


``age_residents_families.csv``

Specifies the number of residents and families by area. The numbers
should match up with the total number of people in the super area of
those areas.

**Note:** As mentioned above, if this data doesn't exist at the area
level, the data can be projected down onto the area level as an
approximation.

+--------------+----------+-----------+
|    area      | families | residents |
+--------------+----------+-----------+
|  [area1_id]  |  #       |  #        | 
+--------------+----------+-----------+
|  [area2_id]  |  #       |  #        |
+--------------+----------+-----------+

``[location]_female_comorbidities.csv``

Distribution of comorbidities by age - different file for each
sex. The following is an example of the formatting of the file:

+-----------------+---+----+----+----+----+----+----+----+----+----+---+
|   comorbidity   | 5 | 10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 99|
+-----------------+---+----+----+----+----+----+----+----+----+----+---+
|  [comorbidity1] | % | %  |  % |  % |  % |  % |  % |  % |  % |  % |  %|
+-----------------+---+----+----+----+----+----+----+----+----+----+---+
|  [comorbidity2] | % | %  |  % |  % |  % |  % |  % |  % |  % |  % |  %|
+-----------------+---+----+----+----+----+----+----+----+----+----+---+

where the ``comorbidity`` column is populated with a list of possible
comorbidity names. The column names of the subsequent rows denote the
maximum age in that age bin. For example the 1st column headed ``5``
is people in the age bracket ``0-5``, whereas the 2nd column denotes
people in the age bracket ``6-10``. This formatting is thereofre
slightly different to that over the age structure file. The ``%``
people people in each age bracket should be given as a float - e.g. if
10% of people between the ages of 6-10 have comorbidity2, then that
element of the table should be ``0.1``.

``[location]_male_comorbidities.csv``

Same as above for men in the world population.

``uk_female_comorbidities.csv``

As above but for the reference population - in this case the UK.

``uk_male_comorbidities.csv``

As above but for the reference population - in this case the UK.


Activities
----------

In the ``activities/`` folder we store information on the locations of
places in the model we want to specifically model and in which people
in the model can go to. Each type of location should have its own
``csv`` file in this folder which specifies the latitude/longitude
coordinates of those relevant locations.

In the case of the Cox's Bazar model, we
include the following locations:
- Community centers and other communal location (``communal.csv``)
- Female-friendly spaces (``female_communal.csv``)
- Food distribution centers (``distribution_center.csv``)
- E-voucher outlets (``e_voucher_outlet.csv``)
- LPG, blanket, et.c distribution centers (``non_food_distribution_center.csv``)
- Religious centers (``religious.csv``)

Here each file is formatted just as a list of latutudes and longitudes
as follows:

+----------+-----------+
| latitude | longitude |
+----------+-----------+
|  [coord] |  [coord]  | 
+----------+-----------+
|  [coord] |  [coord]  |
+----------+-----------+

Hospitals
---------

Even if not explicitly modelled, the model will always require the
presence of some hospitals which patients can go to if/when they get
infected and have particularly severe infections. This file is
formatted in the same way as the activties files above.

Other
-----

There may be other locations which are worth having other folders for
which contain relevant information on their locations and other
attributes.

In the case of Cox's Bazar, we have a ``learning_centers/`` folder
which contains information on the enrollment rates of students by sex,
age and region (``enrollment_rates.csv``), as well as a file, like
those in the activties folder, specifying the locations of the
learning centers (``learning_center.csv``).
