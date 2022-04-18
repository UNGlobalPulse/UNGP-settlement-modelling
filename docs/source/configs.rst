.. _configs:

Model Configuration
===================

Config files handle various components of the model's dynamics,
including how the virtual 'day' is structured, how often people in the
model do different 'activities', how they interact and what
restrictions (such as physical distancing and lockdowns) are imposed
at what time.

All config files are in the ``configs_camps`` folder.

Global Config
-------------

An example of the  global config file:
``configs_camps/config_example.yaml``.

We now go through the key components of the file:

**1. Activities**
::
  activity_to_super_groups:
    primary_activity: []
    leisure: []
    residence: []
    medical_facility: []

The ``primary_activity`` here refers to a list of all activities
which have fixed time points at which the activity is done. In the
case of Cox's Bazar, this is only the ``learning_centers`` as the
times at which all
other activities which people in the model might perform are chosen
based on probability distributions of attendance frequency.

The ``leisure`` list will give all probabilistically chosen
activities. The term -leisure- is a legacy term used by the
``JUNE`` framework but refers to activities more than just those
otherwise considered as leisure activities.

The ``residence`` list provides all the possible classes of places
people can live. In the case of Cox's Bazar, this just includes the
``shelters``.

Finally, the ``medical_facility`` list includes all those possible
places people can go if they need medical treatment once infected
in the model. In the case of Cox's Bazar, this is just
``hospitals``.

**2. Time**
::
  time:
    initial_day: '2020-05-24'
    total_days: 120
    step_duration:
      weekday:
	0: 2
	1: 2
	.
	.
	.
      weekend:
	0: 2
	1: 2
	.
	.
	.
    step_activities:
      weekday:
	0: ['medical_facility', 'residence']
	1: ['medical_facility', 'leisure', 'residence']
	.
	.
	.
      weekend:
	0: ['medical_facility', 'residence']
	1: ['medical_facility', 'leisure', 'residence']

The ``initial_day`` covers the date on which the simualtion starts
(i.e. in the past, future or present).

The ``total_days`` is the number of days it will run for.

The ``step_duration`` speciied the timeslot lengths at which each
activity can be chosen, indexed by numbers. In the example above,
there are at least two possible time slots each 2 hours long. These
occur on both weekdays and weekends. (``JUNE`` lets the user
specify different types of day stuructures on weekdays and
weekends).

The ``step_activities`` utilises the day set up structure to
specify which activities people cas choose in these slots. For
example, ``medical_facilitiy`` is generally always active, however,
in some circumstances (e.g. when in short supply) they might not be
always available.


Activity/Location Configs
-------------------------

The probabilities that certain people go to certain locations is based
on the activity config files. These can be found in the
``configs_camps/defaults/groups`` folder with ``.yaml`` files for each
location. The names are linked to their respective group distributors.

