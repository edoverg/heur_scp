import time
import glob
import os
import sys
import random

def preprocess_instance(instance_path):
    file_name = instance_path

    all_rows = []
    col_num = 0
    
    with open(file_name, 'r') as f:
        initial_data = list(map(int, next(f).split()))
        col_num, row_num = initial_data
        for line in f:
            parsed_line = list(map(int, line.split()))
            cost = parsed_line[0]
            mask = 0
            for column_index in parsed_line[2:]:
                mask |= (1 << (column_index - 1))
                
            all_rows.append((cost, mask)) # Store as a tuple

    return all_rows, col_num

def prune_redundant_sets(solution_masks, chosen_indices, target_mask):
    pruned_solution = []
    #pruned_solution = solution_masks
    final_indices = []
    i = 0
    while i < len(solution_masks):
        temp_mask = 0
        
        # Combine all sets EXCEPT the one at index i
        if i == len(solution_masks) - 1: #if we are at the last element, we only combine the pruned solution so far
            for mask in pruned_solution:
                temp_mask |= mask
        else:
            for mask in pruned_solution + solution_masks[i+1:]:
                temp_mask |= mask

        if (temp_mask & target_mask) != target_mask:
            pruned_solution.append(solution_masks[i])
            final_indices.append(chosen_indices[i])
        
        i += 1
    return pruned_solution, final_indices

def meta_raps_set_cover(all_rows, target_mask, p_priority=1.0, iterations=2):
    best_solution = None
    min_cost = float('inf')
    best_indices = []

    for _ in range(iterations):
        covered = 0
        current_solution = []
        chosen_indices = []
        current_cost = float('inf')
        
        # --- Construction Phase ---
        while (covered & target_mask) != target_mask:
            # Calculate gain for all rows not yet in solution
            # Gain = (row_mask & ~covered).bit_count()
            gains = [(index, cost, mask, (mask & ~covered).bit_count()) 
                     for index, (cost, mask) in enumerate(all_rows)]
            
            # Filter rows that actually add something
            valid_candidates = [g for g in gains if g[3] > 0]
            if not valid_candidates: break
            
            # Find the best possible gain per cost
            max_gain = max(c[3]/c[1] for c in valid_candidates)
            
            # Create Candidate List (RCL) based on p_priority
            # Logic: Gain must be >= 90% of the best gain
            rcl = [c for c in valid_candidates if (c[3]/c[1]) >= (max_gain * p_priority)]
            
            # Randomly pick from the RCL
            chosen_index, chosen_cost, chosen_mask, chosen_gain = random.choice(rcl)
            
            covered |= chosen_mask
            current_solution.append(chosen_mask)
            chosen_indices.append(chosen_index)
            current_cost += chosen_cost

        # --- Improvement Phase (Redundancy Check) ---
        current_solution, final_indices = prune_redundant_sets(current_solution, chosen_indices, target_mask)
        #final_indices = chosen_indices
        current_cost = sum(all_rows[i][0] for i in final_indices) # Assuming mask objects have cost
        if current_cost < min_cost:
            min_cost = current_cost
            best_solution = current_solution
            best_indices = final_indices

    return best_solution, min_cost, best_indices

def get_next_instance_number(directory=".",instance_name=""):
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Look for any files matching 'instance.*.sol'
    existing_files = glob.glob(os.path.join(directory, f"{instance_name}.*.sol"))

    if not existing_files:
        return 1

    numbers = []
    for f in existing_files:
        try:
            #file format is always instance.number.sol
            num = int(os.path.basename(f).split('.')[1])
            numbers.append(num)
        except (ValueError, IndexError):
            continue

    nex_num = max(numbers) + 1 if numbers else 1
    assert nex_num > 0

    return nex_num

def save_solution(filename, min_cost, best_indices, time_elapsed):
    with open(filename, 'w') as f:
        f.write(f"{min_cost}\n")
        for ind in best_indices:
            f.write(f"{ind} ")
        f.write(f"\n{time_elapsed}\n")

def check_indices(all_rows, indices):
    covered = 0
    total_cost = 0
    for ind in indices:
        cost, mask = all_rows[ind]
        covered |= mask
        total_cost += cost
    return covered, total_cost

if __name__ == "__main__":
    #sys.argv = ["raw_main.py","instances/rail507"]
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_instance>", file=sys.stderr)
        sys.exit(1)
    
    instance_path = sys.argv[1]
    filename = os.path.basename(instance_path)

    time_start = time.time()
    
    all_rows, col_num = preprocess_instance(instance_path)
    best_solution, min_cost, best_indices = meta_raps_set_cover(all_rows=all_rows, target_mask=(1 << col_num) - 1, p_priority=0.9, iterations=1)
    #cov_check, cost_check = check_indices(all_rows,best_indices)
    #print(cov_check == (1 << col_num) - 1)
    time_end = time.time()
    time_elapsed = time_end - time_start
    print(f"#### Feasible solution of value {min_cost} [time {time_elapsed}]")
    directory_name = "results"
    next_index_number = get_next_instance_number(directory=directory_name, instance_name=filename)
    save_solution(f"{directory_name}/{filename}.{next_index_number}.sol", min_cost=min_cost, best_indices=best_indices, time_elapsed=time_elapsed)