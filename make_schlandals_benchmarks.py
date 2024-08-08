import sys
import os

script_dir = os.path.dirname(os.path.realpath(__file__))
uai_dir = os.path.join(script_dir, 'bayesian-networks', 'uai')
outdir = os.path.join(script_dir, 'bench-input')
os.makedirs(outdir, exist_ok=True)

def _get_uai_queries(filename):
    with open(os.path.join(uai_dir, filename)) as f:
        content = f.read().split()
        number_var = int(content[1])
        vars_domain_size = [int(content[2 + i]) for i in range(number_var)]
        is_leaf = [True for _ in range(number_var)]
        idx = 2 + number_var + 1
        for _ in range(number_var):
            function_scope_size = int(content[idx])
            idx += 1
            for _ in range(function_scope_size - 1):
                is_leaf[int(content[idx])] = False
                idx += 1
            idx += 1

    queries = []
    for var in range(number_var):
        if is_leaf[var]:
            for i in range(vars_domain_size[var]):
                queries.append(f'1 {var} {i}')
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
