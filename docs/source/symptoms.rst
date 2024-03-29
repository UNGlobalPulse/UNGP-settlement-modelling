.. _disease-characteristics:

Disease Characteristics
=======================

By default, the ``JUNE`` framework is set up to model COVID-19. It has the
capacity to model multiple variants, where different parameters are
set relative to the wild-type (original) variant. however, the disease is able
to be changed.

**Note:** In this section we will run through how the disease is
set up in the ``JUNE`` code, with only a few references to the code in
this repository. We will try to make clear throughout which code we
are referring to. Some of these changes just require a different files
to be passed to certain imported ``june`` functions before eventually
being passed to a simulator which handles the running of the model, whereas
changes will require alterations to the ``JUNE`` code itself. To do these we recommend you locally install
``JUNE`` to make the necessary changes.

A walkthrough of how to change the disease characteristics for a
different disease (while still based on contact patterns is give in
:ref:`New Disease <new-airborne-disease>`)

.. _disease-infection:

Infection
---------

The first stage to setting up the infection and disease parameters is to set the infection
parameters. These are handled by the ``InfectionSelector`` which takes
in information about the transmission properties of the disease, how
people develop different symptoms, as
well as the ``HealthIndexGenerator``. These
are stored in the ``transmission_config`` file and describe details
about a person's infectiousness.

There are three possible shapes which are allowed by the ``JUNE`` code
without having to write any additional functions. These are a: constant
probabaility of infectiousness handled by the ``TransmissionConstant``
class; a function of the form ``x^n exp(-x/alpha)`` handled by the
``TransmissionXNExp`` class; and a gamm function handled by the
``TransmissionGamma`` class.

Each of the above shapes has its own particular input requirements
whic should appear in the ``transmission_config``. To change to any
other classes of functions, would have to be  manually edited.

For example in the case of COVID-19, infectiousness profiles are
constructed from `here
<https://www.nature.com/articles/s41591-020-0869-5>`_ and `here <https://arxiv.org/pdf/2007.06602.pdf>`_.

The ``HealthIndexGenerator`` is another component of the
``InfectionSelector`` and requires information about the rates at
which people end up in certain parts along the symptom trajectory
pipeline. Specifically, this utilises information about the
infection fataility rates (IFRs) of the population, broken down by different
demographic characteristics. This is becuase, when someone gets
infected, ``JUNE`` assigns them an endpoint trajectory based on these
probabailities. For example, one might be more likely to end up in
hospital and recover if they are more elderly than if they are
younger where they are more likely to end up only getting mild
symptoms and recovering.

The final input to the ``InfectionSelector`` is information on how
people might progress through the symptomatic pipeline given their
endpoint assigned to them. This is handled by the ``TrajectoryMakers``
class which uses information on the probabaility distributions of
spending time in these different stages.

.. _disease-comorbidities:

Comorbidities
-------------

The above section specifies how to set what happens to people who get
infected with the circulating agent. An additional change to this is
comorbidities. Specifically, we consider the effects of comorbidities
on a given persons' likelihood to develop more severe symptoms if
infected. I.e. these effect the probabilities calculated from the IFR
data of the population.

The comorbidities act as multipliers to the probabilities of optaining
the severe infection, or above, endpoints relative to the mild
infection endpoint. Their multipliers are placed in the
``configs_camps/defaults/comorbidities.yaml`` file. **Note:** The
names of the comorbidities should match those in the relevant
comorbidity data files.

The ``ImmunitySetter`` handles the addition of comorbidities.

**Note:** ``JUNE`` expects both information about the population being
modeled, as well as a reference population. Specifically, you may know
the disease parameters (IFR values etc.) for certain settings where
there is good disease surveillence, but might not know these for the
population being modeled expicitly. Therefore you may have already
accounted for comorbidities in ithe IFRs which then need to be
corrected for a different populations' comorbiditity prevalence
rates. This is done through calling the ``ImmunitySetter`` and passing
the prevalence rates of the population being modeled, and those of the
`reference` popualtion.

Physiological Age Correction
----------------------------

TODO:
- Add details here
