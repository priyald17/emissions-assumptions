#!/bin/bash

#################################################
# Reproduce data and plots
#################################################

# Format data
echo FORMAT_DATA
cd data
bash format_data.sh
cd ..

# Calculate factors
echo CALCULATE_FACTORS
cd factor_estimates
bash estimate_factors.sh
cd ..

# Plot intervention effects
echo PLOT_INTERVENTIONS
cd interventions
bash run_interventions.sh
cd ..
