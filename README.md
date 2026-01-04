# Quantum Battleship Hunter

## Overview
This repository contains a Python script that uses the Quantum Zeno Effect (inspired by the Elitzur-Vaidman Bomb Tester thought experiment) to detect battleships in a grid using quantum circuits from Qiskit. The script simulates firing photons in superposition to determine tile contents without detonation, running on a local simulator or IBM Quantum hardware.

* Features:
  * Grid size: 3x3 to 10x10.
  * Battleships: Random or specified.
  * Backend: Aer simulator or IBM hardware (fallback to simulator).
  * Verbose (debug) mode for step-by-step output.
  * Input error handling.
  * Output: Matrices and statistics.

## Requirements
* Python 3.8+
* Qiskit: `pip install qiskit qiskit-aer qiskit-ibm-runtime`
* NumPy: `pip install numpy`

For IBM hardware:
* IBM Quantum account and token: `QiskitRuntimeService.save_account(channel="ibm_quantum", token="YOUR_TOKEN")`.

Backend "ibm_fez" may change; check IBM dashboard.

## Usage
### Command-Line
```
python quantum_zeno_detector.py <grid_size> <battleship_count> <sim_mode>
```
* `<grid_size>`: 3 to 10.
* `<battleship_count>`: 1 to grid_size²; omit for random.
* `<sim_mode>`: 1 for simulator (default), 0 for hardware.

Example:
```
python quantum_zeno_detector.py 5 3 1
```

For help:
```
python quantum_zeno_detector.py info
```

### Interactive
```
python quantum_zeno_detector.py
```
Enter grid size, battleship count (blank for random), simulator (Y/N, blank for yes).

## Output
* Progress: `#` for detected empty tiles, `.` for undetermined.
* Initial grid (hidden truth).
* Detected grid (-1: empty, 1: struck, 0: detected battleship).
* Statistics: Struck, detected, loop runs.

Example for 5x5, 3 battleships:
```
######################...
Initial grid:
[[0. 0. 1. 0. 0.]
 [0. 0. 0. 0. 1.]
 [0. 0. 0. 0. 0.]
 [1. 0. 0. 0. 0.]
 [0. 0. 0. 0. 0.]]

Detected grid:
[[-1. -1.  0. -1. -1.]
 [-1. -1. -1. -1.  0.]
 [-1. -1. -1. -1. -1.]
 [ 0. -1. -1. -1. -1.]
 [-1. -1. -1. -1. -1.]]

Battleships struck: 0.
Battleships detected: 3.
Zeno loop run 512 times.
```

## Code Structure
* `quantum_zeno_detector.py`: Main script (refactored with renamed variables for clarity).
* Tune: `rotation_angle` (small ry rotation), `cycle_count` (Zeno iterations).
* Debug: Set `debug_mode = True` for verbose output (e.g., per-tile probes).

See commented code for detailed breakdown.

## How It Works
The script simulates a quantum-based Battleship game, using the Quantum Zeno Effect to locate battleships (treated as quantum bombs) without detonation. Here's a step-by-step breakdown:

1. **Grid Setup**: The program initializes a square grid (e.g., 5x5) and randomly places the specified number of battleships (or a random count if not provided). Battleships are marked as 1s in a NumPy array, ensuring no overlaps.

2. **Quantum Circuits**:
   * **Battleship Circuit**: For tiles with battleships, the circuit applies a series of small rotations (ry gates) to a qubit, followed by measurements after each rotation. This frequent measurement leverages the Zeno Effect to suppress the qubit's evolution to the |1> state, making "strikes" (measuring |1>) very unlikely. Multiple classical bits record all measurements to detect any strike.
   * **Empty Tile Circuit**: For empty tiles, it applies the same rotations but only measures once at the end, allowing the superposition to build up and increasing the chance of measuring |1>, which confirms the tile is empty.

3. **Probe Loop**: The script repeatedly scans the grid in row-major order. For each undetermined tile (marked as 0 in the detected grid), it runs the appropriate compiled circuit (based on whether it's a battleship or not, though in practice, it simulates this). The loop continues until all empty tiles are identified or all battleships are accounted for (struck or detected by elimination).

4. **Detection Logic**:
   * **Empty Tiles**: If the final measurement is |1>, the tile is marked as -1 (confirmed empty), incrementing the empty count.
   * **Battleship Tiles**: If any measurement during the cycle is |1>, it's a "strike" (marked as 1), simulating a detonation. Otherwise, it's inconclusive (remains 0).
   * **Remaining Tiles**: Once all empty tiles are found, any leftover 0s are inferred as detected battleships (safely located without striking).

The process is probabilistic: Empty detections happen ~10-15% per probe, while strike risks are ~0.01% per probe, tunable via rotation_angle and cycle_count.

## Limitations
* **Simulator**: Uses Qiskit's AerSimulator, which is ideal and noise-free, so results may not reflect real quantum hardware variability.
* **Hardware**: When using IBM Quantum (e.g., "ibm_fez"), noise and errors can affect accuracy; the script falls back to simulator if connection fails. Efficiency is lower on hardware due to no batching of trials.
* **Large Grids**: For bigger grids or fewer battleships, the probabilistic nature may require many probe cycles (potentially thousands), increasing runtime.

## License
MIT License. See LICENSE file for details.
