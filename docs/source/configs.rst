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

The probabilities 

Interaction Parameters
**********************

Policies
********
