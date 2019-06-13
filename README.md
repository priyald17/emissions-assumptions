# How much are we saving after all? Characterizing the effects of commonly-varying assumptions on emissions and damage estimates in PJM

This repository is by 
[Priya L. Donti](https://www.priyadonti.com), [J. Zico Kolter](http://zicokolter.com), and [Inês Azevedo](https://inesazevedo.org) and contains the Python source code to
reproduce the experiments in our paper "How much are we saving after all? Characterizing the effects of commonly-varying assumptions on emissions and damage estimates in PJM."

# Introduction

In recent years, several methods have emerged to estimate the emissions and health, environmental, and climate change damages avoided by interventions such as energy efficiency, demand response, and renewables integration. However, differing assumptions employed in these analyses could yield contradicting recommendations regarding intervention implementation. We test the magnitude of the effect of using different key assumptions -- average vs. marginal emissions, year of calculation, temporal and regional scope, and inclusion of non-emitting generation -- to estimate PJM emissions and damage factors. We further highlight the importance of factor selection by evaluating three illustrative 2017 power system examples in PJM.

Please see our paper for additional details.

## Setup and Dependencies

This code uses Python 3. All Python-related dependencies can be installed into a
[conda environment](https://conda.io/docs/user-guide/tasks/manage-environments.html)
using the [environment.yml](./environment.yml) file.

Cloning this repository also requires [Git Large File Storage](https://git-lfs.github.com/), which is used to store some of the raw data files. 

## Usage

To run all experiments, simply run the following command:
`bash run_all.sh`

You can also see pre-run results and visualizations by viewing the notebook files in this repository (which end with the extension `.ipynb`). The structure of this repository is below.

```
run_all.sh - Script to reproduce all experiments.
data
├── format_data.sh - Script to format all data.
├── cems - Folder containing raw CEMS data, formatting scripts, and notebooks.
├── metered_loads - Folder containing raw metered load data, formatting scripts, and notebooks.
├── pjm_gen_by_fuel - Folder containing raw PJM generation by fuel data, formatting scripts, and notebooks.
├── pjm_marginal_fuel - Folder containing PJM marginal fuel type, formatting scripts, and notebooks.
├── date_helpers.py - Helper functions for parsing and formatting dates.
factor_estimates
├── estimate_factors.sh - Script to get marginal and average factor estimates based on formatted data.
├── get_factor_estimates.py - Python code to get emissions factors (see estimate_factors.sh for usage).
├── get_plots.py - Python code to plot emissions factors (see estimate_factors.sh for usage).
├── notebooks - Notebooks with visualizations and summaries of emissions factors.
interventions
├── run_interventions.sh - Script to get plots for intervention effects based on factor estimates.
├── run_intervention.py - Python code to get intervention effects (see run_interventions.sh for usage).
├── plot_intervention.py - Helper functions for plotting intervention effects.
├── monthly_dr.csv - Demand response reduction data (for demand response experiments)
├── notebooks - Notebooks with visualizations and summaries of interventions/power system examples.
si - Folder with notebooks and data to reproduce analyses in the SI.
```

### Acknowledgments

This work was supported by the National Science Foundation Graduate Research Fellowship Program under Grant No. DGE1252522, the Department of Energy Computational Science Graduate Fellowship under Grant No. DE-FG02-97ER25308, and the Center for Climate and Energy Decision Making (CEDM) through a cooperative agreement between Carnegie Mellon University and the National Science Foundation under Grant No. SES-1463492. 

# Licensing

Unless otherwise stated, the source code is copyright Carnegie Mellon University and licensed under the [Apache 2.0 License](./LICENSE).

