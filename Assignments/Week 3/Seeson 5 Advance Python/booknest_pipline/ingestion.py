from get_books import get_books
 
PAGE_CAP = 5  # sensible cap so we never page forever

 
def full_load(subject):
    """Page through a subject until an empty page or PAGE_CAP is hit."""
    all_books = []
    page = 1
    while page <= PAGE_CAP:
        books = get_books(subject, page=page)
        if not books:
            break
        all_books.extend(books)
        print(f"  ... pulled page {page}, running total {len(all_books)}")
        page += 1
    return all_books
 
 
def incremental_load(subject, watermark):
    """Pretend this is tomorrow's run: only keep books newer than watermark."""
    books = get_books(subject, page=1)
    new_books = [b for b in books if (b["first_publish_year"] or 0) > watermark]
    return new_books
 
 
def main():
    print("Booknest ingestion - task 2\n")
 
    subject = "python"
    print(f"FULL LOAD for subject='{subject}' (cap {PAGE_CAP} pages):")
    all_books = full_load(subject)
    print(f"FULL LOAD complete: {len(all_books)} books pulled\n")
 
    years = [b["first_publish_year"] for b in all_books if b["first_publish_year"]]
    watermark = max(years) if years else 0
    print(f"Watermark set to newest first_publish_year seen: {watermark}")
 
    print(f"\nINCREMENTAL next run (only books newer than {watermark}):")
    new_books = incremental_load(subject, watermark)
    print(f"  {len(new_books)} new books would be pulled "
          f"(out of {len(all_books)} in a full load)")
    for b in new_books[:5]:
        print(f"   - {b['title']} ({b['first_publish_year']})")
 
 
if __name__ == "__main__":
    main()