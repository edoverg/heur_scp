import time
import sys
import os

# PREPROCESSING
def solve_coverage(instance_path):
    time_start = time.time()
    all_rows = []
    col_num = 0
    
    # Extract instance name from path
    instance_name = os.path.basename(instance_path)
    
    with open(instance_path, 'r') as f:
        initial_data = list(map(int, next(f).split()))
        col_num,row_num = initial_data
        print(type(col_num))
        for line in f:
            parsed_line = list(map(int, line.split()))
            cost = parsed_line[0]
            mask = 0
            for column_index in parsed_line[2:]:
                mask |= (1 << (column_index - 1))
                
            all_rows.append((cost, mask)) # Store as a tuple

    # GREEDY
    #now that we have the list of tuples, we start the greedy:
    #at each iteration we store the index where the best coverage/cost is achieved
    covered = 0
    covered |= (1 << (col_num - 1)) #initialize an empty universe

    target = (1 << col_num) - 1 #this is the target (all ones)
    chosen_indices = []
    greedy_all_rows = all_rows
    tot_cost = 0
    while covered < target:
        best_value = float('inf')
        best_index = -1
        
        for i in range(row_num):
            if greedy_all_rows[i]==None:
                continue
            cost = greedy_all_rows[i][0] #get the cost
            offered_coverage = greedy_all_rows[i][1] #get the coverage the instance can provide
            added_cover = offered_coverage & ~covered #compute the effective additional coverage
            try:
                cost_per_cover = cost/added_cover.bit_count()
            except:
                cost_per_cover = float('inf')
            
            if cost_per_cover < best_value:
                best_value = cost_per_cover
                best_index = i
        
        covered |= greedy_all_rows[best_index][1]
        tot_cost += greedy_all_rows[best_index][0]
        greedy_all_rows[best_index] = None
        chosen_indices.append(best_index) #best greedy candidate
    #print(covered)
    #print(chosen_indices)
    #print(tot_cost)
    time_end = time.time()
    print(f"#### Feasible solution of value {tot_cost} [time {time_end - time_start}]")
    
    # Write solution file
    solution_filename = f"{instance_name}.1.sol"
    with open(solution_filename, 'w') as f:
        f.write(f"{tot_cost}\n")
        f.write(" ".join(map(str, chosen_indices)) + "\n")
    
    return tot_cost, chosen_indices


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_instance>", file=sys.stderr)
        sys.exit(1)
    
    instance_path = sys.argv[1]
    solve_coverage(instance_path)


