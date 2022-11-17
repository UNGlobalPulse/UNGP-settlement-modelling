Data Outputs
============

When the model is running, the outputs are saved in a specified
folder, which defaults to a ``results`` folder in whichever directory
you're running the model from.

This folder contains: ``config.yaml`` which logs the interaction
parameters used to run the simulation (see :ref:`Interaction
Parameters <interaction-parameters>`); ``policies.json`` which
records details of the policies activated during the running of the
model as a dictionary; ``summary.csv`` which
gives details on the breakdown of infections, hospitalisations, deaths
and recovered people by day and region; ``june_record.h5`` which
provides highly detailed information recorded during the
simulation. This latter ``.h5`` file is made up of a collection of
dataframes which can be combined in a wide variety of ways.

The notebook in ``Notebooks/quickstart camps.ipynb``, together with
the equivalent `quickstart notebook
<https://github.com/IDAS-Durham/JUNE/blob/master/Notebooks/quickstart.ipynb>`_
in the `JUNE <https://github.com/IDAS-Durham/JUNE>`_ repo, contains
many exapmles of what you can derive from the ``summary.csv`` file and
the ``june_record.h5``. Examples of these include:

- Infections, hospitalisations and deaths by age and other
  characteristics and any geographical
  level of granularity
- The locations of where people get infected over time
- Deaths in specific household types
- Where people of a given age or other characteristic get infected
  over time
- Answering the question: in how many households has everyone been infected?

For more details on how this data is being recorded, and how to access
the information in the record, see the
``june/records/records_reader.py`` script.
