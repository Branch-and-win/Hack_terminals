import random

def generate_routes(data, params, routes_count, k=1):
    TERMINALS = data['TERMINALS']
    EdgeTime = data['EdgeTime']
    balances = data['start_balance']
    days_left = data.get('days_left', {})
    days_weights = {t: 1/(days_left[t] + 1) **(k+0.5) for t in days_left}
    TerminalsInRoute = {}
    Stats = {t:0 for t in TERMINALS}
    for r in range(routes_count):
        candidate_terms = [t for t in TERMINALS] 
        candidate_terms = candidate_terms if len(candidate_terms) else TERMINALS
        current_terminal = random.choices(candidate_terms, weights=[days_weights[t] for t in candidate_terms], k=1)[0]
        Stats[current_terminal] += 1
        TerminalsInRoute[r]=[current_terminal]
        cumm_time = 0
        while True:
            available_terms = [
                terminal for terminal in TERMINALS if terminal not in TerminalsInRoute[r] and 
                cumm_time + EdgeTime[current_terminal,terminal] + params['maintenance_minutes'] <= params['shift_minutes']
            ]
            if not len(available_terms):
                break
            next_terminal = random.choices(
                available_terms,
                weights=[days_weights[t] / EdgeTime[current_terminal,t] for t in available_terms], k=1)[0]
            Stats[next_terminal] += 1
            cumm_time += EdgeTime[current_terminal,next_terminal] + params['maintenance_minutes']
            TerminalsInRoute[r].append(next_terminal)
            current_terminal = next_terminal

    data['ROUTES'] = list(range(routes_count))
    data['terminals_in_route'] = TerminalsInRoute

    return TerminalsInRoute, Stats
