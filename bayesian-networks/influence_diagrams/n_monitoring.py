import sys
import os
import random
import itertools
import math
import subprocess
import re

# Example taken from https://gamma-opt.github.io/DecisionProgramming.jl/dev/examples/n-monitoring/
# Reproducing their experiments with the weights

def get_sensor_report_proba():
    """Returns 2-tuples that represent the probability that a sensor returns a true positive high-high or low-low"""
    x = random.random()
    y = random.random()
    return (max(x, 1 - x), max(y, 1-y))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'Use: python n_monitoring <number monitors>')
        sys.exit(1)
    random.seed(59873115)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    julia_template = open(os.path.join(script_dir, 'julia_template.tpl')).read()
    julia_args = []

    N = int(sys.argv[1])
    julia_args.append(str(N))
    #output_dir = os.path.join(script_dir, 'n_monitoring', str(N), 'cnf')
    #julia_file = os.path.join(script_dir, 'n_monitoring', str(N), 'decision_programming.jl')
    julia_file = os.path.join(script_dir, 'decision_programming.jl')
    #os.makedirs(output_dir, exist_ok=True)
    B = 0.03
    # Number of distributions needed for the problem:
    #   - One for the load, is it high or low
    #   - Two distributions per sensor report (depending on the value of the load)
    #   - Two distribution per reinforcement action (depending on the sensor report)
    #   - The failure depend on N + 1 binary variables: the load and the N reinforcement
    #   - The cost depend on N + 1 binary variables: the failure and the N reinforcement
    number_distributions = 1 + 2*N + 2*N + 2**(N+1) + 2*(2**(N+1))
    # Following the documentation, the cost is a random variable between [0,1]
    reinforcement_costs = [random.random() for _ in range(N)]
    julia_args.append(f'[{", ".join([str(x) for x in reinforcement_costs])}]')
    # Probability that the load is high
    high_load_proba = random.random()
    julia_args.append(str(high_load_proba))

    sensor_report_probabilities = [get_sensor_report_proba() for _ in range(N)]
    julia_args.append(f'[{", ".join([f"[{x}, {y}]" for (x,y) in sensor_report_probabilities])}]')


    # We generate a template for the CNF files
    clauses = list()
    distributions = list()
    var_id = number_distributions*2 + 1
    load_var = {'high': var_id, 'low': var_id + 1}
    var_id += 2
    reports_var = {}
    for i in range(N):
        reports_var[i] = {'high': var_id, 'low': var_id + 1}
        var_id += 2
    reinforce_var = {}
    for i in range(N):
        reinforce_var[i] = {'yes': var_id, 'no': var_id + 1}
        var_id += 2

    failure_var = {'yes': var_id, 'no': var_id + 1}
    var_id += 2
    target_var = {'success': var_id, 'failure': var_id + 1}
    var_id += 2

    distribution_var_id = 1

    # Generating the clauses
    
    # For the load
    clauses.append(f'-{distribution_var_id} {load_var["high"]} 0')
    clauses.append(f'-{distribution_var_id + 1} {load_var["low"]} 0')
    distributions.append(f'c p distribution {high_load_proba} {1.0 - high_load_proba}')
    distribution_var_id += 2

    # For the reports
    for i in range(N):
        clauses.append(f'-{load_var["high"]} -{distribution_var_id} {reports_var[i]["high"]} 0')
        clauses.append(f'-{load_var["high"]} -{distribution_var_id + 1} {reports_var[i]["low"]} 0')
        clauses.append(f'-{load_var["low"]} -{distribution_var_id + 2} {reports_var[i]["high"]} 0')
        clauses.append(f'-{load_var["low"]} -{distribution_var_id + 3} {reports_var[i]["low"]} 0')
        (true_high, true_low) = sensor_report_probabilities[i]
        distributions.append(f'c p distribution {true_high} {1.0 - true_high}')
        distributions.append(f'c p distribution {1.0 - true_low} {true_low}')
        distribution_var_id += 4

    # For the reinforcement action
    for i in range(N):
        clauses.append(f'-{reports_var[i]["high"]} -{distribution_var_id} {reinforce_var[i]["yes"]} 0')
        clauses.append(f'-{reports_var[i]["high"]} -{distribution_var_id + 1} {reinforce_var[i]["no"]} 0')
        clauses.append(f'-{reports_var[i]["low"]} -{distribution_var_id + 2} {reinforce_var[i]["yes"]} 0')
        clauses.append(f'-{reports_var[i]["low"]} -{distribution_var_id + 3} {reinforce_var[i]["no"]} 0')
        distributions.append(None)
        distributions.append(None)
        distribution_var_id += 4

    # For the failure
    parent_domains = [['high', 'low']] + [['yes', 'no'] for _ in range(N)]
    numerator_high = random.random()
    numerator_low = random.random()
    julia_args.append(f'[{numerator_high}, {numerator_low}]')

    for parent_values in itertools.product(*parent_domains):
        parent_variables = [-load_var[parent_values[0]]] + [-reinforce_var[i][parent_values[i+1]] for i in range(N)]
        clauses.append(f'{" ".join([str(x) for x in parent_variables])} -{distribution_var_id} {failure_var["yes"]} 0')
        clauses.append(f'{" ".join([str(x) for x in parent_variables])} -{distribution_var_id + 1} {failure_var["no"]} 0')
        denominator = math.exp(B* sum([reinforcement_costs[i] for i in range(N) if parent_values[i+1] == 'yes']))
        numerator = max(numerator_high, 1 - numerator_high) if parent_values[0] == 'high' else min(numerator_low, 1 - numerator_low)
        p = numerator / denominator
        distributions.append(f'c p distribution {p} {1 - p}')
        distribution_var_id += 2

    # For the cost
    # N + 1 = N reinforcement + 1 failure
    sum_cost_reinforcement = sum(reinforcement_costs)
    min_cost = -sum_cost_reinforcement
    max_cost = 100
    parent_domains = [['yes', 'no'] for _ in range(N + 1)]
    for parent_values in itertools.product(*parent_domains):
        parent_variables = [-failure_var[parent_values[0]]] + [-reinforce_var[i][parent_values[i+1]] for i in range(N)]
        clauses.append(f'{" ".join([str(x) for x in parent_variables])} -{distribution_var_id} {target_var["success"]} 0')
        clauses.append(f'{" ".join([str(x) for x in parent_variables])} -{distribution_var_id + 1} {target_var["failure"]} 0')
        cost_modifier = sum([-reinforcement_costs[i] for i in range(N) if parent_values[i+1] == 'yes'])
        cost = 100 if parent_values[0] == 'no' else 0
        cost +=  cost_modifier
        cost = (cost - min_cost) / (max_cost - min_cost)
        distributions.append(f'c p distribution {cost} {1 - cost}')
        distribution_var_id += 2

    template_distributions = [i for i in range(len(distributions)) if distributions[i] is None]
    domains = [[(1.0, 0.0), (0.0, 1.0)] for _ in range(len(template_distributions))]
    file_idx = 1
    best_proba = 0
    best_strategy = None
    for selection in itertools.product(*domains):
        j = 0
        for idx in template_distributions:
            distributions[idx] = f'c p distribution {selection[j][0]} {selection[j][1]}'
            j += 1

        global_strategy = []
        j = 0
        for i in range(N):
            strategy = {'high': 'yes' if selection[j] == (1.0, 0.0) else 'no',
                        'low': 'yes' if selection[j+1] == (1.0, 0.0) else 'no'}
            global_strategy.append(strategy)
            j += 2
        #with open(os.path.join(output_dir, f'{file_idx}.cnf'), 'w') as f:
        with open(os.path.join(script_dir, 'sch.cnf'), 'w') as f:
            f.write(f'p cnf {var_id} {len(clauses) + 1}\n')
            f.write('\n'.join(distributions) + '\n')
            f.write('\n'.join(clauses) + '\n')
            f.write(f'-{target_var["failure"]} 0')

        result = subprocess.run(['schlandals', 'search', '-i', 'sch.cnf'], capture_output=True, encoding='UTF-8')
        proba = float(re.findall(r"\d+.\d+", result.stdout.strip())[0])
        if proba > best_proba:
            best_proba = proba
            best_strategy = global_strategy 

        file_idx += 1

    with open(julia_file, 'w') as f:
        f.write(julia_template.format(*julia_args))

    result = subprocess.run(['julia', '+1.6', julia_file], capture_output=True, encoding='UTF-8')
    local_strategies = re.findall(r'LocalDecisionStrategy\[(.*)\]', result.stdout.split('\n')[-1])[0].split(',')
    dp_optimal_strategy = []
    for i in range(N):
        s = local_strategies[i].strip()[1:-1].split(';')
        strategy = {'high': 'yes' if s[0] == '1 0' else 'no',
                    'low': 'yes' if s[1] == '1 0' else 'no'}
        dp_optimal_strategy.append(strategy)

    if best_strategy != dp_optimal_strategy:
        print('Optimal strategies do not match')
    else:
        print('Found same strategy')
