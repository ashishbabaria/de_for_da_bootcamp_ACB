import os
import time
from concurrent.futures import ProcessPoolExecutor
 
GENRES = ["Fiction", "Mystery", "Romance", "Self-Help",
          "Sci-Fi", "Fantasy", "Biography", "History"]
 
TOTAL_CORES = os.cpu_count()
 
 
def score_genre(genre):
    """Pretend heavy scoring work: crunch a lot of numbers for this genre."""
    total = 0
    for i in range(3_000_000):
        total += (i * len(genre)) % 97
    return genre, total
 
 
def run_serial(genres):
    return [score_genre(g) for g in genres]
 
 
def run_parallel(genres):
    with ProcessPoolExecutor(max_workers=TOTAL_CORES) as pool:
        return list(pool.map(score_genre, genres))
 
 
def main():
    print("Booknest serial vs parallel")
    print(f"CPU cores available: {TOTAL_CORES}\n")
 
    print("SERIAL (1 core):")
    start = time.perf_counter()
    serial_results = run_serial(GENRES)
    serial_time = time.perf_counter() - start
    print(f"  time taken: {serial_time:.2f}s")
 
    print("\nPARALLEL (all cores):")
    start = time.perf_counter()
    parallel_results = run_parallel(GENRES)
    parallel_time = time.perf_counter() - start
    print(f"  time taken: {parallel_time:.2f}s")
 
    serial_sorted = sorted(serial_results)
    parallel_sorted = sorted(parallel_results)
    match = serial_sorted == parallel_sorted
    print(f"\nResults identical: {match}")
    print(f"Serial:   {serial_time:.2f}s")
    print(f"Parallel: {parallel_time:.2f}s")
    if TOTAL_CORES and TOTAL_CORES > 1:
        print(f"Machine has {TOTAL_CORES} cores -> parallel is expected to win.")
    else:
        print("Machine has 1 core -> parallel won't show a speedup here.")
 
 
if __name__ == "__main__":
    main()