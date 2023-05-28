from pyomo.environ import *
from utils import *
from datetime import timedelta
from math import *


WEIGHTS = {
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
    """
    Create the optimization model.

    Args:
        data (dict): Dictionary containing the input data.
        params (dict): Parameters for the optimization model.
        current_date (datetime): Current date.
        cars_count (int): Number of available cars.

    Returns:
        model: Optimization model.
    """

    terminals = data['terminals']
    start_balance = data['start_balance']
    cash_income = data['cash_income']
    routes = data['routes']
    terminals_in_route = data['terminals_in_route']
    last_visit = data['last_visit']
    days_left = data['days_left']

    model = ConcreteModel()

    # Decision variable: Indicator of route using
    model.route_use = Var(routes, domain=Binary, initialize=0)

    # Implicit variable: Number of visits to each terminal
    model.terminal_visits = {(t):
        sum(model.route_use[r] for r in routes if t in terminals_in_route[r])
        for t in terminals
    }

    # Constraints for minimum and maximum visits to terminals
    cons_min_visits = {}
    cons_max_visits = {}
    for t in terminals:
        if days_left[t] == 0:
            cons_min_visits[t] = (
                model.terminal_visits[t] == 1
            )
        else:
            cons_max_visits[t] = (
                model.terminal_visits[t] <= 1
            )            
    constraints_from_dict(cons_min_visits, model, 'cons_min_visits')    
    constraints_from_dict(cons_max_visits, model, 'cons_max_visits')    

    # Constraint to limit the number of routes per day to the number of available cars
    cons_max_routes = {}
    cons_max_routes['cars_count'] = (
        cars_count >= sum(model.route_use[r] for r in routes)
    )    
    constraints_from_dict(cons_max_routes, model, 'cons_max_routes')    

    # Objective function: maximize the sum of terminal visits weighted by days left
    model.obj = Objective(expr = (
        sum(model.terminal_visits[t] * WEIGHTS[days_left[t]] for t in terminals if days_left[t] > 0)
    ), sense = maximize)

    return model

