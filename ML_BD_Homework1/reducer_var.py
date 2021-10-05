#!/usr/bin/env python
"""reducer.py"""

import sys    

def main():
    chunk_sizes = []
    mean_values = []
    var_values = []

    for line in sys.stdin:
        line = line.strip().split('\t')
        chunk_size, chunk_mean, chunk_var = list(map(float, line[1].split(' ')))
        chunk_sizes.append(chunk_size)
        mean_values.append(chunk_mean)
        var_values.append(chunk_var)

    cmv = list(zip(chunk_sizes, mean_values, var_values))
    c_prev, m_prev, v_prev = cmv[0]
    
    for c, m, v in cmv[1:]:
        var = (c_prev * v_prev + c * v) / (c_prev + c) + c_prev * c * ((m - m_prev)**2 / (c_prev + c)**2)
        m_prev = (m * c + m_prev * c_prev) / (c_prev + c)
        c_prev = c + c_prev
        v_prev = var

    print(var)

    with open('var_results.txt', 'a') as output:
        output.write('\t' + str(var))

if __name__ == "__main__":
    main()
