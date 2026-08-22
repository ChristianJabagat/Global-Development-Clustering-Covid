# Clusters in Crisis

**Author:** Christian Regie Jabagat

This independent exploratory project studies how countries grouped by economic,
social, health, finance, and education indicators before and during COVID-19. It
uses World Bank World Development Indicators for 2019, 2020, and 2021, then
compares country clusters across three periods:

- 2019: Pre-COVID
- 2020: Early COVID
- 2021: Mid-COVID

The exploratory notebook is in `EconClustering_ExploratoryAnalysis.ipynb`. The
reproducible version is implemented as a Python pipeline in
`src/econ_clustering/`.

![PCA cluster scatter](outputs/figures/pca_cluster_scatter.png)

## Key Results

- The reproducible complete-panel analysis retains 115 countries and 18 WDI
  indicators.
- Cluster structure is moderately stable from 2019 to 2020, with pairwise
  co-membership Jaccard of 0.539.
- Stability weakens by 2021, with pairwise co-membership Jaccard around 0.377
  for 2019-2021 and 0.374 for 2020-2021.
- The pipeline reports label-invariant metrics because separately fitted
  clustering models do not guarantee comparable numeric cluster IDs across
  years.

## Project Structure

```text
.
├── EconClustering_ExploratoryAnalysis.ipynb
├── AUTHORS.md
├── README.md
├── data/
│   └── README.md
├── docs/
│   ├── analysis_quality_review.md
│   ├── github_exposition_plan.md
│   └── value_adding_analyses.md
├── outputs/
│   ├── analysis_summary.md
│   ├── figures/
│   └── tables/
├── requirements.txt
├── scripts/
│   ├── download_wdi.py
│   └── run_analysis.py
└── src/
    └── econ_clustering/
        ├── __init__.py
        └── pipeline.py
```

## Reproduce the Analysis

Create an environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Download the WDI data if `WDICSV.csv` is not already present:

```bash
python scripts/download_wdi.py --output-dir .
```

Run the analysis:

```bash
python scripts/run_analysis.py --data WDICSV.csv --output outputs
```

## Outputs

- Latest analysis summary:
  - 115 complete countries retained.
  - 18 indicators retained after missingness filtering.
  - Cluster stability is strongest from 2019 to 2020 by pairwise
    co-membership Jaccard, then weakens by 2021.
- `outputs/analysis_summary.md`: concise reproducibility summary.
- `outputs/tables/clean_panel.csv`: final complete country-year feature panel.
- `outputs/tables/data_quality_summary.csv`: compact audit of retained rows,
  countries, years, and features.
- `outputs/tables/clusters_2019.csv`, `clusters_2020.csv`, `clusters_2021.csv`:
  country-level cluster assignments.
- `outputs/tables/cluster_transitions.csv`: country cluster movement over time.
- `outputs/tables/partition_stability_metrics.csv`: label-invariant stability
  metrics across periods.
- `outputs/tables/cluster_validation_metrics.csv`: internal validation metrics
  for hierarchical clustering, K-Means, and OPTICS.
- `outputs/tables/country_mobility_typology.csv`: peer-retention typology for
  country movement across periods.
- `outputs/tables/cluster_profile_summary.csv`: readable cluster-size,
  example-country, and top-feature summaries.
- `outputs/figures/cluster_transition_heatmap.png`: visual transition overview.
- `outputs/figures/pca_cluster_scatter.png`: PCA cluster scatter plots.
- `outputs/figures/cluster_jaccard_heatmap.png`: cluster membership similarity.
- `outputs/figures/feature_missingness.png`: selected-indicator missingness.
- `outputs/figures/country_mobility_typology.png`: country mobility counts.
- `outputs/figures/top_cluster_features.png`: strongest above-average cluster
  features.

## Notes for GitHub

Do not commit `WDICSV.csv`; it is ignored by `.gitignore`. Commit the code,
README, notebook, and lightweight outputs instead. If you want the repository to
be self-contained, publish the raw data through a release asset, cloud storage,
or Git LFS, then link to it from this README.

See `docs/github_exposition_plan.md` for the recommended polish path before
publishing.

See `docs/value_adding_analyses.md` for the most useful additional sections and
analyses to build next.

See `docs/analysis_quality_review.md` for the correctness and interpretation
boundaries of the current analysis.
