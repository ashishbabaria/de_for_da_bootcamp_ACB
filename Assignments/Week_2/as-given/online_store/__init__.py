"""
online_store  -  a PACKAGE for our Session 03 pipeline.

WHAT IS A PACKAGE?
A package is simply a FOLDER of modules (.py files) that has this special
file, __init__.py, inside it. The moment a folder has __init__.py, Python
treats it as a package you can import from, like:

    from online_store.extract import fetch_todays_orders

WHAT IS A MODULE?
A module is one .py file. Each module here does exactly ONE job:

    config.py     ->  all settings in one place
    models.py     ->  the Order class (object oriented design)
    extract.py    ->  pull raw orders IN          (the "E" in ETL)
    transform.py  ->  clean data, build Orders     (the "T" in ETL)
    load.py       ->  save the orders OUT          (the "L" in ETL)

The runner script run_pipeline.py (one folder up) imports from these
modules and runs them in order: extract -> transform -> load.

This __init__.py can stay almost empty. It only marks the folder as a package.
"""
