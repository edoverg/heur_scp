import time
import glob
import os
import sys
import random
from typing import Tuple, List, Union

def preprocess_instance(instance_path: str) -> Tuple[List[Tuple[int, int]], int]:
    '''Preprocesses the instance file and returns the list of rows and the number of columns.
    Parameters:
        instance_path: Path to the instance file
    Returns:
        Tuple of (all_rows, col_num) where all_rows is a list of (cost, mask) tuples and col_num is the number of columns.'''

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
                
            all_rows.append((cost, mask))

    return all_rows, col_num

def prune_redundant_sets(solution_masks: List[int], chosen_indices: List[int], target_mask: int) -> Tuple[List[int], List[int]]:
    '''Prune redundant sets from the solution. It iterates through the solution and checks if removing a set still covers the target mask.
    If removing a set does not cover the target mask, it is added to the pruned solution and classified as essential. 
    The process continues until all sets have been checked.
    Parameters:
        solution_masks: List of masks in the current solution
        chosen_indices: List of indices corresponding to the current solution masks
        target_mask: Target coverage bitmask
    Returns:
        Tuple of (pruned_solution, final_indices) where pruned_solution is the list of masks 
        after pruning and final_indices is the corresponding list of indices.'''
    pruned_solution = []
    final_indices = []
    i = 0
    while i < len(solution_masks):
        temp_mask = 0
        # Combine all sets except the one at index i
        if i == len(solution_masks) - 1:
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

def try_2_1_swap(all_rows: List[Tuple[int, int]], current_solution: List[int], chosen_indices: List[int]) -> Tuple[List[int], int, List[int]]:
    '''Tries to perform a 2-1 swap on the current solution. It iterates through all pairs of sets in the current solution.
    For each pair, it determines the essential elements covered by these two sets together. Then, it looks for a single
    set in all_rows that can cover the essential elements but has a lower cost than the combined cost the two sets.
    Parameters:
        all_rows: List of (cost, mask) tuples for all sets
        current_solution: List of masks in the current solution
        chosen_indices: List of indices corresponding to the current solution masks
    Returns:
        Tuple of (new_solution, new_cost, new_chosen_indices) after the 2-1 swap'''
    new_solution = current_solution.copy()
    new_chosen_indices = chosen_indices.copy()
    new_cost = sum(all_rows[i][0] for i in chosen_indices)

    for i in range(len(current_solution)):
        for j in range(i+1, len(current_solution)):

            combined_mask = current_solution[i] | current_solution[j]

            #make the or of the other sets except i and j 
            # check what elements are essentially covered by these two sets together
            other_covered = 0
            for k in range(len(current_solution)):
                if k != i and k != j:
                    other_covered |= current_solution[k]
            essential_mask = combined_mask & ~other_covered
            assert essential_mask > 0

            combined_cost = all_rows[chosen_indices[i]][0] + all_rows[chosen_indices[j]][0]

            #from all_rows, find a set that covers the essential_mask and 
            # has a lower cost than the combined one
            for index, (cost, mask) in enumerate(all_rows):
                if (mask & essential_mask) == essential_mask and cost < combined_cost:
                    print(f"Found a better set at index {index} that can replace\
                           sets at indices {chosen_indices[i]} and {chosen_indices[j]}")
                    # Update the solution by replacing the two sets with the new set
                    del new_solution[max(i, j)]
                    del new_solution[min(i, j)]
                    new_solution.append(mask)
                    del new_chosen_indices[max(i, j)]
                    del new_chosen_indices[min(i, j)]  
                    new_chosen_indices.append(index)

                    new_cost = new_cost - combined_cost + cost
                    return new_solution, new_cost, new_chosen_indices
        
    return new_solution, new_cost, new_chosen_indices

