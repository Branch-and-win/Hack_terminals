import pandas as pd 
from pyomo.environ import *

def create_output(model, data, date, params):


	TERMINALS = data['TERMINALS']
	ROUTES = data['ROUTES']
	TerminalsInRoute = data['terminals_in_route']
	StartBalance = data['start_balance']
	CashIncome = data['cash_income']
	TERMINALS = data['TERMINALS']
	DaysLeft = data['days_left']
	LastVisit = data['last_visit']


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
					CashIncome[t,date],
					value(model.terminal_visits[t]),
					LastVisit[t],
					DaysLeft[t]
					]
					for t in TERMINALS
					]

	result_tmp_2 = pd.DataFrame(result_list_2, columns=[
							'TID', 'Date', 'Start Balance', 'Income', 'TID Visits', 'Visit Date', 'Days Left'])

	#result_tmp_2.to_excel('terminal_visits.xlsx',index=False)
	
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
	return result_tmp_1, result_tmp_2