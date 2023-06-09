import random

def generate_routes(data, params):
    """
    Generate random routes based on the input data and parameters.

    Args:
        data (dict): Dictionary containing the input data.
        params (dict): Parameters for generating routes.

    Returns:
        tuple: Generated terminals in route.
    """

    terminals = data['terminals']
    edge_time = data['edge_time']
    days_left = data.get('days_left', {})
    terminals_in_route = data['terminals_in_fixed_route'].copy()


    # Generate greedy routes between terminals with days_left = 0
    zero_terminals = [t for t in terminals if days_left[t] == 0]
    print(len(zero_terminals))
    special_route_id = len(terminals_in_route)
    while len(zero_terminals) > 0:
        special_route_id += 1
        current_terminal = random.choice(zero_terminals)
        zero_terminals.remove(current_terminal)
        terminals_in_route[special_route_id]=[current_terminal]
        cumm_time = params['maintenance_minutes']
        # Find available terminals that can be visited next based on time constraints
        while len(zero_terminals) > 0:
            # Select the next nearest terminal 
            next_terminal = sorted(zero_terminals, key=lambda t: edge_time[current_terminal,t])[0]
            if cumm_time + edge_time[current_terminal,next_terminal] + params['maintenance_minutes'] <= params['shift_minutes']:
                terminals_in_route[special_route_id].append(next_terminal)
                cumm_time += edge_time[current_terminal,next_terminal] + params['maintenance_minutes']
                current_terminal = next_terminal
                zero_terminals.remove(current_terminal)
            else:
                break

    print(special_route_id - len(terminals))

    data['routes'] = list(range(1, special_route_id+1))
    data['terminals_in_route'] = terminals_in_route

    return terminals_in_route

