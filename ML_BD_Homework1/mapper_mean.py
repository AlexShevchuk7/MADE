#!/usr/bin/env python
"""mapper.py"""

import sys, csv

def calculate_mean_standard_way(values):
    return sum(values) / len(values)

def main():
    
    chunk_size = 10000
    price_tuples, chunk_values = [], []
    chunk = 0
    prices = []

    f = sys.stdin.read().splitlines()
    csv_reader = csv.reader(f)
    data = list(csv_reader)
        
    for k, row in enumerate(data):

        if k == 0:
            continue
            
        if k < (chunk + 1) * chunk_size:
            chunk_values.append(float(row[9]))
        else:
            chunk_mean = sum(chunk_values) / len(chunk_values)
            price_tuples.append((len(chunk_values), chunk_mean))
            chunk_values = [float(row[9])]
            chunk += 1
         
    chunk_mean = sum(chunk_values) / len(chunk_values)
    price_tuples.append((len(chunk_values), chunk_mean))

    for chunk, item in enumerate(price_tuples):
        output = str(chunk) + '\t' + str(item[0]) + ' ' + str(item[1])
        print(output)

    with open('mean_results.txt', 'w') as output:
        prices = []
        for k, row in enumerate(data):
            if k == 0:
                continue
            else:
                prices.append(float(row[9]))

        mean_price = sum(prices) / len(prices)
        output.write(str(mean_price))

if __name__ == "__main__":
    main()
