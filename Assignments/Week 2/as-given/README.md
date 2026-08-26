# as-given/

The Session 04 demo files as shared by the instructor, unchanged.

## Layout

```
as-given/
    run_pipeline.py        the runner (extract -> transform -> load)
    requirements.txt       no external packages needed
    online_store/          the package
        __init__.py
        config.py          settings in one place
        models.py          the Order class
        extract.py         pull orders in    (E)
        transform.py       clean and build   (T)
        load.py            save orders out   (L)
```

## Run it

From the `as-given/` folder:

```bash
python run_pipeline.py
```

Expected: three orders are processed. Order 103 has a `None` price for one
item; the pipeline logs a warning and skips it instead of crashing.
The save step is deliberately flaky (succeeds about 70% of the time), so you
will see retries and occasionally a "gave up" line. Run a few times to see
different paths.

## Why this folder exists

This is the baseline. The `../enhanced/` folder has the same pipeline with
light production polish applied, so you can diff the two side by side and
see exactly what production hardening adds.
