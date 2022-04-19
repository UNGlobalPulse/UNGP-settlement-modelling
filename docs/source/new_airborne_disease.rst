.. _new-airborne-disease:

Example: New Airborne Disease
==============================

In this example we walk through the changes required to simulate the
spread of a new airborne disease. We utilise the fact that by default
the ``JUNE`` framework simualtes the spread of COVID-19 and demostrate
the require modifications to adjust to other such diseases.


To begin with we assume that we have already created a
:class:`.CampWorld` which has an associated population and geography
and where the possible activities people can go to have been
distirbuted to the population. We also assume that the policies have
been created and saved to ``policies``, along with the
``infection_seeds`` and ``interaction`` patterns (respectively covered
in :ref:`configs-policies`, :ref:`infection_seeding` and :ref:`interactions`). What remains is then to initialise the
various disease characteristics and pass everything to the
``Simulator`` which handles the running of the model.

Following those steps laid out in :ref:`disease-characteristics`, we
first need to set up the ``InfectionSelectors``. These handle the characteristics
of the infectiousness of infected people in the model, the
probailities of how people travel through the different healthcare
trajectories (e.g. whether they have mild symptoms and record, develop
sever symptoms and then go to hospital and die etc.), and on the way
through that trajectory, how long people spend in each stage. This is
described in more detail in :ref:`disease-infection`.

To create the selectors we first need to have the following three
files:

**1.** ``tranmission_config`` - a ``.yaml`` file which contains the
details of the transmission. For simplicity, we can choose a
constant tramission probability of 0.1. This would then go into a file
looking like::
  tranmission_type: constant

  probability: 0.1

**2.** ``rates_file`` - a ``.csv`` file which contains the likehihoods
by by demographic age groups that people end up in different parts of
the symptomatic trjectory endpoints. For simplicity we recommend
you make a copy of, and edit:
``$BASE/data/input/health_index/infection_outcome_rates.csv``

**3.** ``trajectories_config`` - a ``.yaml`` file which contains the
details of the time to complete different stages of the trajory given
a particualr endpoint. For simplicity, we recommend you make a copy
of, and
edit:``june/configs/defaults/epidemiology/infection/symptoms/trajectories.yaml``
to ensure all the different possibilities can be explored.

Once these files have been created and put in a place of your
choosing, you can create the selectors::
  selector = InfectionSelector.from_file(
      transmission_config_path = [path to transmission_config],
      trajectories_config_path = [path to trajectories_config],
      rates_files = [path to rates_file]
  )
  selectors = InfectionSelectors([selector])


This handles the main infection parameters for a given disease. As
discussed in :ref:`disease-characteristics` we might also have
comorbiditis in the popualtion which are going to affect the
trajectories. If these numbers are not already naturally acounted for
in the underlying ``rates_file`` then we can boost certain agent's
likelihood of progressing to the severely infected stage by
distributing comorbidities to certain people in the model and setting
this boosting factor. This is described in more detail in :ref:`disease-comorbidities`.

To set cormorbidities, we need a comorbidities file which determines
how each comorbidity boosts the likelihood of progressing to and
symptomatic endpoint which goes through the severely symptomatic stage
in the symptomatic trajectory. We recommend you take the
``configs_camps/defaults/comorbidities.yaml`` as an example and adjust
this to the relevant comorbidites. As discussed in
:ref:`disease-comorbidities`, we also need the prevalence rates. See
:ref:`data-demography` for more details on this.

We distribute comorbidities to the population::

  comorbidity_data = load_comorbidity_data(
      [path to male popualtion comorbiditiy prevalences],
      [path to female popualtion comorbiditiy prevalences],
  )
  
  for person in world.people:
      person.comorbidity = generate_comorbidity(person, comorbidity_data)
     
Once these files have been created, we can create the
``ImmunitySetter``::

  immunity_setter = ImmunitySetter.from_file_with_comorbidities(
      comorbidity_multipliers_path [path to comorbidities file],
      male_comorbidity_reference_prevalence_path = [path to male reference popualtion comirbidity prevalences],
      female_comorbidity_reference_prevalence_path = path to female reference popualtion comirbidity prevalences],
  )

**Note:** These reference popualtion files are the UK prevalence rates
by default, which assumes that the user wants to model a population
based on the UK population, or simialar, where disease data is well
reported. If you know the data for the ``rates_file`` for the
population you're modelling then you can set these reference
prevalences to ``0`` everyehere.

Finally, putting all of this together we can create the
``Epidemiology`` class::

  epidemiology = Epidemiology(
      infection_selectors=selectors,
      infection_seeds=infection_seeds,
      immunity_setter=immunity_setter,
  )

which is ultimately passed to the ``Simulator``::

  Simulator.ActivityManager = CampActivityManager
  simulator = Simulator.from_file(
      world=world,
      interaction=interaction,
      leisure=leisure,
      policies=policies,
      config_filename=CONFIG_PATH,
      epidemiology=epidemiology,
      record=record,
  )

