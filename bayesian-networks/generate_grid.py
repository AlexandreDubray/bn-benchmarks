import random

def get_distribution(size, determinist):
    distribution = [random.random() for _ in range(size)]
    s = sum(distribution)
    for i in range(size):
        distribution[i] /= s
    if determinist:
        m = max(distribution)
        for i in range(size):
            distribution[i] = 0 if distribution[i] < m else 1
        assert(sum(distribution) == 1)
    return distribution

def get_node_id(row, col, n):
    return row*n + col

def generate_grid(n, ratio, id):
    outfile = open(f'uai/grid-{n}-{ratio}-{id}.uai', 'w')
    outfile.write('BAYES\n')
    ratio = ratio / 100
    number_nodes = n*n
    number_determinist = int(number_nodes*ratio)
    outfile.write(f'{number_nodes}\n')
    outfile.write(f'{" ".join(["2" for _ in range(number_nodes)])}\n')
    outfile.write(f'{number_nodes}\n')

    nodes = {i: {'parents': [], 'determinist': False} for i in range(number_nodes)}
    ns = [i for i in range(number_nodes)]
    random.shuffle(ns)

    for i in range(number_determinist):
        nodes[ns[i]]['determinist'] = True

    for row in range(n):
        for col in range(n):
            node = get_node_id(row, col, n)
            right = get_node_id(row, col+1, n)
            down = get_node_id(row+1, col, n)
            if row < n-1:
                nodes[node]['parents'].append(down)
            if col < n-1:
                nodes[node]['parents'].append(right)

    for i in range(number_nodes):
        ps = nodes[i]['parents']
        outfile.write(f'{len(ps) + 1} {" ".join([str(x) for x in ps])} {i}\n')

    for i in range(number_nodes):
        ps = nodes[i]['parents']
        number_elements = 2**(len(ps) + 1)
        outfile.write(f'{number_elements}\n')
        distributions = []
        for _ in range(int(number_elements / 2)):
            distributions += [str(x) for x in get_distribution(2, nodes[i]['determinist'])]
        outfile.write(" ".join(distributions) + '\n')

    sink = get_node_id(n-1, n-1, n)
    assert(sink == n*n - 1)
    outfile.close()

if __name__ == '__main__':
    sizes = [10, 12, 14, 16, 18, 20, 25, 30, 40, 50]
    ratios = [50, 75, 90]
    for size in sizes:
        for ratio in ratios:
            for i in range(10):
                generate_grid(size, ratio, i+1)
