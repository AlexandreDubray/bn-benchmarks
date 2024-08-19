import sys
import subprocess
import re
import os
import random

def get_evidence_content(evidence):
    try:
        return [int(x) for x in open(evidence).read().split()]
    except FileNotFoundError:
        return [int(x) for x in evidence.split()]

def get_minimal_uai(uai_file, evidences):
    number_evidences = evidences[0]
    variables_in_evidences = [evidences[2*i+1] for i in range(number_evidences)]
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

    for i in range(evidences[0]):
        evidences[2*i + 1] = new_ids[evidences[2*i + 1]]

    return new_uai_content

def parse_exe_output(fn):
    output = {}
    with open(f'{fn}.cnf') as f:
        lines = f.readlines()
        s = lines[0].rstrip().split(' ')
        output['nvars'] = int(s[2])
        output['nclauses'] = int(s[3])
        output['clauses'] = lines[1:]
        
    weights = {}
    with open(f'{fn}.weight') as f:
        for line in f.readlines()[:-1]:
            s = line.rstrip().split(' ')
            var = int(s[0])
            weight = float(s[1])
            weights[var] = weight
    output['weights'] = weights
    
    variable_map = {}
    with open(f'{fn}.map') as f:
        for line in f:
            s = line.rstrip().split('=')
            var = int(s[0])
            subsplit = s[1].split('][')
            variable_map[var] = [[int(x) for x in re.findall(r'-?\d+', y)] for y in subsplit]
    output['variable_map'] = variable_map
    return output

if __name__ == '__main__':
    if len(sys.argv) != 5 or sys.argv[1] == "--help" or sys.argv[1] == "-h":
        print("Usage: python enc3.py [--help] <model.uai> <evidence> <enc3|enc4|enc4linp> <WMC command>")
        print("\tmodel.uai: The BN, in uai format")
        print("\tevidence: The evidences, either as a file or a string")
        print("\tenc3|enc4|enc4linp: The encoding to use")
        print("\tWMC command: The command to run. Use the placeholder {} for the input file")
        sys.exit(1)
    evidence = get_evidence_content(sys.argv[2])
    model = get_minimal_uai(sys.argv[1], evidence)
    fn = random.randint(0, 1_000_000_000)
    with open(f'{fn}.uai', 'w') as f:
        f.write(' '.join(model))
    if sys.argv[3] == 'enc3':
        bash_cmd = ['./bn2cnf_linux', '-i', f'{fn}.uai', '-o', f'{fn}.cnf', '-w', f'{fn}.weight', '-v', f'{fn}.map']
    elif sys.argv[3] == 'enc4':
        bash_cmd = ['./bn2cnf_linux', '-i', f'{fn}.uai', '-o', f'{fn}.cnf', '-w', f'{fn}.weight', '-v', f'{fn}.map', '-s', 'prime']
    elif sys.argv[3] == 'enc4linp':
        bash_cmd = ['./bn2cnf_linux', '-i', f'{fn}.uai', '-o', f'{fn}.cnf', '-w', f'{fn}.weight', '-v', f'{fn}.map', '-s', 'prime', '-e', 'LOG', 'implicit']
    else:
        print(f'Error: receive as algorithm {sys.argv[3]} but should be one of: enc3, enc4, enc4linp')
        sys.exit(1)
    subprocess.run(bash_cmd, stdout=subprocess.DEVNULL)

    output = parse_exe_output(fn)
    evidence_clauses = []
    number_evidence = evidence[0]
    for i in range(number_evidence):
        var = evidence[2*i + 1]
        value = evidence[2*i + 2]
        for value_indicator_variables in output['variable_map'][var][value]:
            evidence_clauses.append(f'{value_indicator_variables} 0')

    with open(f'{fn}.cnf', 'w') as f:
        f.write(f'p cnf {output["nvars"]} {len(output["clauses"]) + len(evidence_clauses)}\n')
        for v in output['weights']:
            f.write(f'c p weight {v} {output["weights"][v]} 0\n')
        f.write(''.join(output["clauses"]))
        f.write('\n'.join(evidence_clauses))

    os.remove(f'{fn}.weight')
    os.remove(f'{fn}.map')
    os.remove(f'{fn}.uai')

    subprocess.run(sys.argv[4].format(f'{fn}.cnf').split())

    os.remove(f'{fn}.cnf')
