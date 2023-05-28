import pandas as pd 
from datetime import timedelta,datetime
from pyomo.environ import *
import pickle5 as pickle

def create_data(params, forecast_mode):
    """
    Create initial data for the optimization model.

    Args:
        params (dict): Parameters for the optimization model.
        forecast_mode (bool): Flag indicating whether to use forecasted income or actual income.

    Returns:
        dict: Dictionary containing initial data.
    """

    data = {}

    # Load terminal data
    terminals = pd.read_excel(
        './input/terminal_data_hackathon v4.xlsx',sheet_name='TIDS')['TID'].tolist()
    
    # Load edge data
    edge_data = pd.read_csv(
        './input/times v4.csv', index_col=['Origin_tid','Destination_tid'])
    data['edges'] = list(edge_data.index.values)
    data['edge_time'] = edge_data['Total_Time'].to_dict()

    # Set minimum edge time to avoid zero values
    for (t1,t2) in data['edges']:
        if data['edge_time'][t1,t2] == 0:
            data['edge_time'][t1,t2] = 0.1

    # Load income data
    income_data = pd.read_excel(
		'./input/terminal_data_hackathon v4.xlsx',sheet_name='Incomes')
    income_data = pd.melt(income_data, id_vars=['TID','остаток на 31.08.2022 (входящий)'], var_name='Datetime', value_name='Income')
    income_data = income_data.set_index(['TID','Datetime'])
    cash_income_unformatted = income_data['Income'].to_dict()

    cash_income = {}
    for k,v in cash_income_unformatted.items():
        cash_income[k[0],datetime.strptime(k[1], '%Y-%m-%d %H:%M:%S')] = v
    data['cash_income'] = cash_income

    # Load start balance data
    balance_data = pd.read_excel(
        './input/terminal_data_hackathon v4.xlsx',sheet_name='Start_balance', index_col=[0])
    start_balance = balance_data['start_balance'].to_dict()
    data['start_balance'] = start_balance

    # Load forecasted income data
    with open('./input/prognosis_full.pickle', 'rb') as fp:
        forecast_income = pickle.load(fp)
    data['forecast_income'] = forecast_income

    # Calculate days left based on cash balance
    days_left = {t: params['max_days'] for t in terminals}
    running_balance = {}
    for t in terminals:
        running_balance[t] = start_balance[t]
        if start_balance[t] > params['max_cash']:
            days_left[t] = 0
        else:
            for d in pd.date_range(start=params['start_date'], periods=params['max_days']).tolist():
                if forecast_mode:
                    if running_balance[t] + forecast_income[t][(params['start_date']+ timedelta(days=-1)).strftime("%Y-%m-%d %H:%M:%S")][d.strftime("%Y-%m-%d %H:%M:%S")] >= params['max_cash']:
                        days_left[t] = (d - params['start_date']).days + 1
                        break
                    else:
                        running_balance[t] += forecast_income[t][(params['start_date']+ timedelta(days=-1)).strftime("%Y-%m-%d %H:%M:%S")][d.strftime("%Y-%m-%d %H:%M:%S")]    
                else:                
                    if running_balance[t] + cash_income[t,d] >= params['max_cash']:
                        days_left[t] = (d - params['start_date']).days + 1
                        break
                    else:
                        running_balance[t] += cash_income[t,d]

    data['last_visit'] = {t: 
        params['start_date'] + timedelta(days=-1)
        for t in terminals
    }
    data['days_left'] = days_left
    data['terminals'] = terminals

    return data

def update_data(data, model, current_date, params, forecast_mode):
    """
    Update data for the next day based on the optimization model results.

    Args:
        data (dict): Dictionary containing the current data.
        model: Optimization model object.
        current_date (datetime): Current date.
        params (dict): Parameters for the optimization model.
        forecast_mode (bool): Flag indicating whether to use forecasted income or actual income.

    Returns:
        dict: Updated dictionary containing data for the next day.
    """

    start_balance = data['start_balance']
    cash_income = data['cash_income']
    terminals = data['terminals']
    days_left = data['days_left']
    last_visit = data['last_visit']
    forecast_income = data['forecast_income']

    # Calculate days left based on cash balance and prev days_left
    running_balance = {}
    for t in terminals:
        if value(model.terminal_visits[t] > 0.5):
            last_visit[t] = current_date 
            start_balance[t] = cash_income[t,current_date] 
        else:
            start_balance[t] += cash_income[t,current_date] 
        days_left[t] = params['max_days'] - (current_date - last_visit[t]).days
        running_balance[t] = start_balance[t]
        if start_balance[t] > params['max_cash']:
            days_left[t] = 0
        else:
            for d in pd.date_range(start=current_date + timedelta(days=1), periods=params['max_days'] + 1).tolist():
                if forecast_mode:
                    if running_balance[t] + forecast_income[t][(current_date).strftime("%Y-%m-%d %H:%M:%S")][d.strftime("%Y-%m-%d %H:%M:%S")] >= params['max_cash']:
                        days_left[t] = min(days_left[t], (d - current_date).days)
                        break
                    else:
                        running_balance[t] += forecast_income[t][(current_date).strftime("%Y-%m-%d %H:%M:%S")][d.strftime("%Y-%m-%d %H:%M:%S")]
                else:
                    if running_balance[t] + cash_income[t,d] >= params['max_cash']:
                        days_left[t] = min(days_left[t], (d - current_date).days)
                        break
                    else:
                        running_balance[t] += cash_income[t,d]

    data['start_balance'] = start_balance
    data['days_left'] = days_left
    data['last_visit'] = last_visit
    
    return data
