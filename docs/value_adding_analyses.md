# Value-Adding Analyses

These are the strongest additions if the goal is to turn the exploratory
analysis into a portfolio-ready GitHub project.

## 1. Executive Findings Section

Add a short section before the methodology that answers:

- What changed from 2019 to 2021?
- Which clusters were stable?
- Which countries moved?
- What indicators explain those moves?

This makes the project easier for recruiters, exposition judges, or technical
reviewers to understand without reading the full notebook.

## 2. Data Quality and Missingness Audit

Status: implemented in `outputs/tables/data_quality_summary.csv`,
`outputs/tables/feature_missingness.csv`, and
`outputs/figures/feature_missingness.png`.

Add a short discussion showing:

- which WDI indicators were removed because of missingness;
- how many countries remained after filtering;
- what kinds of countries may be excluded by complete-case filtering.

This improves credibility because WDI data coverage is uneven across countries.

## 3. Sensitivity Analysis

Rerun clustering under alternative preprocessing choices:

- complete-case filtering versus median or KNN imputation;
- 60%, 70%, and 80% feature-availability thresholds;
- alternative hierarchical distance thresholds;
- optional winsorization of extreme indicator values.

This answers whether the conclusions are stable or dependent on one cleaning
choice.

## 4. Cluster Validation Section

Status: implemented in `outputs/tables/cluster_validation_metrics.csv`.

Use the method-comparison table to discuss:

- silhouette score;
- Davies-Bouldin index;
- Calinski-Harabasz index;
- number of clusters;
- interpretability notes.

The current pipeline already exports K-Means metrics. This section would make
the choice of hierarchical clustering more persuasive.

## 5. Label-Invariant Transition Analysis

Keep and expand the new stability metrics:

- Adjusted Rand Index;
- Normalized Mutual Information;
- pairwise co-membership Jaccard;
- cluster-to-cluster Jaccard heatmap.

This is one of the most important upgrades because numeric cluster labels are
arbitrary across years.

## 6. Country Mobility Typology

Status: implemented in `outputs/tables/country_mobility_typology.csv` and
`outputs/figures/country_mobility_typology.png`.

The table classifies countries into:

- stable countries;
- temporary movers that returned near their original peer group;
- persistent movers that remained structurally reclassified;
- outlier countries.

This turns the analysis from abstract clusters into an interpretable global
story.

## 7. Cluster Profile Cards

Status: implemented as `outputs/tables/cluster_profile_summary.csv`.

For each year and cluster, the profile includes:

- cluster size;
- top above-average indicators;
- top below-average indicators;
- example countries;
- suggested descriptive label.

This is clearer than relying only on boxplots.

## 8. Explainability Upgrade

Replace or supplement LIME with a reproducible global feature-importance
section:

- Random Forest or XGBoost trained to predict cluster labels;
- permutation importance;
- SHAP summary plots if dependencies are available.

This gives a stronger explanation of which indicators separate clusters.

## 9. Geographic Analysis

Restore the map only if the geospatial file is complete and licensed. Useful map
outputs would include:

- cluster maps by year;
- transition map for movers versus stable countries;
- regional summaries by continent or World Bank region.

This is high value visually, but only if the shapefile dependency is fixed.

## 10. Limitations and Interpretation Boundaries

Add a section that explicitly states:

- clustering reveals structural similarity, not causality;
- WDI indicators are not COVID policy-response variables;
- independent yearly clustering cannot prove a direct pandemic effect;
- missingness and outliers can influence cluster formation.

This makes the project more analytically mature and protects the claims from
overreach.

## Best Next Build Order

1. Add the executive findings section.
2. Convert the implemented cluster-profile summary into polished README cards.
3. Add sensitivity analysis.
4. Add an explainability upgrade with permutation importance or SHAP.
5. Add a limitations section to the notebook and README.
6. Restore maps only after fixing the geospatial data source.
