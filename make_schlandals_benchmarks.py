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
        idx = 2 + number_var + 1
        scopes = []
        for _ in range(number_var):
            scope_size = int(content[idx])
            idx += 1
            scopes.append([int(content[idx + i]) for i in range(scope_size)])
            idx += scope_size

        is_leaf = [True for _ in range(number_var)]

        for variable in range(number_var):
            for parent in scopes[variable][:-1]:
                is_leaf[parent] = False

        queries = []
        leaves = [x for x in range(number_var) if is_leaf[x]]
        if len(leaves) < 200:
            for variable in range(number_var):
                if is_leaf[variable]:
                    value = random.randint(0, vars_domain_size[variable] - 1)
                    #for value in range(vars_domain_size[variable]):
                    queries.append(f'1 {variable} {value}')
        else:
            random.shuffle(leaves)
            for variable in leaves[:200]:
                value = random.randint(0, vars_domain_size[variable] - 1)
                queries.append(f'1 {variable} {value}')
        return queries


def make_opti_bench():
    instances = [f for f in os.listdir(uai_dir) if os.path.isfile(os.path.join(uai_dir, f))]
    with open(os.path.join(outdir, 'opti-benchs.csv'), 'w') as f:
        f.write('model,query')
        for model in instances:
            if 'fs' in model or 'blockmap' in model or 'mastermind' in model:
                continue
            f.write('\n')
            queries = _get_uai_queries(model)
            print(f"Parsing {model}: {len(queries)} queries")
            model_path = os.path.join(uai_dir, model)
            f.write('\n'.join([f'{model_path},{query}' for query in queries]))

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