def construct_and_improve_solution(all_rows: List[Tuple[int, int]],
                                   current_solution: List[int], 
                                   chosen_indices: List[int], 
                                   covered: int, 
                                   target_mask: int, 
                                   p_priority: float) -> Tuple[List[int], int, List[int]]:
    """
    Randomized greedy construction phase with candidate list and improvement phase (redundancy pruning).
    
    Parameters:
        all_rows: List of (cost, mask) tuples
        current_solution: Current list of masks in the solution
        chosen_indices: Current list of indices corresponding to solution masks
        covered: Current coverage bitmask
        target_mask: Target coverage bitmask
        p_priority: Priority parameter for candidate list (0.0-1.0). 
            It selects candidates that are within p_priority of the best gain-to-cost ratio.
    
    Returns:
        Tuple of (improved_solution, cost, final_indices)
    """
    
    while (covered & target_mask) != target_mask:
        gains = [(index, cost, mask, (mask & ~covered).bit_count()) 
                for index, (cost, mask) in enumerate(all_rows)]
        
        valid_candidates = [g for g in gains if g[3] > 0]
        if not valid_candidates: 
            break
        
        max_gain = max(c[3]/c[1] for c in valid_candidates)
        selected_candidates = [c for c in valid_candidates if (c[3]/c[1]) >= (max_gain * p_priority)]
        
        chosen_index, chosen_cost, chosen_mask, chosen_gain = random.choice(selected_candidates)
        
        covered |= chosen_mask
        current_solution.append(chosen_mask)
        chosen_indices.append(chosen_index)

    current_solution, final_indices = prune_redundant_sets(current_solution, chosen_indices, target_mask)
    current_cost = sum(all_rows[i][0] for i in final_indices)
    
    return current_solution, current_cost, final_indices

def reduced_scp(all_rows: List[Tuple[int, int]], 
                initial_solution: List[int], 
                initial_indices: List[int], 
                initial_cost: int | float, 
                improve_iterations: int, 
                p_priority: float, 
                search_magnitude: float, 
                target_mask: int) -> Tuple[List[int], int | float, List[int]]:
    
    """A reduced Set Cover Problem - it takes as input a feasible solution, removes a random number of sets and attempts
    to reconstruct a better solution.
    Parameters:
        all_rows: List of (cost, mask) tuples for all sets
        initial_solution: List of masks in the initial solution
        initial_indices: List of indices corresponding to the initial solution masks
        initial_cost: Cost of the initial solution
        improve_iterations: Number of iterations to repeat the reduction-construction process
        p_priority: Priority parameter for candidate list (0.0-1.0). 
        search_magnitude: Magnitude (0.0-1.0) of search for reduced SCP. 
            It is the percentage of indices that will be removed from the initial solution.
        target_mask: Target coverage bitmask
    
    Returns:
        Tuple of (best_solution, best_cost, best_indices)
    """
    best_solution = initial_solution.copy()
    best_indices = initial_indices.copy()
    best_cost = initial_cost
    
    for _ in range(improve_iterations):
        reduced_solution = initial_solution.copy()
        reduced_indices = initial_indices.copy()
        
        for _ in range(int(search_magnitude * len(initial_solution))):
            if not reduced_solution:
                break
            remove_index = random.randint(0, len(reduced_solution) - 1)
            del reduced_solution[remove_index]
            del reduced_indices[remove_index]
        
        # Check coverage of reduced solution
        covered = 0
        for mask in reduced_solution:
            covered |= mask
        
        if (covered & target_mask) == target_mask:
            return reduced_solution, sum(all_rows[i][0] for i in reduced_indices), reduced_indices
        
        current_solution, current_cost, final_indices = construct_and_improve_solution(
            all_rows, reduced_solution, reduced_indices, covered, target_mask, p_priority
        )
        
        if current_cost < best_cost:
            best_cost = current_cost
            best_solution = current_solution
            best_indices = final_indices
    
    return best_solution, best_cost, best_indices

