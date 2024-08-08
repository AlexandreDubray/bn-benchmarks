import os
import subprocess
import sys
from operator import mul
from functools import reduce

def get_evidence_content(evidence):
    try:
        return [int(x) for x in open(evidence).read().split()]
    except FileNotFoundError:
        return [int(x) for x in evidence.split()]

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
    if len(sys.argv) != 5 or "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python pl.py [--help] <model.uai> <evidence> <problog command>")
        print("\tmodel.uai: The BN, in uai format")
        print("\tevidence: The evidences, either as a file or a string (<nb_evidence> <variable1 value1> <variable2 value2> ...)")
        print("\tquery: The queries to do (<nb_query> <variable1 value1> ...)")
        print("\tproblog command: The command to run. Use the placeholder {} for the input file")

    model = sys.argv[1]
    evidence = get_evidence_content(sys.argv[2])
    queries = get_evidence_content(sys.argv[3])

    with open(model) as f:
        content = f.read().split()
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

    with open('input.pl', 'w') as f:
        f.write('\n'.join(clauses))

    subprocess.run(sys.argv[4].format('input.pl').split())
    os.remove('input.pl')
