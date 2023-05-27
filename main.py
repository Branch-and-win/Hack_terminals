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
#params['end_date'] = datetime.datetime(2022, 11, 30)
params['end_date'] = datetime(2022, 9, 15)
params['num_cars'] = 10

result_1 = []
result_2 = []
result_3 = []

data = create_data(params, forecast_mode=True)
routes_count = 2000
k = 1

for d in pd.date_range(start=params['start_date'], end=params['end_date']).tolist():

	print('NEW DAY')
	print(d)


	if d.day >= 11 and d.day <= 15:
		routes_count = 5000

		#k = 0.7
	else:
		routes_count = 3000
		k = 1

	generate_routes(data, params, routes_count, d, k)
	model = create_model(data, params, d, params['num_cars'])

	#Solver = SolverFactory('appsi_highs')
	Solver = SolverFactory('gurobi')
	Solver.options['TimeLimit'] = 600
	#Solver.options['time_limit'] = 1800
	Solver.options['MIPGap'] = 0.001
	#Solver.options['mip_rel_gap'] = 0.0001	
	Solver.options['Threads'] = 12
	#Solver.options['Method'] = 2
	#Solver.options['lpmethod'] = 'ipm'
	#Solver.options['Cuts'] = 0
	#Solver.options['cutPasses'] = 0
	#Solver.options['NoRelHeurTime'] = 60
	SolverResults = Solver.solve(model, tee=True)   
	if (SolverResults.solver.termination_condition == TerminationCondition.infeasible or 
		SolverResults.solver.termination_condition == TerminationCondition.noSolution):
		break 
	result_tmp_1, result_tmp_2, result_tmp_3 = create_output(model, data, d, params)
	result_1.append(result_tmp_1)
	result_2.append(result_tmp_2)
	result_3.append(result_tmp_3)
	data = update_data(data, model, d, params, forecast_mode=True)
#create_output(model, data)


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
