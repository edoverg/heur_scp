import glob
import os
import sys

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python make_csv.py <output_csv> <results_directory> <instance_name>...", file=sys.stderr)
        sys.exit(1)
    
    output_csv_path = sys.argv[1]
    results_directory_path = sys.argv[2]
    instance_list = sys.argv[3:]
    
    min_cost = float('inf')
    time_elapsed = 0.0

    for instance_name in instance_list:
        existing_files = glob.glob(os.path.join(results_directory_path, f"{instance_name}.*.sol"))
        for solution_file in existing_files:
            with open(solution_file, 'r') as f:
                lines = f.readlines()
                if len(lines) < 2:
                    continue
                try:
                    cost = float(lines[0].strip())
                    time_taken = float(lines[-1].strip())
                    if cost < min_cost:
                        min_cost = cost
                        time_elapsed = time_taken
                except ValueError:
                    continue

        if not os.path.exists(output_csv_path):
            with open(output_csv_path, 'w') as f:
                f.write("instance_name,min_cost,time_elapsed\n")
                f.write(f"{instance_name},{int(min_cost)},{time_elapsed}\n")
        else:
            with open(output_csv_path, 'a') as f:
                f.write(f"{instance_name},{int(min_cost)},{time_elapsed}\n")