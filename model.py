from pyomo.environ import *
from utils import *
from datetime import timedelta
from math import *


def create_model(data, params, cars_count):
    """
    Create the optimization model.

    Args:
        data (dict): Dictionary containing the input data.
        params (dict): Parameters for the optimization model.
        cars_count (int): Number of available cars.

    Returns:
        model: Optimization model.
    """

    terminals = data['terminals']
    routes = data['routes']
    terminals_in_route = data['terminals_in_route']
    days_left = data['days_left']
    
    # Countes the number of terminals in certain days_left group (1..14)
    group_count = {i: 0 for i in range(1, params['max_days']+1)}
    for t in terminals:
        if days_left[t] > 0:
            group_count[days_left[t]] += 1

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
        # Mandatory terminals
        if days_left[t] == 0:
            cons_min_visits[t] = (
                model.terminal_visits[t] >= 1
            )
        else:
        # Voluntary terminals
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

    # Objective function: maximize the sum of terminal visits weighted by (group_count[days_left[t]] / days_left[t])
    model.obj = Objective(expr = (
        sum(model.terminal_visits[t] * (group_count[days_left[t]] / days_left[t]) for t in terminals if days_left[t] > 0)
    ), sense = maximize)

    return model

