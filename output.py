import pandas as pd 
from pyomo.environ import *
from datetime import timedelta,datetime

def create_output(model, data, date, params):


	TERMINALS = data['TERMINALS']
	ROUTES = data['ROUTES']
	TerminalsInRoute = data['terminals_in_route']
	StartBalance = data['start_balance']
	CashIncome = data['cash_income']
	TERMINALS = data['TERMINALS']
	DaysLeft = data['days_left']
	LastVisit = data['last_visit']
	EdgeTime = data['EdgeTime']
	forecast_income = data['forecast_income']


	result_list_1= [[r,date,
					len(TerminalsInRoute[r]),
					TerminalsInRoute[r]
					]
					for r in ROUTES
					if value(model.route_use[r] > 0.5)
					]

	result_tmp_1 = pd.DataFrame(result_list_1, columns=[
							'Route ID', 'Date','Length', 'Terminals list'])
	
	#result_tmp_1.to_excel('out_routes.xlsx',index=False)

	result_list_2= [[t,date,
					StartBalance[t],
					(0 if value(model.terminal_visits[t]) > 0.5 else StartBalance[t]),
					((0 if value(model.terminal_visits[t]) > 0.5 else StartBalance[t]) * params['balance_percent'] /365), 
					(max(100, StartBalance[t] * params['maintenance_percent']) if value(model.terminal_visits[t]) > 0.5 else 0),
					CashIncome[t,date],
					forecast_income[t][(date + timedelta(days=-1)).strftime("%Y-%m-%d %H:%M:%S")][date.strftime("%Y-%m-%d %H:%M:%S")],
					value(model.terminal_visits[t]),
					LastVisit[t],
					DaysLeft[t]
					]
					for t in TERMINALS
					]

	result_tmp_2 = pd.DataFrame(result_list_2, columns=[
							'TID', 'Date', 'Start Balance', 'End Balance','Funding Costs','Maintenance Costs','Income','Forecast Income','TID Visits', 'Visit Date', 'Days Left'])

	#result_tmp_2.to_excel('terminal_visits.xlsx',index=False)


	result_routes = []
	i = 1
	for r in ROUTES:
		if value(model.route_use[r]) > 0.5:
			current_time = datetime(date.year, date.month, date.day, params['start_hour'],0)
			last_t = 0
			for t in TerminalsInRoute[r]:
				if last_t != 0:
					current_time += timedelta(minutes=params['maintenance_minutes'] + EdgeTime[last_t,t])
				result_routes.append(
					{
						'Car num': i,
						'TID': t,
						'Arrive time': current_time,
						'Departure time': current_time + timedelta(minutes=params['maintenance_minutes'])
					}
				)
				last_t = t
			i += 1
	result_tmp_3 = pd.DataFrame(result_routes)
		

	
	'''
	result_list_2= [[t,d,
					value(model.terminal_balance[t,d]),
					value(model.terminal_visits[t,d])
					]
					for t in TERMINALS
					for d in DAYS
					]

	result_tmp_2 = pd.DataFrame(result_list_2, columns=[
							'TID', 'Date', 'TID Balance', 'TID Visits'])
	
	result_tmp_2.to_excel('terminals.xlsx',index=False)
	'''
	return result_tmp_1, result_tmp_2, result_tmp_3