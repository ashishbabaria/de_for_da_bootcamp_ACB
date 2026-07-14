import json
import os
import requests
 
BASE = "https://openlibrary.org/search.json"
FIELDS = "title,author_name,first_publish_year,ratings_average,edition_count"
OFFLINE_FILE = os.path.join("data", "offline_books.json")
HEADERS = {"User-Agent": "booknest-de-bootcamp/1.0"}
 
 
def _load_offline():
    with open(OFFLINE_FILE, "r") as f:
        return json.load(f)
 
 
def get_books(subject, page=1, limit=10):
    """Call the Open Library search API for one page of books on a subject.
    Returns a list of dicts: {title, author, first_publish_year, rating}.
    Falls back to the local offline sample if the API call fails.
    """
    url = f"{BASE}?q={subject}&page={page}&limit={limit}&fields={FIELDS}"
 
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        docs = data.get("docs", [])
    except Exception as error:
        print(f"  (API call failed: {error} -- using offline sample)")
        docs = _load_offline()
 
    books = []
    for d in docs:
        authors = d.get("author_name") or ["Unknown"]
        books.append({
            "title": d.get("title", "Unknown title"),
            "author": authors[0],
            "first_publish_year": d.get("first_publish_year"),
            "rating": d.get("ratings_average"),
        })
    return books
 
 
def main():
    print("Booknest catalogue enrichment\n")
    books = get_books("python", page=1)
    print(f"Got {len(books)} books for subject 'python':\n")
    for b in books[:5]:
        print(f"  {b['title']:<45} by {b['author']:<25} "
              f"({b['first_publish_year']})  rating {b['rating']}")
 
 
if __name__ == "__main__":
    main()