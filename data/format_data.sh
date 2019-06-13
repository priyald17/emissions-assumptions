#!/bin/bash

#################################################
# Format all data
#################################################

# CEMS hourly data and hourly differences
echo cems
cd cems
python cems_formatting.py  --aggRegion isorto
python cems_formatting.py  --aggRegion nerc
cd ..

# PJM hourly generation by fuel
echo pjm_gen_by_fuel
cd pjm_gen_by_fuel
python pjm_gen_by_fuel_formatting.py
cd ..

# PJM hourly marginal fuel proportions
echo pjm_marginal_fuel
cd pjm_marginal_fuel
python pjm_marginal_fuel_formatting.py
cd ..

# PJM hourly metered loads
echo metered_loads
cd metered_loads
python metered_loads_formatting.py
cd ..
