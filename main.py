from pyomo.environ import *
import yaml
import logging
import structlog

logger = structlog.get_logger('main')

from create_data import *
from routes_generation import *
import datetime
import pandas as pd
from output import *
from model import *

def main():
    # Load parameters from YAML file
    with open('./params.yml', 'r') as stream:
        params = yaml.safe_load(stream)
    params['shift_minutes'] = (params['end_hour'] - params['start_hour']) * 60
    params['start_date'] = datetime(params['start_date'].year, params['start_date'].month, params['start_date'].day)
    params['end_date'] = datetime(params['end_date'].year, params['end_date'].month, params['end_date'].day)

    result_1 = []
    result_2 = []
    result_3 = []

    # Create initial data
    data = create_data(params, forecast_mode=True)

    for d in pd.date_range(start=params['start_date'], end=params['end_date']).tolist():

        logger.info(f'Start calc new day {d}')

        # Generate routes for the current day
        generate_routes(data, params)

        # Create optimization model for the current day
        model = create_model(data, params, params['num_cars'])

        # Set solver params and solve model
        Solver = SolverFactory('appsi_highs')
        Solver.options['time_limit'] = 300
        Solver.options['mip_rel_gap'] = 0.01    
        SolverResults = Solver.solve(model, tee=True)  

        # Check solver termination condition
        if (SolverResults.solver.termination_condition == TerminationCondition.infeasible or 
            SolverResults.solver.termination_condition == TerminationCondition.noSolution):
            break 
        
        # Create one day optimization results
        result_tmp_1, result_tmp_2, result_tmp_3 = create_output(model, data, d, params)
        
        # Append results for the current day to the overall results
        result_1.append(result_tmp_1)
        result_2.append(result_tmp_2)
        result_3.append(result_tmp_3)

        # Update data for the next day (if applicable)
        data = update_data(data, model, d, params, forecast_mode=True)


    # Create result tables
    result_1 = pd.concat(result_1)
    result_2 = pd.concat(result_2)
    result_3 = pd.concat(result_3)

    result_4 = pd.pivot_table(result_2, values='Funding Costs', index=['TID'], columns=['Date'])
    result_5 = pd.pivot_table(result_2, values='Maintenance Costs', index=['TID'], columns=['Date'])
    result_6 = pd.pivot_table(result_2, values='End Balance', index=['TID'], columns=['Date'])

    # Export result tables to Excel files
    result_1.to_excel('./output/лог_Маршруты.xlsx', index=False)
    result_2.to_excel('./output/лог_Терминалы.xlsx', index=False)
    result_3.to_excel('./output/Маршруты.xlsx', index=False)
    result_4.to_excel('./output/Стоимость фондирования.xlsx')
    result_5.to_excel('./output/Стоимость инкассации.xlsx')
    result_6.to_excel('./output/Остатки на конец дня.xlsx')

    # Create summary table
    result_7_p1 = pd.DataFrame(result_4.sum()).transpose()
    result_7_p1.insert(0, "статья расходов","фондирование",True)
    result_7_p2 = pd.DataFrame(result_5.sum()).transpose()
    result_7_p2.insert(0, "статья расходов","инкассация",True)
    result_7_p3 = pd.DataFrame([[params['car_cost']*params['num_cars']]*len(result_4.columns)], columns = result_4.columns)
    result_7_p3.insert(0, "статья расходов","стоимость броневиков",True)
    result_7_p12 = result_7_p1.append(result_7_p2)
    result_7_p12 = result_7_p12.append(result_7_p3)
    result_7_p31 = pd.DataFrame(result_7_p12.sum()).transpose()
    result_7_p31['статья расходов'] = 'итого'
    result_7 = result_7_p12.append(result_7_p31)
    result_7.to_excel('./output/Итог.xlsx', index=False)

if __name__ == '__main__':
    main()