def meta_rasp_set_cover(all_rows: List[Tuple[int, int]], 
                        target_mask: int, 
                        covered_input: int = 0, 
                        p_priority: float = 0.9, 
                        iterations: int = 1,
                        run_reduced_scp: bool = False , 
                        run_ls: bool = False) -> Tuple[List[int], int | float, List[int]]:
    '''Entry point for the metaheuristic algorithm. It performs multiple iterations of construction and improvement, 
    followed by an optional reduced SCP phase and local search phase.
    Parameters:
        all_rows: List of (cost, mask) tuples for all sets
        target_mask: Target coverage bitmask
        covered_input: Initial coverage bitmask (default is 0)
        p_priority: Priority parameter for candidate list (0.0-1.0)
        iterations: Number of iterations for the initial randomized greedy construction (repeated start)
        run_reduced_scp: Condition to run the reduced SCP phase (default is False)
        run_ls: Condition to run the local search phase (default is False)
    Returns:
        Tuple of (best_solution, min_cost, best_indices)'''
    best_solution = []
    min_cost = float('inf')
    best_indices = []

    for _ in range(iterations):
        best_solution, min_cost, best_indices = construct_and_improve_solution(
            all_rows, [], [], covered_input, target_mask, p_priority
        )

    print("After initial construction cost is ", min_cost)

    if run_reduced_scp:
        best_solution, min_cost, best_indices = reduced_scp(
            all_rows=all_rows, 
            initial_solution=best_solution, 
            initial_indices=best_indices, 
            initial_cost=min_cost, 
            improve_iterations=5, 
            p_priority=p_priority, 
            search_magnitude=0.2, 
            target_mask=target_mask
        )
    
    print("After reduced SCP, cost is ", min_cost)
    
    if run_ls:
        for _ in range(5):
            best_solution, min_cost, best_indices = try_2_1_swap(
                all_rows=all_rows, 
                current_solution=best_solution, 
                chosen_indices=best_indices
            )
    
    return best_solution, min_cost, best_indices

def get_next_instance_number(directory: str = ".", instance_name: str = "") -> int:
    '''Return the next available solution number for a given instance in the specified directory.
    Parameters:
        directory: The directory where solution files are stored.
        instance_name: The base name of the instance (without the .sol extension).
    Returns:
        next_num: The next available solution number (integer).
    '''
    if not os.path.exists(directory):
        os.makedirs(directory)

    #NOTE: file format is always instance.number.sol
    existing_files = glob.glob(os.path.join(directory, f"{instance_name}.*.sol"))

    if not existing_files:
        return 1

    numbers = []
    for f in existing_files:
        try:
            num = int(os.path.basename(f).split('.')[1])
            numbers.append(num)
        except (ValueError, IndexError):
            continue

    next_num = max(numbers) + 1 if numbers else 1
    assert next_num > 0

    return next_num

def save_solution(filename: str, min_cost: int | float, best_indices: List[int], time_elapsed: float) -> None:
    '''Save the solution to a file in the specified format.
    Parameters:
        filename: The name of the file to save the solution to.
        min_cost: The cost of the solution.
        best_indices: The indices of the chosen sets in the solution.
        time_elapsed: The time taken to find the solution.
    Returns:
        None
    '''
    with open(filename, 'w') as f:
        f.write(f"{min_cost}\n")
        for ind in best_indices:
            f.write(f"{ind} ")
        f.write(f"\n{time_elapsed}\n")
      
if __name__ == "__main__":
    print("Starting the metaheuristic algorithm for Set Cover Problem...")
    #sys.argv = ["raw_main.py","instances/rail507"]
    if len(sys.argv) < 2:
        print("Usage: python raw_main.py <path_to_instance>", file=sys.stderr)
        sys.exit(1)
    
    instance_path = sys.argv[1]
    filename = os.path.basename(instance_path)

    directory_name = "results_final"
    next_index_number = get_next_instance_number(directory=directory_name, instance_name=filename)
    #just create the file to reserve the name
    open(f"{directory_name}/{filename}.{next_index_number}.sol", 'w').close()

    time_start = time.time()
    
    all_rows, col_num = preprocess_instance(instance_path)
    target_mask = (1 << col_num) - 1
    best_solution, min_cost, best_indices = meta_rasp_set_cover(
        all_rows=all_rows, 
        target_mask=target_mask, 
        p_priority=0.9, 
        iterations=1,
        run_reduced_scp=True,
        run_ls=True,
    )

    time_end = time.time()
    time_elapsed = time_end - time_start
    
    print(f"#### Feasible solution of value {min_cost} [time {time_elapsed}]")
    save_solution(f"{directory_name}/{filename}.{next_index_number}.sol", min_cost=min_cost, best_indices=best_indices, time_elapsed=time_elapsed)
    