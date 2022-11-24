# Project Title
pybroker - a trivial but complete broker for Cloud Foundry in python/Flask

## Introduction

See the "cf-broker" project for an improved/updated version of this.

"pybroker" is a complete but minimal cloud foundry broker written in
python using the Flask framework.

It implements a service "Imaginary Service" that provides large dreams
or small dreams.  It merely maintains an internal data structure with
instances that have been created and bound.

The data stored at the instance creation and binding are the data
POSTed into the broker endpoints - so it may be used to test what is
in the data structures.

## Creating the broker
A simple "cf push" by admin will run the broker.py application, it is
probably best if this is pushed into a system space/org.

The shell scripts "expose-broker.sh" and "hide-broker.sh" are cf-cli
scripts that will (respectively) instantiate the broker application as
a service and place it in the marketplace, and the "hide-broker" will
remove it.

Note that re-pushing the application destroys "data structure" and
GUIDs in the application - which will confuse the market place
bindings.  The hide-broker/expose-broker are intended to mitigate
issues that will arise from re-pushes.  Investigate the cf-cli
purge-service-binding/purge-service-offering to recover from
re-pushes.

## Testing
A simple "test-broker.sh" script is intended to verify correct
operation of the broker.  More contributions here are welcome.

### Dependencies

"pybroker" uses Flask and logger (see requirements.txt).
