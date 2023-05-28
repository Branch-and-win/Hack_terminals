from pyomo.environ import *
from create_data import *
from routes_generation import *
import datetime
import pandas as pd
from output import *
from model import *

params = {}
params['balance_percent'] = 0.02
params['max_days'] = 14
params['maintenance_percent'] = 0.0001
params['car_cost'] = 20000
params['max_cash'] = 1000000
params['maintenance_minutes'] = 10
params['max_days'] = 14
params['start_hour'] = 8
params['end_hour'] = 20
params['shift_minutes'] = (params['end_hour'] - params['start_hour']) * 60
params['start_date'] = datetime(2022, 9, 1)
params['end_date'] = datetime(2022, 11, 30)
params['num_cars'] = 8

result_1 = []
result_2 = []
result_3 = []

data = create_data(params, forecast_mode=True)
routes_count = 10000
k = 1

for d in pd.date_range(start=params['start_date'], end=params['end_date']).tolist():

	print('NEW DAY')
	print(d)


	generate_routes(data, params, routes_count, d, k)
	model = create_model(data, params, d, params['num_cars'])

	Solver = SolverFactory('appsi_highs')
	Solver.options['time_limit'] = 300
	Solver.options['mip_rel_gap'] = 0.01	
	SolverResults = Solver.solve(model, tee=True)   
	if (SolverResults.solver.termination_condition == TerminationCondition.infeasible or 
		SolverResults.solver.termination_condition == TerminationCondition.noSolution):
		break 
	result_tmp_1, result_tmp_2, result_tmp_3 = create_output(model, data, d, params)
	result_1.append(result_tmp_1)
	result_2.append(result_tmp_2)
	result_3.append(result_tmp_3)
	data = update_data(data, model, d, params, forecast_mode=True)



result_1 = pd.concat(result_1)
result_2 = pd.concat(result_2)
result_3 = pd.concat(result_3)

result_4 = pd.pivot_table(result_2, values='Funding Costs', index=['TID'], columns=['Date'])
result_5 = pd.pivot_table(result_2, values='Maintenance Costs', index=['TID'], columns=['Date'])
result_6 = pd.pivot_table(result_2, values='End Balance', index=['TID'], columns=['Date'])



result_1.to_excel('out_routes.xlsx', index=False)
result_2.to_excel('terminals.xlsx', index=False)
result_3.to_excel('routes.xlsx', index=False)
result_4.to_excel('funding.xlsx')
result_5.to_excel('maintenance.xlsx')
result_6.to_excel('end_balance.xlsx')

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
result_7.to_excel('summary.xlsx', index=False)
