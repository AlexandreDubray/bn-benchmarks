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

if __name__ == '__main__':
    if len(sys.argv) != 3 or "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python dai.py [--help] <model.uai> <evidence>")
        print("\tmodel.uai: The BN, in uai format")
        print("\tevidence: The evidences, either as a file or a string")
        sys.exit(1)
    evidence = get_evidence_content(sys.argv[2])
    model = open(sys.argv[1]).read().split()
    #model = get_minimal_uai(sys.argv[1], evidence)
    fn = random.randint(0, 1_000_000_000)
    #with open(f'{fn}.uai', 'w') as f:
    #    f.write(' '.join(model))
    with open(f'{fn}.evid', 'w') as f:
        f.write(f'{evidence[0]}')
        for i in range(evidence[0]):
            f.write(f'\n{evidence[2*i+1]} {evidence[2*i+2]}')
    cmd = ['dai', sys.argv[1], f'{fn}.evid', '0', 'PR']
    subprocess.run(cmd)
    #os.remove(f'{fn}.uai')
    os.remove(f'{fn}.evid')
