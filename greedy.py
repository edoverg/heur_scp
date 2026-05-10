import time

# PREPROCESSING
def solve_coverage(instance):
    all_rows = []
    col_num = 0
    file_name = 'instances/' + instance
    with open(file_name, 'r') as f:
        initial_data = list(map(int, next(f).split()))
        col_num,row_num = initial_data
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
    available_rows = set(range(row_num))
    tot_cost = 0
    while covered < target:
        best_value = float('inf')
        best_index = -1
        
        for i in available_rows:
            cost = all_rows[i][0] #get the cost
            offered_coverage = all_rows[i][1] #get the coverage the instance can provide
            added_cover = offered_coverage & ~covered #compute the additional coverage
            try:
                cost_per_cover = cost/added_cover.bit_count()
            except:
                cost_per_cover = float('inf')
            
            if cost_per_cover < best_value:
                best_value = cost_per_cover
                best_index = i
        
        covered |= all_rows[best_index][1]
        tot_cost += all_rows[best_index][0]
        available_rows.remove(best_index)
        chosen_indices.append(best_index)#best greedy candidate
    #print(covered)
    #print(chosen_indices)
    #print(tot_cost)
    return tot_cost

if __name__ == "__main__":
    time_start = time.time()
    tot_cost = solve_coverage('rail4284')
    time_end = time.time()
    print(f"#### Feasible solution of value {tot_cost} [time {time_end - time_start}]")