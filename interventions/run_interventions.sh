#!/bin/bash

#################################################
# Get intervention plots
#################################################

# Building lighting
echo building_lighting
python run_intervention.py --case building_lighting

# Demand response
echo demand_response
python run_intervention.py --case demand_response

# Summer load
echo summer_load
python run_intervention.py --case summer_load
