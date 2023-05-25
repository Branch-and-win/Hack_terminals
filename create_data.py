import pandas as pd 
from datetime import timedelta,datetime
from pyomo.environ import *

def create_data(params):

	data = {}

	TERMINALS = pd.read_excel(
		'input/terminal_data_hackathon v4.xlsx',sheet_name='TIDS')['TID'].tolist()
	
	edge_data = pd.read_csv(
		'input/times v4.csv', index_col=['Origin_tid','Destination_tid'])
	data['EDGES'] = list(edge_data.index.values)
	data['EdgeTime'] = edge_data['Total_Time'].to_dict()
	for (t1,t2) in data['EDGES']:
		if data['EdgeTime'][t1,t2] == 0:
			data['EdgeTime'][t1,t2] = 0.1

	income_data = pd.read_excel(
		'input/terminal_data_hackathon v4.xlsx',parse_dates=True,sheet_name='Incomes')

	income_data['Datetime'] = pd.to_datetime(income_data['Date'])
	CashIncome = {}
	for _, row in income_data.iterrows():
		CashIncome[(row['TID'],datetime.fromisoformat(row['Date']))] = row['Income']

	data['cash_income'] = CashIncome

	balance_data = pd.read_excel(
		'input/terminal_data_hackathon v4.xlsx',sheet_name='Start_balance', index_col=[0])
	StartBalance = balance_data['start_balance'].to_dict()
	data['start_balance'] = StartBalance


	DaysLeft = {t: params['max_days'] for t in TERMINALS}
	RunningBalance = {}
	for t in TERMINALS:
		RunningBalance[t] = StartBalance[t]
		if StartBalance[t] > params['max_cash']:
			DaysLeft[t] = 0
		else:
			for d in pd.date_range(start=params['start_date'], periods=params['max_days']).tolist():
				if RunningBalance[t] + CashIncome[t,d] >= params['max_cash']:
					DaysLeft[t] = (d - params['start_date']).days + 1
					break
				else:
					RunningBalance[t] += CashIncome[t,d]

	data['last_visit'] = {t: 
		params['start_date'] + timedelta(days=-1)
		for t in TERMINALS
	}
	data['days_left'] = DaysLeft
	data['TERMINALS'] = TERMINALS

	return data

def update_data(data, model, current_date, params):

	StartBalance = data['start_balance']
	CashIncome = data['cash_income']
	TERMINALS = data['TERMINALS']
	DaysLeft = data['days_left']
	LastVisit = data['last_visit']


	RunningBalance = {}

	for t in TERMINALS:
		if value(model.terminal_visits[t] > 0.5):
			LastVisit[t] = current_date 
			StartBalance[t] = CashIncome[t,current_date] 
		else:
			StartBalance[t] += CashIncome[t,current_date] 
		DaysLeft[t] = params['max_days'] - (current_date - LastVisit[t]).days
		RunningBalance[t] = StartBalance[t]
		if StartBalance[t] > params['max_cash']:
			DaysLeft[t] = 0
		else:
			for d in pd.date_range(start=current_date + timedelta(days=1), periods=params['max_days'] + 1).tolist():
				if RunningBalance[t] + CashIncome[t,d] >= params['max_cash']:
					DaysLeft[t] = min(DaysLeft[t], (d - current_date).days)
					break
				else:
					RunningBalance[t] += CashIncome[t,d]


	data['start_balance'] = StartBalance
	data['days_left'] = DaysLeft
	data['last_visit'] = LastVisit
	
	return data
