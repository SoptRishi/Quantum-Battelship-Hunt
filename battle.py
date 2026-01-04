import math
import random
import sys
import numpy as np
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
from qiskit.circuit import QuantumCircuit
from qiskit import transpile
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator

# Configuration parameters
rotation_angle = math.pi / 310  # Small rotation per step in the observation cycle
cycle_count = 30  # Iterations in the observation cycle
max_grid_dim = 10  # Upper limit for grid dimension
min_grid_dim = 3  # Lower limit for grid dimension
debug_mode = False  # Toggle for detailed logging (for troubleshooting)

# Runtime variables
grid_dim = 0
target_count = 0
cell_count = 0
local_sim = None

# Tracking metrics
targets_hit = 0
clear_cells_detected = 0
cycle_executions = 0

# Command-line argument handling
if len(sys.argv) > 1:
    if sys.argv[1] == "info":
        print(f"""This program employs quantum observation principles to identify targets in a matrix without triggering them.
        \nParam 1: matrix dimension ({min_grid_dim}-{max_grid_dim})
        \nParam 2: target quantity (1 to total cells)
        \nParam 3: local simulation (1=yes, 0=no)
        \n""")
        sys.exit(0)
    if len(sys.argv) > 4:
        print("Invalid: Up to 3 params - dimension, targets, sim mode.")
        sys.exit(1)
    try:
        grid_dim = int(sys.argv[1])
        cell_count = grid_dim ** 2
    except ValueError:
        print("Invalid: dimension must be numeric.")
        sys.exit(1)
    if grid_dim < min_grid_dim or grid_dim > max_grid_dim:
        print(f"Invalid: dimension between {min_grid_dim} and {max_grid_dim}.")
        sys.exit(1)
    if len(sys.argv) > 2:
        try:
            target_count = int(sys.argv[2])
        except ValueError:
            print("Invalid: targets must be numeric.")
            sys.exit(1)
        if target_count < 1 or target_count > cell_count:
            print("Invalid: targets 1 to {cell_count}.")
            sys.exit(1)
    else:
        target_count = random.randint(1, cell_count)
    if len(sys.argv) == 4:
        try:
            local_sim = bool(int(sys.argv[3]))
        except ValueError:
            print("Invalid: sim mode 1 or 0.")
            sys.exit(1)
    else:
        local_sim = True

# Interactive input if no args
else:
    while grid_dim == 0:
        try:
            grid_dim = int(input(f"Matrix dimension ({min_grid_dim}-{max_grid_dim}): "))
            if grid_dim < min_grid_dim or grid_dim > max_grid_dim:
                raise ValueError
        except ValueError:
            print("Invalid input, retry.")
            grid_dim = 0
    cell_count = grid_dim ** 2
    while target_count == 0:
        inp = input(f"Target count (1-{cell_count}), blank for random: ")
        if inp == "":
            target_count = random.randint(1, cell_count)
        else:
            try:
                target_count = int(inp)
                if target_count < 1 or target_count > cell_count:
                    raise ValueError
            except ValueError:
                print("Invalid input, retry.")
                target_count = 0
    while local_sim is None:
        inp = input("Local sim? (Y/N, blank=yes): ")
        if inp.lower() in ["y", ""] or not inp:
            local_sim = True
        elif inp.lower() == "n":
            local_sim = False
        else:
            print("Invalid input, retry.")
            local_sim = None

# Initialize matrix for target positions
target_matrix = np.zeros((grid_dim, grid_dim))

# Place targets randomly
placed = 0
while placed < target_count:
    r = random.randint(0, grid_dim - 1)
    col = random.randint(0, grid_dim - 1)
    if target_matrix[r][col] != 1:
        target_matrix[r][col] = 1
        placed += 1

# Matrix for results: -1 clear, 1 hit, 0 unknown (remaining 0s are located targets)
result_matrix = np.zeros((grid_dim, grid_dim))

# Prepare quantum setups
target_qc = QuantumCircuit(1, cycle_count)
clear_qc = QuantumCircuit(1, 1)

# Observation cycle setup
for _ in range(cycle_count):
    target_qc.ry(2 * rotation_angle, 0)
    clear_qc.ry(2 * rotation_angle, 0)
    target_qc.measure(0, _)
clear_qc.measure(0, 0)

# Backend selection
if local_sim:
    sim_backend = AerSimulator()
    comp_target_qc = transpile(target_qc, sim_backend)
    comp_clear_qc = transpile(clear_qc, sim_backend)
else:
    try:
        svc = QiskitRuntimeService()
        hw_backend = svc.backend("ibm_fez")
        print(f"Using hardware: {hw_backend.name}")
        pass_mgr = generate_preset_pass_manager(backend=hw_backend, optimization_level=1)
        comp_target_qc = pass_mgr.run(target_qc)
        comp_clear_qc = pass_mgr.run(clear_qc)
        sampler_inst = SamplerV2(mode=hw_backend)
    except Exception as err:
        print(f"Hardware access failed: {err}")
        print("Using local sim.")
        local_sim = True
        sim_backend = AerSimulator()
        comp_target_qc = transpile(target_qc, sim_backend)
        comp_clear_qc = transpile(clear_qc, sim_backend)

# Function to probe a cell
def probe_cell(has_target):
    global cycle_executions
    cycle_executions += 1
    qc_to_use = comp_target_qc if has_target else comp_clear_qc
    res_mem = exec_quantum(qc_to_use)
    if has_target:
        if '1' in res_mem[0]:
            if debug_mode: print("Impact")
            global targets_hit
            targets_hit += 1
            return 1
    else:
        if res_mem[0][0] == '1':
            if debug_mode: print("Clear")
            global clear_cells_detected
            clear_cells_detected += 1
            return -1
    if debug_mode: print("Undetermined")
    return 0

# Execute quantum circuit
def exec_quantum(qc):
    if local_sim:
        run_res = sim_backend.run(qc, shots=1, memory=True)
        return run_res.result().get_memory()
    else:
        job_res = sampler_inst.run([qc], shots=1)
        bits = job_res.result()[0].data.c.get_bitstrings()
        return bits

if debug_mode:
    print(f"Targets: {target_count}")
    print(f"Matrix: {grid_dim}x{grid_dim}")
    print(f"Cells: {cell_count}")
    print("Target matrix:")
    print(target_matrix)

# Cycle until all clear cells detected or targets hit
while clear_cells_detected + target_count < cell_count:
    for row in range(grid_dim):
        if clear_cells_detected + target_count >= cell_count:
            break
        for col in range(grid_dim):
            if result_matrix[row][col] == 0:
                if debug_mode: print(f"Probing row {row}, col {col}")
                result_matrix[row][col] = probe_cell(bool(target_matrix[row][col]))
                if not debug_mode:
                    print(f"\r" + "#" * clear_cells_detected + "." * (cell_count - clear_cells_detected - target_count), end="")
                if clear_cells_detected + target_count >= cell_count:
                    break

# Results display
print("\n\nTarget matrix:")
print(target_matrix)
print("\nResult matrix:")
print(result_matrix)
targets_hit = np.sum(result_matrix == 1)
print(f"\nTargets hit: {targets_hit}.")
print(f"Targets located: {target_count - targets_hit}.")
print(f"Cycle executions: {cycle_executions}.")
