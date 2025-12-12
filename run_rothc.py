from RothC_src import *

import pandas as pd
import numpy as np
import os


def run_rothc(
    starting_soil_carbon=31.84,
    total_years=40,
    start_year=2025,
    clay=18,
    depth=30,
    temp=None,
    rain=None,
    evap=None,
    pc=None,
    dpm_rpm=1.44,
    carbon_input_project=4.0,          # annual input
    farmyard_manure_project=0.1 * 0.5535,
    carbon_input_baseline=2.5,         # annual input
    farmyard_manure_baseline=0.0,      # annual input
    month_output_path="month_results.xlsx",
    year_output_path="year_results.xlsx",
    write_files=True
):
    """
    Run RothC with user-defined parameters and return monthly and yearly outputs
    as pandas DataFrames. Optionally write them to Excel files.
    """

    # Default climate / management sequences if not provided
    if temp is None:
        temp = [27.7, 30.3, 31.8, 30.9, 29.3, 27.6, 26.6, 26.0, 26.4, 28.0, 28.8, 27.8]
    if rain is None:
        rain = [5.0, 10.9, 20.9, 86.4, 130.1, 141.8, 139.7, 241.0, 198.1, 82.9, 5.2, 0.3]
    if evap is None:
        evap = [193.33, 200.0, 230.67, 225.33, 220.0, 192.0, 176.0, 164.0,
                162.67, 190.67, 192.0, 192.0]
    if pc is None:
        pc = [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0]

    # Ensure working directory is the script directory (as in original code)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Set initial pool values
    soc = starting_soil_carbon
    SOC = [soc]

    rpm = (0.1847 * soc + 0.1555) * (clay + 1.2750) ** (-0.1158)
    RPM = [rpm]
    DPM = [dpm_rpm * rpm]
    HUM = [(0.7148 * soc + 0.5069) * (clay + 0.3421) ** 0.0184]
    BIO = [(0.0140 * soc + 0.0075) * (clay + 8.8473) ** 0.0567]
    iom = 0.049 * soc ** 1.139
    IOM = [iom]

    DPM_Rage = [0.0]
    RPM_Rage = [0.0]
    BIO_Rage = [0.0]
    HUM_Rage = [0.0]
    IOM_Rage = [50000.0]

    # Initial soil water content (deficit)
    SWC = [0.0]
    TOC1 = 0.0

    # Number of monthly time steps (original: 12 + total_years * 12)
    nsteps = 12 + total_years * 12

    # Run RothC to equilibrium with baseline inputs
    k = -1
    j = -1

    SOC[0] = DPM[0] + RPM[0] + BIO[0] + HUM[0] + IOM[0]
    timeFact = 12
    test = 100.0

    while test > 1e-6:
        k += 1
        j += 1

        if k == timeFact:
            k = 0

        TEMP = temp[k]
        RAIN = rain[k]
        PEVAP = evap[k] / 0.75
        PC = pc[k]
        DPM_RPM = dpm_rpm

        C_Inp = carbon_input_baseline / 12.0
        FYM_Inp = farmyard_manure_baseline / 12.0
        modernC = 100.0 / 100.0

        Total_Rage = [0.0]

        RothC(
            timeFact, DPM, RPM, BIO, HUM, IOM, SOC,
            DPM_Rage, RPM_Rage, BIO_Rage, HUM_Rage, Total_Rage,
            modernC, clay, depth, TEMP, RAIN, PEVAP, PC,
            DPM_RPM, C_Inp, FYM_Inp, SWC
        )

        # Each year, check convergence of the active pools
        if np.mod(k + 1, timeFact) == 0:
            TOC0 = TOC1
            TOC1 = DPM[0] + RPM[0] + BIO[0] + HUM[0]
            test = abs(TOC1 - TOC0)

    # After equilibrium, start project run
    Total_Delta = (np.exp(-Total_Rage[0] / 8035.0) - 1.0) * 1000.0
    year_list = [[1, j + 1, DPM[0], RPM[0], BIO[0], HUM[0], IOM[0], SOC[0], Total_Delta]]
    month_list = []

    k = 0
    year = start_year
    month = 1

    for i in range(timeFact, nsteps):
        TEMP = temp[k]
        RAIN = rain[k]
        PEVAP = evap[k] / 0.75
        PC = pc[k]
        DPM_RPM = dpm_rpm

        C_Inp = carbon_input_project / 12.0
        FYM_Inp = farmyard_manure_project / 12.0
        modernC = 100.0 / 100.0

        RothC(
            timeFact, DPM, RPM, BIO, HUM, IOM, SOC,
            DPM_Rage, RPM_Rage, BIO_Rage, HUM_Rage, Total_Rage,
            modernC, clay, depth, TEMP, RAIN, PEVAP, PC,
            DPM_RPM, C_Inp, FYM_Inp, SWC
        )

        Total_Delta = (np.exp(-Total_Rage[0] / 8035.0) - 1.0) * 1000.0

        month_list.insert(
            i - timeFact,
            [year, month, DPM[0], RPM[0], BIO[0], HUM[0], IOM[0], SOC[0], Total_Delta]
        )

        if month == timeFact:
            timeFact_index = int(i / timeFact)
            year_list.insert(
                timeFact_index,
                [year, month, DPM[0], RPM[0], BIO[0], HUM[0], IOM[0], SOC[0], Total_Delta]
            )

        k += 1
        month += 1

        if k == timeFact:
            k = 0
            month = 1
            year += 1

    output_years_project = pd.DataFrame(
        year_list,
        columns=[
            "Year", "Month",
            "DPM_t_C_ha", "RPM_t_C_ha", "BIO_t_C_ha",
            "HUM_t_C_ha", "IOM_t_C_ha", "SOC_t_C_ha", "deltaC"
        ]
    )

    output_months_project = pd.DataFrame(
        month_list,
        columns=[
            "Year", "Month",
            "DPM_t_C_ha", "RPM_t_C_ha", "BIO_t_C_ha",
            "HUM_t_C_ha", "IOM_t_C_ha", "SOC_t_C_ha", "deltaC"
        ]
    )

    if write_files:
        with pd.ExcelWriter(month_output_path) as writer:
            output_months_project.to_excel(writer, sheet_name="Project", index=False)
        with pd.ExcelWriter(year_output_path) as writer:
            output_years_project.to_excel(writer, sheet_name="Project", index=False)

    # Return dataframes for further use
    return output_months_project, output_years_project

