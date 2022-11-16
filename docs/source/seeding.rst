.. _infection-seeding:

Seeding the Infection
=====================

To model the spread of a disease, the model needs to know the initial
conditions of spread - i.e. who has the disease at the beginning of
the simualtion. To simulate disease spread from the beginning then it
might only be a few people. Alternatively, disease spread can be
simulated from a mid-way point, therefore possibly requiring a lot of
people to be infected when the simualtion is initialised. Manually
adding these infections into the is known as `seeding` the infection.

The seeding of infections is not just for the beginning of the
simulation. The model also allows users to specify any date on which
to add infections manually to the model. This means that initial
infections can be seeded over several days, e.g. adding 10 new
infections per day for 10 days. Additionally, new infections can be
added half way through the model run if so desired. This might be
useful, for example, in the case of seeding new variants part way
through the simulation.



Selectors
---------

The first step is to initialise the characteristics of the disease
itself. This is done through the ``InfectionSelector``. More details
on this can be found in the :ref:`Infection <disease-infection>`
section.

For now, we assume that the ``selectors`` are set up as follows::

  selector = InfectionSelector.from_file()
  selectors = InfectionSelectors([selector])

Seeding
-------

The seeding part is now very simple. The ``InfectionSeed`` class
handles the creation of the infection seeds. The class needs a
dataframe which is double indexed by age and date, and which specifies
the number of cases to seed as a percentage of people of a given age
in a given region.

The simplest implementations of these are::

  infection_seed = InfectionSeed.from_global_age_profile(
      world = world,
      infection_selector = selector,
      daily_cases_per_region = [dataframe],
      seed_past_infections = True,
      age_profile = [dataframe],
  )

The ``world`` is just the ``World`` class created at the beginning
(see :ref:`Model Setup <model-setup>`).

The ``infection_selector`` was created above.

The ``daily_cases_per_region`` dataframe contains the percentage of
the population on a given day in a given region who should be
infected.

If ``seed_past_infections`` is ``True`` then if the dataframe contains
people who should have been infected on a given date which has already
passed by the date on which the model is initiated, then the model
will ensure they are all still infected from day 0.

The ``age_profile`` dataframe is essentially a dictionary which
provides the weighting by age group of how the infections at the
regional level are to be spread across different ages. This is an
optional parameter, and if not set will uniformly weight all ages.

The other implementation is::

  infection_seed = InfectionSeed.from_uniform(
      world = world,
      infection_selector = selector,
      cases_per_capita = [number]
      seed_past_infections = True,
      date = [initial date]
  )

This implementation is very similar to the above but even
simpler. Here, the user just needs to tell the model the percentage of
people in the world to infect ``cases_per_capita`` and the ``date`` on
which to do this (in ``YYYY-MM-DD HH:MM`` format).

Immunity setting
----------------

The remaining piece is to set the immunity (or 'anti'-immunity) from
comorbidities, differences in susceptibility, prior infections and
vaccination.

We will not go into the details here, but the simplest implementation
is to assume that the population have comorbidities::

  immunity_setter = ImmunitySetter.from_file_with_comorbidities(
    comorbidity_multipliers_path = [path],
    male_comorbidity_reference_prevalence_path= [path],
    female_comorbidity_reference_prevalence_path = [path],   
  )

Details on the comorbidities can be found in the :ref:`Disease
Comorbidities <disease-comorbidities>` section.

Putting it all together
-----------------------

Finally, this is all combined into the ``Epidemiology`` class::

  epidemiology = Epidemiology(
    infection_selectors=selectors,
    infection_seeds=infection_seeds,
    immunity_setter=immunity_setter,
  )

See the `Quickstart notebook
<https://github.com/UNGlobalPulse/UNGP-settlement-modelling/blob/master/Notebooks/quickstart%20camp.ipynb>`_
in ``Notebooks/quickstart camp.ipynb`` for details on how this fits together into the model.






