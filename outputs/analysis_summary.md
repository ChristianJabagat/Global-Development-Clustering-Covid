# Analysis Summary

- Complete countries retained: 115
- Years analyzed: 2019, 2020, 2021
- Features retained after missingness filtering: 18

## Hierarchical Cluster Sizes
- Pre-COVID (2019): C0: 47, C1: 64, C2: 4
- Early COVID (2020): C0: 67, C1: 45, C2: 3
- Mid-COVID (2021): C0: 56, C1: 2, C2: 34, C3: 23

## Label-Invariant Stability Metrics
- Pre-COVID to Early COVID: ARI=0.423, NMI=0.390, pairwise Jaccard=0.539
- Pre-COVID to Mid-COVID: ARI=0.235, NMI=0.389, pairwise Jaccard=0.377
- Early COVID to Mid-COVID: ARI=0.222, NMI=0.368, pairwise Jaccard=0.374

Adjusted Rand Index, Normalized Mutual Information, and pairwise co-membership
Jaccard compare partitions without assuming that numeric cluster labels are aligned
across years.

## Country Mobility Typology
- moderate mobility: 91
- high mobility: 22
- persistent mover: 2

Country mobility is based on same-cluster peer-group retention, not raw
numeric cluster IDs.
