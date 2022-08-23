.. _contact_tracker:

The contact tracker
====================

In this example we walk through the changes required to simulate the
virtual contact matrix surveys. We utilise the fact that by default
the ``JUNE`` framework simualtes the spread of COVID19 via contact 
interaction matrices which can also be used to simulate contact surveys.

To begin with we assume that we have already created a
:class:`.World` which has an associated population and geography
and where the possible activities people can go to have been
distirbuted to the population. What remains is then to initialise the
tracker with the venues we wish to survey and pass everything to the
``Simulator`` which handles the running of the model.

The Tracker class iteratively performs contact surveys over all venues that are specified from the World. They are two survey types implemented. Firstly the "1D" contact survey in which for each person of each subgroup type at a venue are made to interact with the required number of contacts of each subgroup type based on a poisson sampling distribution of the input contact matrices. Or secondly the "All" contact survey in which every person at a venue contacts every other person at a venue (independent of input contact matrices). 

In these virtual surveys we bin the contacts based on the interaction bins and a ages binning e.g. [0, 1, 2, .... , 99]. After the tracker is complete these matrices can be normalised into three types;
**1.** CM_T: The total contacts per day.

**2.** NCM: The total contacts per day per capita for each venue

**3.** NCM_R: The total contacts per day per capita for each venue accounting for reciprocal contacts
  

To create the tracker we first need to have the following two
files/paths:

**1.** ``load_interactions_path``  a ``.yaml`` file which contains the
details of the interactions. If none is specifed the default interaction file will be read.
The file will contain entries resembling this example::
  household:
    contacts: [[1.2,1.27,1.27,1.27],[1.69,1.34,1.3,1.3],[1.69,1.47,1.34,1.34],[1.69,1.47,1.34,2.00]]
    proportion_physical: [[0.79,0.7,0.7,0.7],[0.7,0.34,0.4,0.4],[0.7,0.4,0.62,0.62],[0.7,0.62,0.62,0.45]] 
    characteristic_time: 12
    type: Discrete
    bins: ["kids","young_adults","adults","old_adults"]
Here we specify the venue name (household), the contact matrix (the number of contacts per capita by bin group), the proportion physical contact matrix (faction of contacts which are physical), characteristic time (mean amount of time spent at the venue per visit) and the bin type (can be "Discrete" or "Age") and lastely the bin names. An example with Age based binning would be the following::
  pub:
    contacts: [[0,0], [0, 3]]
    proportion_physical: [[0.12,0.12],[0.12,0.12]]
    characteristic_time: 3
    type: Age
    bins: [0,18,100] 

**2.** ``record_path`` The path in which to save out the results and or make plots.

To construct the ``Tracker`` class we feed in the following parameters::

**1.** world. The world class with it's asscoiated population and geography

**2.** record path. Path to save out tracker results

**3.** group_types. List of world.venues for the tracker to run over. E.g. 
   group_types = [
    world.households,
    world.care_homes,
    world.schools,
    world.hospitals,
    world.companies,
    world.universities,
    world.pubs,
    world.groceries,
    world.cinemas,
    world.gyms,
    world.city_transports,
    world.inter_city_transports, 
   ]

**4.** load_interactions_path. Filepath for the interactions yaml file containing the contact matrices. If a non standard interactions.yaml file is used each supergroup structure has to be initialised with .Get_Interaction(Interactions_File_Path) for example::

   Hospitals.Get_Interaction(Interactions_File_Path)
   geography.hospitals = Hospitals.for_geography(geography)

   Schools.Get_Interaction(Interactions_File_Path)
   geography.schools = Schools.for_geography(geography)

   Companies.Get_Interaction(Interactions_File_Path)
   geography.companies = Companies.for_geography(geography)
   
If none is specified the groups will be constructed with default parameters. 

**5.** contact_sexes. List of sexes to track for individual contact matrices by sex. E.g.
   contact_sexes = ["unisex", "male", "female"]
   contact_sexes = ["unisex"]
   

**6.** Tracker_Contact_Type. List of contact tracking survey types to be performed. E.g.
   Tracker_Contact_Type=["1D", "All"]

**7.** MaxVenueTrackingSize. Integer maximum number of venues of each type to survey. Picks a random subset list of each venue type up to length MaxVenueTrackingSize. Default value np.inf (all venues surveyed).


Finally, putting all of this together we can create the
``Tracker`` class::

  tracker = Tracker(
    world=world,
    record_path=Results_Path,
    group_types=group_types,
    load_interactions_path=Interactions_File_Path,
    contact_sexes=["unisex", "male", "female"],
    Tracker_Contact_Type=["1D", "All"]
  )

which is ultimately passed to the ``Simulator``::

  simulator = Simulator.from_file(
    world=world,
    epidemiology=epidemiology,
    interaction=interaction, 
    config_filename = CONFIG_PATH,
    leisure = leisure,
    travel = travel,
    record=record,
    policies = policies,
    tracker = tracker,
  )
  
Lastly, tracker == None or the tracker keyword can be ommited entirely to run the simulator without the tracker.

After the simulation is complete the tracker results can be rebinned in the following ways;
  For adult  children contacts
    simulator.tracker.contract_matrices("AC", np.array([0,18,60])) 
  For custom age bins
    simulator.tracker.contract_matrices("Paper",[0,5,10,13,15,18,20,22,25,30,35,40,45,50,55,60,65,70,75,100])
    
Then the results can be summerised to the terminal and to file with the following
   simulator.tracker.post_process_simulation(save=True)
   
If save == True is specified, the results are saved out to record_path / Tracker. There will exist a set of folders containing key results about the tracker.
   CM_yamls: Summaries in .yaml files of the final contact matrices of each type for each tracker type.
   CM_metrics: Summaries of assortivness metrics for each contact matrices of each type and tracker type.
   junk: Intermediate saving files. Can be ignored.
   Venue_AvContacts: Normalised average contacts per person per day per veneue
   Venue_CumTime: The cumalative time spent at each venue. sum(Npeople_Venue * dt ) for each venue.
   Venue_Demographics: Unique persons per age bin to visit each venue type during the simulation.  
   Venue_TotalDemographics: The cumalative number of visits at each venue.
   Venue_TravelDist: Histogram of the travel distances between venues and each persons household
   Venue_UniquePops: Number of unique people at a subset of venues per day ("_ByDate") and also per timestep ("_BydT") and per sex in seperate files.
