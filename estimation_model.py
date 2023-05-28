from pyomo.environ import *
from utils import *
from datetime import timedelta
from math import *


def update_data(data, params, cash_income):
    """
    Update the input data with encashment intervals and special encashment days based on cash income.

    Args:
        data (dict): Dictionary containing the input data.
        params (dict): Parameters for updating the data.
        cash_income (dict): Cash income data.

    Returns:
        None
    """

    intervals = []
    special_days = []

    for t in data['terminals']:
        if start_balance[t] >= params['max_cash']:
            special_days.append((t,params['start_date']))
        intervals.append((t,pd.date_range(start=params['start_date'], end=params['end_date']).tolist()))
        for d1 in data['days']:
            if cash_income[t,d1] > params['max_cash']:
                    special_days.append((t,d1+timedelta(days=1)))
                    break
            cumm_sum = cash_income[t,d1]
            for d2 in [d for d in data['days'] if d > d1 and d+timedelta(days=1) in data['days']]:
                if cumm_sum + cash_income[t,d2] > params['max_cash']:
                    intervals.append((t,pd.date_range(start=d1, end=d2+timedelta(days=1)).tolist()))
                    break
                else:
                    cumm_sum += cash_income[t,d2]

def create_model(data, params):
    """
    Create an optimization model to estimate the number of cars needed.

    Args:
        data (dict): Dictionary containing the input data.
        params (dict): Parameters for the optimization model.

    Returns:
        model: Optimization model.
    """

    days = data['days']
    terminals = data['terminals']
    start_balance = data['start_balance']
    cash_income = data['cash_income']
    routes = data['routes']
    terminals_in_use = data['terminals_in_route']
    intervals = data['intervals']
    special_days = data['special_days']

    model = ConcreteModel()

    # Decision variable: Indicator for route usage in a specific day
    model.route_use = Var(routes, days, domain=Binary, initialize=0)

    # Decision variable: Number of cars in the park
    model.cars_count = Var(domain=NonNegativeReals, initialize=0)

    # Implicit variable: Number of visits to a terminal in a specific day
    model.terminal_visits = {(t,d):
        sum(model.route_use[r,d] for r in routes if t in terminals_in_use[r])
        for t in terminals
        for d in days
    }

    # Constraint: Terminal must be visited once on special days
    cons_special_days = {}
    for t,date in special_days:
        cons_special_days[t,date] = (
            model.terminal_visits[t,date] == 1
        )
    constraints_from_dict(cons_special_days, model, 'cons_special_days')

    # Constraint: At least one visit to a terminal within each interval
    cons_intervals = {}
    i = 0
    for t,dates_list in intervals:
        cons_intervals[t,i] = (
            sum(model.terminal_visits[t,d] for d in dates_list) >= 1
        )
        i += 1
    constraints_from_dict(cons_intervals, model, 'cons_intervals')

    # Constraint: Number of routes in a day must be less than or equal to the number of cars
    cons_max_routes = {}
    for d in days:
        cons_max_routes[d] = (
            model.cars_count  >=
            sum(model.route_use[r,d] for r in routes)
        )    
    constraints_from_dict(cons_max_routes, model, 'cons_max_routes')    
    
    # Objective function: Minimize the number of cars
    model.obj = Objective(expr = (
         model.cars_count
    ), sense = minimize)

    return model
