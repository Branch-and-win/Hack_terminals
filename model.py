from pyomo.environ import *
from utils import *
from datetime import timedelta
from math import *


Weights = {
	1:20,
	2:13,
	3:12,
	4:11,
	5:10,
	6:9,
	7:8,
	8:7,
	9:6,
	10:5,
	11:4,
	12:3,
	13:2,
	14:1
}

def create_model(data, params, current_date, cars_count):

	## Входные данные

	TERMINALS = data['TERMINALS']
	StartBalance = data['start_balance']
	CashIncome = data['cash_income']
	ROUTES = data['ROUTES']
	TerminalsInRoute = data['terminals_in_route']
	LastVisit = data['last_visit']
	DaysLeft = data['days_left']


	## Оптимизационная модель
	model = ConcreteModel()

	# Индикатор использования маршрута
	model.route_use = Var(ROUTES, domain=Binary, initialize=0)

	# Количество посещений терминала 
	model.terminal_visits = {(t):
		sum(model.route_use[r] for r in ROUTES if t in TerminalsInRoute[r])
		for t in TERMINALS
	}

	consMinVisits = {}
	consMaxVisits = {}
	for t in TERMINALS:
		if DaysLeft[t] == 0:
			consMinVisits[t] = (
				model.terminal_visits[t] == 1
			)
		else:
			consMaxVisits[t] = (
				model.terminal_visits[t] <= 1
			)			
	constraints_from_dict(consMinVisits, model, 'consMinVisits')	
	constraints_from_dict(consMaxVisits, model, 'consMaxVisits')	

	# Количество маршрутов за день меньше количества броневиков
	consMaxRoutes = {}
	consMaxRoutes['cars_count'] = (
		cars_count >= sum(model.route_use[r] for r in ROUTES)
	)	
	constraints_from_dict(consMaxRoutes, model, 'consMaxRoutes')	


	## Целевая функция:

	model.obj = Objective(expr = (
		sum(model.terminal_visits[t] * Weights[DaysLeft[t]] for t in TERMINALS if DaysLeft[t] > 0)
	), sense = maximize)

	return model

