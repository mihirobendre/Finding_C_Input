
from run_rothc import run_rothc

months_df, years_df = run_rothc(
    starting_soil_carbon=40,
    total_years=30,
    carbon_input_project=5.0,
    start_year=2030
)

print(years_df)
