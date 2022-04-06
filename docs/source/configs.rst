Model Configuration
===================

Config files handle various components of the model's dynamics,
including how the virtual 'day' is structured, how often people in the
model do different 'activities', how they interact and what
restrictions (such as physical distancing and lockdowns) are imposed
at what time.

All config files are in the ``configs_camps`` folder.

Global Config
*************

An example of the  global config file:
``configs_camps/config_example.yaml``.

We now go through the key components of the file:

1. Activities::
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
   activities. The term *leisure* is a legacy term used by the
   ``JUNE`` framework but refers to activities more than just those
   otherwise considered as leisure activities.

   The ``residence`` list provides all the possible classes of places
   people can live. In the case of Cox's Bazar, this just includes the
   ``shelters``.

   Finally, the ``medical_facility`` list includes all those possible
   places people can go if they need medical treatment once infected
   in the model. In the case of Cox's Bazar, this is just
   ``hospitals``.

2. Time::
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
*************************

The probabilities that certain people go to certain locations is based
on the activity config files. These can be found in the
``configs_camps/defaults/groups`` folder with ``.yaml`` files for each
location. The names are linked to their respective group distributors.

The requirements for each file are as follows::
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
as ``# times = 2*0.3 = 0.6``.

As a final example, if a person goes 2 times a week on average,
regardless of weekday or weekend then for the weekday ``# times =
2*(5/7) = 1.43`` and on the weekend ``# times = 2*(2/7) = 0.57``.

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
**********************



Policies
********
