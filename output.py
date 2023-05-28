import pandas as pd 
from pyomo.environ import *
from datetime import timedelta,datetime

def create_output(model, data, date, params):
    """
    Create the output data based on the optimization model results.

    Args:
        model (ConcreteModel): Optimization model.
        data (dict): Dictionary containing the input data.
        date (datetime): Current date.
        params (dict): Parameters for the optimization model.

    Returns:
        tuple: Resulting dataframes for routes, terminals, and route details.
    """

    terminals = data['terminals']
    routes = data['routes']
    terminals_in_route = data['terminals_in_route']
    start_balance = data['start_balance']
    cash_income = data['cash_income']
    terminals = data['terminals']
    days_left = data['days_left']
    last_visit = data['last_visit']
    edge_time = data['edge_time']
    forecast_income = data['forecast_income']

    # Create dataframe for routes
    result_list_1= [[r,date,
                    len(terminals_in_route[r]),
                    terminals_in_route[r]
                    ]
                    for r in routes
                    if value(model.route_use[r] > 0.5)
                    ]
    result_tmp_1 = pd.DataFrame(result_list_1, columns=[
                            'Route ID', 'Date','Length', 'Terminals list'])

    # Create dataframe for terminals
    result_list_2= [[t,date,
                    start_balance[t],
                    (0 if value(model.terminal_visits[t]) > 0.5 else start_balance[t]),
                    ((0 if value(model.terminal_visits[t]) > 0.5 else start_balance[t]) * params['balance_percent'] /365), 
                    (max(100, start_balance[t] * params['maintenance_percent']) if value(model.terminal_visits[t]) > 0.5 else 0),
                    cash_income[t,date],
                    forecast_income[t][(date + timedelta(days=-1)).strftime("%Y-%m-%d %H:%M:%S")][date.strftime("%Y-%m-%d %H:%M:%S")],
                    value(model.terminal_visits[t]),
                    last_visit[t],
                    days_left[t]
                    ]
                    for t in terminals
                    ]
    result_tmp_2 = pd.DataFrame(result_list_2, columns=[
                            'TID', 'Date', 'Start Balance', 'End Balance','Funding Costs','Maintenance Costs','Income',
                            'Forecast Income','TID Visits', 'Visit Date', 'Days Left'])

    # Create dataframe for route details
    result_routes = []
    i = 1
    for r in routes:
        if value(model.route_use[r]) > 0.5:
            current_time = datetime(date.year, date.month, date.day, params['start_hour'],0)
            last_t = 0
            for t in terminals_in_route[r]:
                if last_t != 0:
                    current_time += timedelta(minutes=params['maintenance_minutes'] + edge_time[last_t,t])
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
        
    return result_tmp_1, result_tmp_2, result_tmp_3