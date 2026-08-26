# Week 2 - Production Python for Data Engineers

Codebasics Data Engineering Bootcamp · Session 4
**Structure · Robustness · Safety**

Side-by-side demo of the same ETL pipeline at two polish levels - so the
difference between "works on a laptop" and "ready for production" is
visible at a glance.

## Folder layout

```
Week 2/
    as-given/      instructor's demo files, unchanged
    enhanced/      same pipeline with light production polish
    README.md      this file
```

## What the pipeline does

A small batch ETL job that processes customer orders:

```
EXTRACT  ->  fetch raw orders (currently fake; in real life a DB or API)
TRANSFORM->  clean messy prices, build Order objects, apply discount
LOAD     ->  save each order with retries on transient failures
```

Production patterns demonstrated across both versions:
- modular package structure (one job per file)
- OOP encapsulation (`Order` class bundles data + behaviour)
- config-driven design (every tunable value in `config.py`)
- structured logging (timestamped, levelled, greppable)
- exception handling (one bad row never kills the whole run)
- retries with backoff (transient failures self-heal)
- secrets from environment (no passwords in source)

## How to run

```bash
# As-given version
cd as-given
python run_pipeline.py

# Enhanced version (notice the exit code at the end)
cd ../enhanced
python run_pipeline.py
```

See each folder's own README for per-version detail. The `enhanced/README.md`
has a side-by-side table of every change vs. `as-given`.

## Why two versions

Code that runs once on a laptop is not production code. The same pipeline
becomes a system you can trust at 2am once it's structured into modules,
emits proper logs, survives bad data, retries flaky calls, and keeps its
secrets outside the source. Keeping both versions in the repo makes the
progression visible - what got added, what got changed, and why.
