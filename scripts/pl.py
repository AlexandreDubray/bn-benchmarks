import os
import subprocess
import sys
from operator import mul
from functools import reduce
import random

def get_evidence_content(evidence):
    try:
        return [int(x) for x in open(evidence).read().split()]
    except FileNotFoundError:
        return [int(x) for x in evidence.split()]

def get_minimal_uai(uai_file, evidences, queries):
    number_evidences = evidences[0] if len(evidences) > 0 else 0
    variables_in_evidences = [evidences[2*i+1] for i in range(number_evidences)]
    number_query = queries[0]
    variables_in_queries = [queries[2*i+1] for i in range(number_query)]
    content = open(uai_file).read().split()
    number_variables = int(content[1])
    parents = [[] for _ in range(number_variables)]
    idx = 2 + number_variables + 1
    for _ in range(number_variables):
        scope_size = int(content[idx])
        idx += 1
        vars = [int(content[idx + i]) for i in range(scope_size)]
        idx += len(vars)
        parents[vars[-1]] = vars[:-1]

    is_needed = [False for _ in range(number_variables)]
    queue = []
    for x in variables_in_evidences:
        queue.append(x)

    for x in variables_in_queries:
        queue.append(x)

    while len(queue) > 0:
        x = queue.pop()
        if not is_needed[x]:
            is_needed[x] = True
            for p in parents[x]:
                queue.append(p)

    new_ids = {}
    new_domains = []
    for v in range(number_variables):
        if is_needed[v]:
            new_ids[v] = len(new_ids)
            new_domains.append(content[2 + v])

    new_uai_content = ['BAYES', f'{len(new_ids)}'] + new_domains + [f'{len(new_ids)}']

    new_scopes = []
    idx = 2 + number_variables + 1
    for _ in range(number_variables):
        scope_size = int(content[idx])
        idx += 1
        vars = [int(content[idx + i]) for i in range(scope_size)]
        idx += len(vars)
        v = vars[-1]
        if is_needed[v]:
            new_scopes.append(f'{scope_size}')
            for vv in vars:
                new_scopes.append(f'{new_ids[vv]}')

    new_uai_content += new_scopes

    for v in range(number_variables):
        nb_entry = int(content[idx])
        if is_needed[v]:
            new_uai_content.append(content[idx])
            new_uai_content += content[idx+1:(idx+1+nb_entry)]
        idx += 1 + nb_entry

    for i in range(number_evidences):
        evidences[2*i + 1] = new_ids[evidences[2*i + 1]]

    for i in range(number_query):
        queries[2*i+1] = new_ids[queries[2*i + 1]]


    return new_uai_content

def parent_values_from_domain(domains):
    values = []
    current = [0 for _ in domains]
    number_values = reduce(mul, domains, 1)
    for _ in range(number_values):
        values.append([x for x in current])
        for i in range(len(current)-1, -1, -1):
            current[i] = (current[i] + 1) % domains[i]
            if current[i] != 0: break
    return values

if __name__ == '__main__':
    if len(sys.argv) != 6 or "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python pl.py [--help] <model.uai> <evidence> <reduce> <problog command>")
        print("\tmodel.uai: The BN, in uai format")
        print("\tevidence: The evidences, either as a file or a string (<nb_evidence> <variable1 value1> <variable2 value2> ...)")
        print("\tquery: The queries to do (<nb_query> <variable1 value1> ...)")
        print("\treduce: Should the UAI file be reduced ? (true|false)")
        print("\tproblog command: The command to run. Use the placeholder {} for the input file")
        sys.exit(1)

    evidence = get_evidence_content(sys.argv[2])
    queries = get_evidence_content(sys.argv[3])
    if sys.argv[4] == 'true' or sys.argv[4] == 'True':
        content = get_minimal_uai(sys.argv[1], evidence, queries)
    else:
        content = open(sys.argv[1]).read().split()

    if content[0] != 'BAYES':
        print("The input file should be a UAI bayesian network (BAYES header)")
        sys.exit(1)

    number_var = int(content[1])
    variables_domain_size = [int(x) for x in content[2:2+number_var]]
    assert(int(content[2 + number_var]) == number_var)
    variables_scopes = []
    content_index = 3 + number_var
    # Parsing the scope of each CPT
    for _ in range(number_var):
        number_var_in_scope = int(content[content_index])
        content_index += 1
        variables_scopes.append([int(content[content_index + x]) for x in range(number_var_in_scope)])
        content_index += number_var_in_scope

    # Parsing each CPT. There is one clause per CPT entry, using annotated disjuction we have one line per CPT line
    clauses = []
    for idx in range(number_var):
        # Skipping the number of probability
        content_index += 1
        scope_variables_domain = [variables_domain_size[x] for x in variables_scopes[idx]]
        nb_parents = len(variables_scopes[idx]) - 1
        target_var = variables_scopes[idx][-1]
        nb_values = variables_domain_size[target_var]
        variables_choices = parent_values_from_domain(scope_variables_domain)
        choice_idx = 0

        while choice_idx < len(variables_choices):
            probas = [float(content[content_index + i]) for i in range(nb_values)]
            values = [f"v{target_var}(v{i})" for i in range(nb_values)]
            head = "; ".join([f'{probas[i]}::{values[i]}' for i in range(nb_values)])
            tail = ", ".join([f'v{variables_scopes[idx][i]}(v{variables_choices[choice_idx][i]})' for i in range(nb_parents)])
            if len(tail) > 0:
                clauses.append(f'{head} :- {tail}.')
            else:
                clauses.append(f'{head}.')
            choice_idx += len(values)
            content_index += nb_values

    if len(evidence) > 0:
        number_evidence = evidence[0]
        for i in range(number_evidence):
            var = evidence[2*i+1]
            val = evidence[2*i+2]
            clauses.append(f'v{var}(v{val}).')

    number_query = queries[0]
    for i in range(number_query):
        var = queries[2*i+1]
        val = queries[2*i+2]
        clauses.append(f'query(v{var}(v{val})).')

    filename = f'tmp_{random.randint(0, 1_000_000_000)}.pl'
    with open(filename, 'w') as f:
        f.write('\n'.join(clauses))

    subprocess.run(sys.argv[5].format(filename).split())
    os.remove(filename)
