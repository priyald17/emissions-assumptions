#!/bin/bash

#################################################
# Get factor estimates and plots
#################################################

# Average factors
echo aefs
python get_factor_estimates.py --factorType average

# Marginal factors
echo mefs
python get_factor_estimates.py --factorType marginal

# Plotting
echo plotting
python get_plots.py
