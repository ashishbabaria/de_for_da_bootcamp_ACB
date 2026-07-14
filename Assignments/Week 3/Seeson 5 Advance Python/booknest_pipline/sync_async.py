import asyncio
import time
import requests
 
BASE = "https://openlibrary.org/search.json"
SUBJECTS = ["python", "data engineering", "sql", "machine learning", "spark", "pandas"]
HEADERS = {"User-Agent": "booknest-de-bootcamp/1.0"}
 
 
def fetch_count(subject):
    """One blocking request: how many results exist for this subject."""
    url = f"{BASE}?q={subject}&limit=1&fields=title"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return subject, resp.json().get("numFound", 0)
    except Exception as error:
        return subject, f"(failed: {error})"
 
 
def fetch_sync(subjects):
    results = []
    for s in subjects:
        results.append(fetch_count(s))
    return results
 
 
async def fetch_one_async(subject):
    # requests is blocking, so hand it to a thread and await it there
    return await asyncio.to_thread(fetch_count, subject)
 
 
async def fetch_all_async(subjects):
    tasks = [fetch_one_async(s) for s in subjects]
    return await asyncio.gather(*tasks)
 
 
def main():
    print("Booknest sync vs async\n")
 
    print("SYNC (one at a time):")
    start = time.perf_counter()
    sync_results = fetch_sync(SUBJECTS)
    sync_time = time.perf_counter() - start
    for subject, count in sync_results:
        print(f"  {subject:<20} -> {count}")
    print(f"SYNC time: {sync_time:.2f}s\n")
 
    print("ASYNC (all together):")
    start = time.perf_counter()
    async_results = asyncio.run(fetch_all_async(SUBJECTS))
    async_time = time.perf_counter() - start
    for subject, count in async_results:
        print(f"  {subject:<20} -> {count}")
    print(f"ASYNC time: {async_time:.2f}s\n")
 
    print(f"Summary: sync {sync_time:.2f}s vs async {async_time:.2f}s "
          f"across {len(SUBJECTS)} calls")
 
 
if __name__ == "__main__":
    main()