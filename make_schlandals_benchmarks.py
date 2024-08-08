import sys
import os
import random

random.seed(697458)

script_dir = os.path.dirname(os.path.realpath(__file__))
uai_dir = os.path.join(script_dir, 'bayesian-networks', 'uai')
outdir = os.path.join(script_dir, 'bench-input')
os.makedirs(outdir, exist_ok=True)

def _get_uai_queries(filename):
    with open(os.path.join(uai_dir, filename)) as f:
        content = f.read().split()
        number_var = int(content[1])
        vars_domain_size = [int(content[2 + i]) for i in range(number_var)]
        variables = [i for i in range(number_var)]
        random.shuffle(variables)

        queries = []
        for i in range(min(50, len(variables))):
            var = variables[i]
            value = random.randint(0, vars_domain_size[var]-1)
            queries.append(f'1 {var} {value}')
        return queries


def make_opti_bench():
    instances = [f for f in os.listdir(uai_dir) if os.path.isfile(os.path.join(uai_dir, f))]
    with open(os.path.join(outdir, 'opti-benchs.csv'), 'w') as f:
        f.write('model,query')
        for model in instances:
            f.write('\n')
            print(f"Parsing {model}")
            f.write('\n'.join([f'{model},{query}' for query in _get_uai_queries(model)]))

def make_learn_bench():
    pass

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python make_schlandals_benchmarks.py [opti|learn]")
        sys.exit(1)
    if sys.argv[1] == 'opti':
        make_opti_bench()
    elif sys.argv[1] == 'learn':
        make_learn_bench()
    else:
        print("Usage: python make_schlandals_benchmarks.py [opti|learn]")
        sys.exit(1)
