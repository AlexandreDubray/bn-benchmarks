import os
import re
"""
This script parses the bayesian networks in BIF format (from the bif directory) and transforms them
into UAI format.
Each network is then output in the uai directory.
"""

script_dir = os.path.dirname(os.path.realpath(__file__))
bif_dir = os.path.join(script_dir, 'bif')
uai_dir = os.path.join(script_dir, 'uai')
os.makedirs(uai_dir, exist_ok=True)

def parse_variables(dataset):
    variables = {}
    with open(os.path.join(bif_dir, dataset + '.bif')) as f:
        lines = f.readlines()
        i = 0
        vid = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith('variable'):
                # Start of the definition of a variable. We get the name of the variable from this line
                s = line.rstrip().split(' ')
                variable_name = s[1]
                # The domain and type of variable is defined at the next line
                domain_def = lines[i+1].strip().split(' ')
                dom_size = int(domain_def[3])
                values = [x.replace(',', '') for x in domain_def[6:-1]]
                variables[variable_name] = {
                        'dom_size': dom_size,
                        'domain': values,
                        'id': vid
                        }
                vid += 1
                i += 2
            else:
                i += 1
    return variables

def get_cpt(dataset, network_variables):
    with open(os.path.join(bif_dir, dataset + '.bif')) as f:
        lines = f.readlines()
        # Regex to extract the variables from CPT definition
        cpt_variable_pattern = re.compile("probability \((.*)\) {")
        # Regex to extract probability from a CPT line
        cpt_distribution_pattern = re.compile("\((.*)\) (.*)")
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith('probability'):
                # Extract the variables from the CPT. The first variable is the child, the other are the parents.
                vars = cpt_variable_pattern.match(line).group(1).replace(',', '')
                s = vars.split('|')
                target_var = s[0].rstrip().lstrip()
                parent_vars = s[1].rstrip().lstrip().split(' ') if len(s) > 1 else []
                i += 1
                distributions = []
                parents_domain = []
                line = re.sub('[,|;]', '', lines[i].strip())
                if len(parent_vars) > 0:
                    # } means the end of the CPT
                    while line.rstrip() != "}":
                        pattern = cpt_distribution_pattern.match(line)
                        parents_value = pattern.group(1).split(' ')
                        probabilities = [float(x) for x in pattern.group(2).split(' ')]
                        distributions.append(probabilities)
                        parents_domain.append(parents_value)
                        i += 1
                        line = re.sub('[,|;]', '', lines[i].strip())
                else:
                    probabilities = [float(x) for x in line.split(' ')[1:]]
                    distributions.append(probabilities)
                    parents_domain.append([])
                network_variables[target_var]['cpt'] = {
                        'distributions': distributions,
                        'parents_domain': parents_domain,
                        'parents_var': parent_vars,
                }
            i += 1

def write_uai(instance):
    network_variables = parse_variables(instance)
    get_cpt(instance, network_variables)
    with open(os.path.join(uai_dir, f'{instance}.uai'), 'w') as f:
        # preamble
        # Type of network
        f.write('BAYES\n')
        # Number of variable
        f.write(f'{len(network_variables)}\n')
        # Domain of the variables
        f.write(' '.join([str(network_variables[v]["dom_size"]) for v in network_variables]) + '\n')
        # Number of function (CPT) in the newtork
        f.write(f'{len(network_variables)}\n')
        # For each CPT, the number of variable included in it, ending with the variable id
        for v in network_variables:
            parents = " ".join(reversed([str(network_variables[p]["id"]) for p in network_variables[v]['cpt']['parents_var']]))
            if parents != "":
                f.write(f'{len(network_variables[v]["cpt"]["parents_var"]) + 1} {parents} {network_variables[v]["id"]}\n')
            else:
                f.write(f'{len(network_variables[v]["cpt"]["parents_var"]) + 1} {network_variables[v]["id"]}\n')

        f.write('\n')
        
        cpts = []
        for v in network_variables:
            number_values = sum([len(x) for x in network_variables[v]['cpt']['distributions']])
            lines = []
            for distribution in network_variables[v]['cpt']['distributions']:
                lines.append(' '.join([str(x) for x in distribution]))
            cpts.append("{}\n{}".format(
                number_values,
                " ".join(lines)
                ))
        f.write('\n'.join(cpts))




instances = [f.split('.')[0] for f in os.listdir(bif_dir) if os.path.isfile(os.path.join(bif_dir, f))]

for instance in instances:
    print(instance)
    write_uai(instance)
