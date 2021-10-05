#!/usr/bin/env python
"""reducer.py"""

import sys    

def main():
    chunk_values = []
    mean_values = []
    word = None

    for line in sys.stdin:
        line = line.strip().split('\t')
        chunk_size, chunk_mean = list(map(float, line[1].split(' ')))
        chunk_values.append(chunk_size)
        mean_values.append(chunk_mean)
        
    total_mean = sum([chunk_size * chunk_mean 
                        for chunk_size, chunk_mean in zip(chunk_values, mean_values)]) / sum(chunk_values)

    print(total_mean)

    with open('mean_results.txt', 'a') as output:
        output.write('\t' + str(total_mean))

if __name__ == "__main__":
    main()
