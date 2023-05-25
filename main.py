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
params['shift_minutes'] = 720
params['max_days'] = 14
params['start_date'] = datetime.datetime(2022, 9, 1)
#params['end_date'] = datetime.datetime(2022, 11, 30)
params['end_date'] = datetime.datetime(2022, 9, 28)

result_1 = []
result_2 = []

data = create_data(params)

for d in pd.date_range(start=params['start_date'], end=params['end_date']).tolist():

	print('NEW DAY')
	print(d)

	generate_routes(data, params, 2000)
	model = create_model(data, params, d, 11)

	Solver = SolverFactory('appsi_highs')
	#Solver.options['TimeLimit'] = 60
	Solver.options['time_limit'] = 100
	#Solver.options['MIPGap'] = 0.01
	Solver.options['mip_rel_gap'] = 0.01	
	#Solver.options['Threads'] = 12
	#Solver.options['Method'] = 2
	#Solver.options['lpmethod'] = 'ipm'
	#Solver.options['Cuts'] = 0
	#Solver.options['cutPasses'] = 0
	#Solver.options['NoRelHeurTime'] = 60
	SolverResults = Solver.solve(model, tee=True)   
	result_tmp_1, result_tmp_2 = create_output(model, data, d, params)
	result_1.append(result_tmp_1)
	result_2.append(result_tmp_2)
	data = update_data(data, model, d, params)
#create_output(model, data)


result_1 = pd.concat(result_1)
result_2 = pd.concat(result_2)

result_1.to_excel('output/out_routes.xlsx', index=False)
result_2.to_excel('output/terminals.xlsx', index=False)
