import random

def generate_routes(data, params, routes_count, date, k=1):
    """
    Generate random routes based on the input data and parameters.

    Args:
        data (dict): Dictionary containing the input data.
        params (dict): Parameters for generating routes.
        routes_count (int): Number of routes to generate.
        date (datetime): Current date.
        k (int): Parameter for adjusting days weights (default: 1).

    Returns:
        tuple: Generated terminals in route and statistics.
    """

    terminals = data['terminals']
    edge_time = data['edge_time']
    days_left = data.get('days_left', {})

    terminals_in_route = {}

    # Generate greedy routes between terminals with days_left = 0
    zero_terminals = [t for t in terminals if days_left[t] == 0]
    print(len(zero_terminals))
    special_route = 0
    while len(zero_terminals) > 0:
        special_route += 1
        if special_route > params['num_cars']:
            print('Many routes')
        current_terminal = random.choice(zero_terminals)
        zero_terminals.remove(current_terminal)
        terminals_in_route[special_route]=[current_terminal]
        cumm_time = params['maintenance_minutes']
        # Find available terminals that can be visited next based on time constraints
        while len(zero_terminals) > 0:
            # Select the next nearest terminal 
            next_terminal = sorted(zero_terminals, key=lambda t: edge_time[current_terminal,t])[0]
            if cumm_time + edge_time[current_terminal,next_terminal] + params['maintenance_minutes'] <= params['shift_minutes']:
                terminals_in_route[special_route].append(next_terminal)
                cumm_time += edge_time[current_terminal,next_terminal] + params['maintenance_minutes']
                current_terminal = next_terminal
                zero_terminals.remove(current_terminal)
            else:
                break

    # Generate greedy routes for all terminals as starting point
    all_terminals = [t for t in terminals]
    while len(all_terminals) > 0:
        special_route += 1
        current_terminal = all_terminals[0]
        all_terminals.remove(current_terminal)
        terminals_in_route[special_route]=[current_terminal]
        cumm_time = params['maintenance_minutes']
        next_terminals = [t for t in terminals if t != current_terminal]
        # Find available terminals that can be visited next based on time constraints
        while True:
            # Select the next nearest terminal 
            next_terminal = sorted(next_terminals, key=lambda t: edge_time[current_terminal,t])[0]
            if cumm_time + edge_time[current_terminal,next_terminal] + params['maintenance_minutes'] <= params['shift_minutes']:
                terminals_in_route[special_route].append(next_terminal)
                cumm_time += edge_time[current_terminal,next_terminal] + params['maintenance_minutes']
                current_terminal = next_terminal
                next_terminals.remove(current_terminal)
            else:
                break
    

    for r in range(special_route+1,routes_count+special_route+1):
        # Select a candidate terminal randomly based on the days weights
        candidate_terms = [t for t in terminals] 
        current_terminal = random.choices(candidate_terms, k=1)[0]

        # Initialize the terminals in the route for the current route with the current terminal
        terminals_in_route[r]=[current_terminal]
        cumm_time = params['maintenance_minutes']

        while True:
            # Find available terminals that can be visited next based on time constraints
            available_terms = [
                terminal for terminal in terminals if terminal not in terminals_in_route[r] and 
                cumm_time + edge_time[current_terminal,terminal] + params['maintenance_minutes'] <= params['shift_minutes']
            ]
            if not len(available_terms):
                break

            # Select the next terminal randomly based on weighted selection using days weights and edge times
            next_terminal = random.choices(
                available_terms,
                weights=[1 / (edge_time[current_terminal,t]**2) for t in available_terms], k=1)[0]
            
            cumm_time += edge_time[current_terminal,next_terminal] + params['maintenance_minutes']
            terminals_in_route[r].append(next_terminal)
            current_terminal = next_terminal

    data['routes'] = list(range(1,routes_count+special_route))
    data['terminals_in_route'] = terminals_in_route

    return terminals_in_route

