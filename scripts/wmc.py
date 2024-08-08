import sys
import subprocess
import re
import os

def get_evidence_content(evidence):
    try:
        return [int(x) for x in open(evidence).read().split()]
    except FileNotFoundError:
        return [int(x) for x in evidence.split()]

def parse_exe_output():
    output = {}
    with open('tmp.cnf') as f:
        lines = f.readlines()
        s = lines[0].rstrip().split(' ')
        output['nvars'] = int(s[2])
        output['nclauses'] = int(s[3])
        output['clauses'] = lines[1:]
        
    weights = {}
    with open('tmp.weight') as f:
        for line in f.readlines()[:-1]:
            s = line.rstrip().split(' ')
            var = int(s[0])
            weight = float(s[1])
            weights[var] = weight
    output['weights'] = weights
    
    variable_map = {}
    with open('tmp.map') as f:
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
    model = sys.argv[1]
    evidence = get_evidence_content(sys.argv[2])
    if sys.argv[3] == 'enc3':
        bash_cmd = ['./bn2cnf_linux', '-i', model, '-o', 'tmp.cnf', '-w', 'tmp.weight', '-v', 'tmp.map']
    elif sys.argv[3] == 'enc4':
        bash_cmd = ['./bn2cnf_linux', '-i', model, '-o', 'tmp.cnf', '-w', 'tmp.weight', '-v', 'tmp.map', '-s', 'prime']
    elif sys.argv[3] == 'enc4linp':
        bash_cmd = ['./bn2cnf_linux', '-i', model, '-o', 'tmp.cnf', '-w', 'tmp.weight', '-v', 'tmp.map', '-s', 'prime', '-e', 'LOG', 'implicit']
    else:
        print(f'Error: receive as algorithm {sys.argv[3]} but should be one of: enc3, enc4, enc4linp')
        sys.exit(1)
    subprocess.run(bash_cmd, stdout=subprocess.DEVNULL)

    output = parse_exe_output()
    evidence_clauses = []
    number_evidence = evidence[0]
    for i in range(number_evidence):
        var = evidence[2*i + 1]
        value = evidence[2*i + 2]
        for value_indicator_variables in output['variable_map'][var][value]:
            evidence_clauses.append(f'{value_indicator_variables} 0')

    with open('input.cnf', 'w') as f:
        f.write(f'p cnf {output["nvars"]} {len(output["clauses"]) + len(evidence_clauses)}\n')
        for v in output['weights']:
            f.write(f'c p weight {v} {output["weights"][v]} 0\n')
        f.write(''.join(output["clauses"]))
        f.write('\n'.join(evidence_clauses))

    os.remove('tmp.cnf')
    os.remove('tmp.weight')
    os.remove('tmp.map')

    subprocess.run(sys.argv[4].format('input.cnf').split())

    os.remove('input.cnf')
