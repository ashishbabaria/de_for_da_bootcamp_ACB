import pandas as pd
 
SALES_FILE = "data/sales.csv"
CHUNK_SIZE = 50_000
 
 
def stream_revenue_by_genre(path=SALES_FILE, chunksize=CHUNK_SIZE):
    """Loop the file in chunks, accumulate revenue per genre."""
    revenue_by_genre = {}
    rows_seen = 0
 
    for chunk in pd.read_csv(path, chunksize=chunksize):
        rows_seen += len(chunk)
        chunk["revenue"] = chunk["price"] * chunk["quantity"]
        per_chunk = chunk.groupby("genre")["revenue"].sum()
        for genre, amount in per_chunk.items():
            revenue_by_genre[genre] = revenue_by_genre.get(genre, 0) + amount
 
    return revenue_by_genre, rows_seen
 
 
def shrink_memory(chunk):
    """Cast price/rating to float32 and genre/city/payment_type to category."""
    before = chunk.memory_usage(deep=True).sum() / 1024**2
 
    chunk = chunk.copy()
    chunk["price"] = chunk["price"].astype("float32")
    chunk["rating"] = chunk["rating"].astype("float32")
    chunk["genre"] = chunk["genre"].astype("category")
    chunk["city"] = chunk["city"].astype("category")
    chunk["payment_type"] = chunk["payment_type"].astype("category")
 
    after = chunk.memory_usage(deep=True).sum() / 1024**2
    return chunk, before, after
 
 
def main():
    print("Booknest streaming + memory\n")
 
    print(f"Streaming {SALES_FILE} in chunks of {CHUNK_SIZE:,} rows...")
    revenue_by_genre, rows_seen = stream_revenue_by_genre()
    print(f"Streamed {rows_seen:,} rows total (never loaded whole file at once)\n")
 
    print("Revenue by genre:")
    for genre, amount in sorted(revenue_by_genre.items(), key=lambda kv: -kv[1]):
        print(f"  {genre:<12} INR {amount:,.2f}")
 
    print("\nMemory optimisation on one chunk:")
    first_chunk = next(pd.read_csv(SALES_FILE, chunksize=CHUNK_SIZE))
    print("Dtypes before:")
    print(first_chunk.dtypes)
 
    shrunk_chunk, before_mb, after_mb = shrink_memory(first_chunk)
    print(f"\nMemory before: {before_mb:.2f} MB")
    print(f"Memory after:  {after_mb:.2f} MB")
    print(f"Reduction:     {(1 - after_mb / before_mb) * 100:.1f}%")
 
    print("\nDtypes after:")
    print(shrunk_chunk.dtypes)
 
 
if __name__ == "__main__":
    main()