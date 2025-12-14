
from run_rothc import run_rothc
import pandas as pd
import numpy as np

'''
starting_c_in = 2

months_df, years_df = run_rothc(
	starting_soil_carbon=31.84,
	total_years=0,
	carbon_input_project = starting_c_in,
	start_year=2030
)

baseline_soc = years_df.at[0,'SOC_t_C_ha']
'''


def solve_carbon_input(
	starting_soil_carbon=31.84,
	starting_fym = 0.0,
	total_years=0,
	start_year=2025,
	tol=1e-3,
	max_iter=50,
	c_min=0.0,
	c_max=20.0
):
	"""
	Find carbon_input_project such that baseline_soc ≈ starting_soil_carbon.
	Returns (carbon_input_project, baseline_soc, n_iter).
	"""

	def soc_for_input(c_in):
		months_df, years_df = run_rothc(
			starting_soil_carbon=starting_soil_carbon,
			farmyard_manure_baseline = starting_fym,
			total_years=total_years,
			carbon_input_baseline=c_in,
			start_year=start_year,
			write_files=False  # optional: avoid writing Excel each time
		)
		return years_df.at[0, "SOC_t_C_ha"]

	# Evaluate at bounds
	soc_min = soc_for_input(c_min)
	
	soc_max = soc_for_input(c_max)
	

	# If monotonic, check that root is bracketed
	# Adjust logic if model behaves differently
	if (soc_min - starting_soil_carbon) * (soc_max - starting_soil_carbon) > 0:
		raise ValueError(
			"Baseline SOC at bounds does not bracket the target; "
			"adjust c_min and c_max."
		)

	for n in range(max_iter):
		c_mid = 0.5 * (c_min + c_max)
		soc_mid = soc_for_input(c_mid)
		diff = soc_mid - starting_soil_carbon

		if abs(diff) <= tol:
			return c_mid, soc_mid, n + 1

		# Decide which half to keep (assuming SOC increases with C input)
		if (soc_min - starting_soil_carbon) * diff < 0:
			c_max = c_mid
			soc_max = soc_mid
		else:
			c_min = c_mid
			soc_min = soc_mid

	# If max_iter reached, return best estimate
	return c_mid, soc_mid, max_iter









target_c, baseline_soc, iters = solve_carbon_input(
	starting_soil_carbon=131.6373,
	starting_fym = 0.5,
	total_years=0,
	start_year=2030,
	tol=1e-2,
	c_min=0.0,
	c_max=100.0
)

print("Solved carbon_input_baseline:", target_c)
print("Resulting baseline_soc:", baseline_soc)
print("Iterations:", iters)

