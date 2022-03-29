Inputs
======
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
  
Geography
*********

In the ``geography/`` folder we include infromation about the
geogrpahy of the ``world`` we are modelling - e.g. a refugee
settlement.

``JUNE`` operates on a three-tiered geographical hierarchy:
1. Regions: the highest level
2. Super areas: the middle level
3. Areas: the lowest level

As an example, in the case of the Cox's Bazar settlement: regions
correspond to the ~20 camps which make up the settlements; super areas
refer to the UNHCR deliniated blocks in whach camp; and areas refer to
the Majhee blocks.

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

Outputs
=======
