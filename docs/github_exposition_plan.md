# GitHub Exposition Plan

## Current State

The notebook has a meaningful exploratory research question: whether
economic-development clusters shifted during the COVID-19 period. The folder now
also contains a reproducible Python pipeline that exports lightweight tables and
figures for GitHub.

## Issues Found

- `WDICSV.csv` is about 161 MB, which is too large for a normal GitHub commit.
  It should stay ignored and be downloaded locally or hosted as a release asset.
- The notebook defines `plot_cluster_heatmap` twice. The second definition
  overwrites the first and returns only 2020-2021 columns, while later code
  expects a `Pre-COVID` column.
- The notebook depends on `world-administrative-boundaries/*.shp`, but that
  shapefile is not present in this folder.
- `lime` is imported in the notebook but is not installed in the current Python
  environment.
- The original overall Jaccard calculation compares numeric cluster labels
  directly. Cluster labels are arbitrary across separate clustering runs, so the
  reproducible pipeline adds label-invariant metrics.

## What To Push

Commit these:

- `README.md`
- `AUTHORS.md`
- `EconClustering_ExploratoryAnalysis.ipynb`
- `requirements.txt`
- `docs/analysis_quality_review.md`
- `data/README.md`
- `docs/github_exposition_plan.md`
- `docs/value_adding_analyses.md`
- `scripts/`
- `src/`
- `outputs/analysis_summary.md`
- `outputs/figures/`
- `outputs/tables/`

Do not commit these:

- `WDICSV.csv`
- `WDI_CSV.zip`
- `.DS_Store`
- local virtual environments
- missing or experimental shapefile folders unless you intentionally add a
  complete, licensed geospatial dataset

## Recommended Repository Story

Use the README as the first impression, with the notebook as the detailed
exploratory analysis and the pipeline as the reproducible implementation. A good
GitHub description would be:

> Clustering World Bank development indicators to examine how country economic
> groupings shifted across 2019, 2020, and 2021.

## Next Polish Steps

1. Add a short abstract figure near the top of `README.md`, likely
   `outputs/figures/pca_cluster_scatter.png`.
2. Decide whether the map section should be restored. If yes, add a reproducible
   geospatial data source and document its license.
3. Convert the exploratory notebook into a `notebooks/` version that calls
   `src/econ_clustering/pipeline.py` instead of duplicating logic.
4. Add a small GitHub Actions workflow that runs `python -m py_compile` and the
   pipeline when data is available.
5. Create a release and attach the raw WDI CSV or link to the official World
   Bank download page.
