## Object model

| Object | Type | Points at | Purpose |
|---|---|---|---|
| `LS_StayNest_Storage` | Linked service (Azure Blob Storage) | the storage account | the one reusable connection every dataset uses |
| `ds_source` | DelimitedText dataset | `raw/hotels.csv` | Copy source |
| `ds_sink` | DelimitedText dataset | `bronze/hotels.csv` | Copy sink |
| `ds_raw_folder` | DelimitedText dataset | `raw/` (no file name) | folder handle for Get Metadata |
| `ds_raw_file` *(stretch)* | parameterised DelimitedText | `raw/@{fileName}` | source in the loop |
| `ds_bronze_file` *(stretch)* | parameterised DelimitedText | `bronze/@{fileName}` | sink in the loop |

## Pipelines

**`PL_Copy_Hotels`** (graded)
- **Copy** `Copy_hotels_raw_to_bronze`: `ds_source` → `ds_sink`. Lands `hotels.csv` in `bronze`.
- **Get Metadata** `GetMeta_raw_folder`: reads `ds_raw_folder`, field list = `childItems`.
  Output lists the three files in `raw` (`hotels.csv`, `customers.csv`, `bookings.csv`).

**`PL_Copy_AllFiles`** (optional stretch)
- **Get Metadata** (`childItems`) → **ForEach** over `@activity('GetMeta_raw_folder').output.childItems`
  → inside, a **Copy** whose source/sink file name is `@item().name`.
  One pipeline moves every file in `raw`; dropping a fourth file in needs no changes.

## The object model, in one sentence

Read top-down as a sentence: a **trigger** decides when a **pipeline** runs; the
pipeline is a sequence of **activities**; each activity reads or writes a **dataset**;
the dataset connects through a **linked service**; and the **integration runtime** is
where the work actually runs. This build uses five of the six pieces:

| Piece | In this build |
|---|---|
| Trigger | none — run on demand with **Debug** (a schedule trigger would be the next step) |
| Pipeline | `PL_Copy_Hotels` (and `PL_Copy_AllFiles` for the loop) |
| Activity | Copy (move data) + Get Metadata (control/inspect) |
| Dataset | `ds_source`, `ds_sink`, `ds_raw_folder` (+ parameterised `ds_raw_file` / `ds_bronze_file`) |
| Linked service | `LS_StayNest_Storage` |
| Integration runtime | AutoResolveIntegrationRuntime (Azure-hosted, the default) |

## How to run

1. Open the Data Factory Studio, open `PL_Copy_Hotels`.
2. Click **Debug**. Wait for both activities to go green in the run output.
3. Check storage: `staynest/bronze/hotels.csv` now exists.
4. Click the **Get Metadata** activity's output icon to see the `childItems` list.

## Authentication note

The linked service uses the Data Factory's **system-assigned managed identity**
(granted *Storage Blob Data Contributor* on the storage account), so no key or
connection string is stored in this repo. **Never commit a storage key or connection
string.**

## Two things to be ready to explain (graded on understanding)

**Why one parameterised dataset beats forty hard-coded ones.** A dataset is a
*shape*, not a file. `ds_raw_file` takes a `fileName` parameter and resolves its path
at runtime with `@dataset().fileName`, so the same object copies `hotels.csv`,
`customers.csv`, `bookings.csv`, or anything dropped in later. Hard-coding one dataset
per file means every new file type is a new dataset, a new copy step, and a redeploy —
the metadata-driven loop scales to N files with zero new objects.

**Why Data Factory hands heavy work to Databricks / SQL.** ADF is first an
*orchestrator*: it connects to sources, moves bytes, and schedules the work. Its
Copy/Mapping Data Flow can do light transforms, but Data Flows spin up a Spark cluster
under the hood and bill for it, and complex logic is easier to express, test, and
version in Databricks (PySpark) or SQL. So the pattern is: ADF moves and coordinates;
compute engines do the transformation. Right tool for each job, and cheaper.