The requirements for each file are as follows
::
  times_per_week:
    weekday:
      male:
	[min_age]-[max_age]: [# times]
	.
	.
	.
      female:
	[min_age]-[max_age]: [# times]
	.
	.
	.
    weekend:
      male:
	[min_age]-[max_age]: [# times]
	.
	.
	.
      female:
	[min_age]-[max_age]: [# times]
	.
	.
	.
    hours_per_day:
    weekday:
      male:
	[min_age]-[max_age]: [age]
	.
	.
	.
      female:
	[min_age]-[max_age]: [age]
	.
	.
	.
    drags_household_probability: [probability]
    neighbours_to_consider: [#]
    maximum_distance: [#]

The ``times_per_week`` sets, by age and sex, the regularity with which
people attend certain locations during the weekdays or weekends (as
defined by the global config file). This is calculated by look
determining how many times per weekday or weekend a person visits
those locations on average.

For example, if a person attends a community centre 2 times on average
during the weekday, then ``# times = 2``.

To make it more complicated, if
there is a 30% change that someone in a given age and sex bracket will
go to an activity and that if they do then they will go 2 times per
weekday on average, then this can be represented as a meanfield effect
as ``# times = 2-0.3 = 0.6``.

As a final example, if a person goes 2 times a week on average,
regardless of weekday or weekend then for the weekday ``# times =
2-(5/7) = 1.43`` and on the weekend ``# times = 2-(2/7) = 0.57``.

The ``hours_per_day`` specifies the number of hours with which a
person of those demographic characteristics, can do the activity in a
give day. For example, in the case of Cox's Bazar, a person has 8
hours per day in which they can choose (across multiple time slots)
which activities to do.

The ``drags_household_probability`` sets the chance that, if someone
decides to do an activity, they will bring their whole
household/family with them. For example, this might be more likely to
be the case when visiting other households.

The ``neightbours_to_consider`` parameter sets the number of possible
nearby venues, within the radius (in km) of where they live set by the
``maximum_distance`` parameter, which a person might consider
visiting. For example, if::
  neighbours_to_consider: 5
  maximum_distane: 10
  
then the person will randomly choose one of 5 possible venues to visit
for that activity as long as each of the 5 are within a 10km radius of
where they live. The reason the ``neighbours_to_consider`` parameter
is needed, rather than each time selecting randomly a venue within the
radius is twofold: i) people often only regularly visit a handful of
local venues of given types rather than always randomly choosing based
on proximity; and ii) for computational efficency, the number of
possible selectable venues is pre-computed when the model is
initialised to save on random number generation.

**Note:** In theory, one is not restricted to setting regularities of
attendance based only on age and sex. Other characteristics can be
readily added by modifying the distributor classes of the given venues.
      

Interaction Parameters
----------------------

Related to the disease characteristics, the interaction parameters
control how intense interactions between people in the model are. This
affects the probability of being infected given the presence of an
infected person in the same venue as another person at the same time.

Details on the use and implementation of these interaction parameters
(`betas`) can be found in the main `JUNE paper <https://royalsocietypublishing.org/doi/full/10.1098/rsos.210506>`_.

Interaction parameters are controlled by a ``.yaml`` file passed to
the ``Interaction`` class. This is stored in the
``configs_camps/defaults/interaction/`` folder. There are several key
sets of interaction parameters::
  alpha_physical: [#]
  betas:
    religious: [#]
    distribution_center: [#]
    .
    .
    .
  contact_matrices:
    religious:
      contacts: [matrix]
      proportion_physical: [matrix]
      characteristic_time: [#]
    distribution_center:
      contacts: [matrix]
      proportion_physical: [matrix]
      characteristic_time: [#]

Contacts between people in the model can induce disease spread if one
of these people are infected. The number of contacts between people of
different ages in different venues is contolled by the
``contact_matrices``. Contacts are divided into two categories: i)
physical and non-physical. The total number of contacts is given by a
contacter-contactee matrix in the ``contacts`` element. The ``proportion_physical`` matrix denotes
what percentage of each type of contact (i.e. elemenet of the contact
matrices) are physical (i.e. have a higher internsity). The contact
matrices are generally derived from surveys of the population.

The intensity of contacts (which scales the probability of infection
given a contact) is handled by the ``betas``. These have a maximum
value of ``1.0``. The scaling of these betas when contacts are
physical are handled by the ``alpha_physical`` parameters which
scales, irrespective of the location.

**Note:** In general, when fitting the model it is these ``betas`` and
``alpha_physical`` parameters which are considered free fitting parameters.
      
Policies
--------

Policies handle the interventions and behaviour changes in the model
due to e.g. government measures, people changing their behaviour due
to the disease, etc.

``JUNE`` allows for many policy choices and changes and more can be
added through designing new classes of policies. An example of adding
a new policy class can be seen in ``camps/policy/isolation.py``.

All policies are
given a ``start_time`` and ``end_time`` in ``datetime`` format.

Examples of policy file setups can be found in the
``configs_camps/defaults/policy/`` folder or in the main ``JUNE``
folder: ``june/configs/defaults/policy/``.

The standard policies which can be implemented are:

1. ``hospitalisation`` which should be set all the time if hospitals
   are available and specifies that people should be hopitalised if
   necessary.

2. ``severe_symptoms_stay_home`` specifies during what period those
   with severe symptoms should stay home (i.e. if someone progresses
   to severe symptomatic level then they are considered too ill to
   leave the home). This should be active the whole time if the
   categorisation of severe symptoms is considered bad enough.

3. ``quarantine`` specifies for how many days a symptomatic person
   should quarantine in their home for and with what level of
   compliance people quarantine. Similarly, this policy allows you to
   set the number of days other household members must quarantine for
   if someone else in their household is symptomatic. The household's
   level of compliance can also be set in this policy.

4. ``shielding`` can be used to ensure people over a certain age do
   not leave their homes as regularly. A minimum age is set to
   determine this, as well as a compliance factor.

4. ``social_distancing`` where the ``betas`` are scaled by
   ``beta_factors`` to simualte the effects of social/physical
   distancing.

5. ``close_leisure_venue`` allows for the specification of closing
   specific venues completely for certain periods of time.

6. ``change_leisure_probability`` specifies a new temporary set of
   ``times_per_week`` for specific venues and demographics. Any set of
   venues or demographics not specified in the policy are taken from
   the above mentioned activity configs as default values.

7. ``mask_wearing`` acts in a similar way to the ``social_distancing``
   policy. The compliance with mask wearing can be set at the level of
   different types of venues, as well as the
   overall reduction in the ``betas`` due to the efficacy of the
   mask. The new value of the ``betas`` is calculated as::
     1 - ([overall compliance]-[venue compliance]-(1-[mask efficacy
     beta reduction]))

**Note:** In the current implementation, compliance factors do not
denote specific individuals who are compliant and those who are not,
rather it acts as a mean field effect.
