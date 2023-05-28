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
    balances = data['start_balance']
    days_left = data.get('days_left', {})

    # Calculate days weights based on remaining days and parameter k
    days_weights = {t: 1/(2 + 1) **(k+0.5) if ((days_left[t] == 15 - date.day) and date.month == 9) else 1/(days_left[t] + 1) **(k+0.5) for t in days_left}
    
    terminals_in_route = {}
    # Filter terminals
    terminals = [t for t in terminals if (days_left[t] <= 4) or ((days_left[t] == 15 - date.day) and date.month == 9)]
    stats = {t:0 for t in terminals}

    for r in range(routes_count):
        # Select a candidate terminal randomly based on the days weights
        candidate_terms = [t for t in terminals] 
        candidate_terms = candidate_terms if len(candidate_terms) else terminals
        current_terminal = random.choices(candidate_terms, weights=[days_weights[t] for t in candidate_terms], k=1)[0]

        # Update statistics by incrementing the count for the selected terminal
        stats[current_terminal] += 1

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
                weights=[days_weights[t] / (edge_time[current_terminal,t]**2) for t in available_terms], k=1)[0]

            # Update statistics by incrementing the count for the selected terminal
            stats[next_terminal] += 1
            
            cumm_time += edge_time[current_terminal,next_terminal] + params['maintenance_minutes']
            terminals_in_route[r].append(next_terminal)
            current_terminal = next_terminal

    data['routes'] = list(range(routes_count))
    data['terminals_in_route'] = terminals_in_route

    return terminals_in_route, stats

