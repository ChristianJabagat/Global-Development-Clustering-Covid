"""Reproducible WDI economic clustering analysis.

This module turns the exploratory notebook into a scriptable pipeline:
load selected World Development Indicators, build a complete 2019-2021 panel,
cluster each year, and export the analysis tables and figures.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import os
from pathlib import Path
import tempfile
from textwrap import wrap

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(tempfile.gettempdir()) / "econ_clustering_matplotlib"),
)
os.environ.setdefault(
    "XDG_CACHE_HOME",
    str(Path(tempfile.gettempdir()) / "econ_clustering_cache"),
)
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import AgglomerativeClustering, KMeans, OPTICS
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler


YEARS = (2019, 2020, 2021)
PERIOD_NAMES = {
    2019: "Pre-COVID",
    2020: "Early COVID",
    2021: "Mid-COVID",
}

INDICATORS = {
    "Education": [
        "SE.SEC.NENR",
        "SE.SEC.ENRL.TC.ZS",
        "SE.XPD.CTOT.ZS",
        "SE.XPD.PRIM.ZS",
        "SE.XPD.SECO.ZS",
        "SE.XPD.TERT.ZS",
    ],
    "Health": [
        "SH.XPD.CHEX.GD.ZS",
        "SH.XPD.GHED.GD.ZS",
        "SH.MED.BEDS.ZS",
        "SH.MED.PHYS.ZS",
        "SH.UHC.NOP2.ZS",
        "SH.XPD.GHED.CH.ZS",
        "SH.XPD.PVTD.CH.ZS",
    ],
    "Social protection and outcomes": [
        "SI.POV.LMIC",
        "SI.POV.MDIM",
        "SI.POV.GINI",
        "SL.UEM.TOTL.ZS",
        "HD.HCI.OVRL",
        "SE.TER.ENRR",
        "SL.EMP.SELF.ZS",
        "EN.POP.DNST",
        "SE.PRM.ENRR",
        "SE.SEC.ENRR",
    ],
    "Public finance": [
        "GC.DOD.TOTL.GD.ZS",
        "DT.TDS.DPPG.GN.ZS",
        "GC.TAX.TOTL.GD.ZS",
    ],
    "Monetary and financial systems": [
        "FB.BNK.CAPA.ZS",
        "FD.RES.LIQU.AS.ZS",
        "FB.AST.NPER.ZS",
        "FR.INR.RINR",
        "FI.RES.TOTL.DT.ZS",
    ],
    "Economic fitness": [
        "NY.GDP.MKTP.KD.ZG",
        "NE.GDI.TOTL.ZS",
        "NE.EXP.GNFS.ZS",
        "NE.IMP.GNFS.ZS",
        "BX.KLT.DINV.WD.GD.ZS",
        "GC.XPN.TOTL.GD.ZS",
        "DT.DOD.DSTC.ZS",
        "BX.TRF.PWKR.DT.GD.ZS",
    ],
    "Industry composition and productivity": [
        "NV.AGR.TOTL.ZS",
        "NV.IND.MANF.ZS",
        "NV.SRV.TOTL.ZS",
        "SL.TLF.ACTI.ZS",
    ],
}

EXCLUDED_COUNTRIES = [
    "Africa Eastern and Southern",
    "Africa Western and Central",
    "Arab World",
    "Caribbean small states",
    "Central Europe and the Baltics",
    "Early-demographic dividend",
    "East Asia & Pacific",
    "East Asia & Pacific (excluding high income)",
    "East Asia & Pacific (IDA & IBRD countries)",
    "Euro area",
    "Europe & Central Asia",
    "Europe & Central Asia (excluding high income)",
    "Europe & Central Asia (IDA & IBRD countries)",
    "European Union",
    "Fragile and conflict affected situations",
    "Heavily indebted poor countries (HIPC)",
    "High income",
    "IBRD only",
    "IDA & IBRD total",
    "IDA blend",
    "IDA only",
    "IDA total",
    "Late-demographic dividend",
    "Latin America & Caribbean",
    "Latin America & Caribbean (excluding high income)",
    "Latin America & the Caribbean (IDA & IBRD countries)",
    "Least developed countries: UN classification",
    "Low & middle income",
    "Low income",
    "Lower middle income",
    "Middle East & North Africa",
    "Middle East & North Africa (excluding high income)",
    "Middle East & North Africa (IDA & IBRD countries)",
    "Middle income",
    "North America",
    "OECD members",
    "Other small states",
    "Pacific island small states",
    "Post-demographic dividend",
    "Pre-demographic dividend",
    "Small states",
    "South Asia",
    "South Asia (IDA & IBRD)",
    "Sub-Saharan Africa",
    "Sub-Saharan Africa (excluding high income)",
    "Sub-Saharan Africa (IDA & IBRD countries)",
    "Upper middle income",
    "World",
]

# These thresholds reproduce the exploratory notebook's dendrogram choices.
HIERARCHICAL_DISTANCE_THRESHOLDS = {
    2019: 18,
    2020: 20,
    2021: 15,
}
KMEANS_CLUSTERS = {2019: 3, 2020: 3, 2021: 3}
OPTICS_EPS = {2019: 4, 2020: 5, 2021: 5}


@dataclass(frozen=True)
class YearResult:
    year: int
    period: str
    raw_features: pd.DataFrame
    scaled_features: pd.DataFrame
    clusters: pd.DataFrame
    pca: pd.DataFrame


def _indicator_codes(indicators: dict[str, list[str]] = INDICATORS) -> list[str]:
    return [code for codes in indicators.values() for code in codes]


def load_wdi_panel(
    csv_path: Path,
    years: tuple[int, ...] = YEARS,
    indicators: dict[str, list[str]] = INDICATORS,
    exclude_countries: list[str] = EXCLUDED_COUNTRIES,
    min_feature_availability: float = 0.70,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load, filter, and pivot WDI data into a country-year panel."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Could not find {csv_path}. See data/README.md for download steps."
        )

    year_columns = [str(year) for year in years]
    usecols = ["Country Name", "Country Code", "Indicator Name", "Indicator Code"]
    usecols += year_columns
    raw = pd.read_csv(csv_path, usecols=usecols)

    indicator_lookup = {
        code for code in _indicator_codes(indicators)
    }
    filtered = raw[raw["Indicator Code"].isin(indicator_lookup)].copy()
    filtered = filtered[~filtered["Country Name"].isin(exclude_countries)]
    filtered = filtered[~filtered["Country Name"].str.contains("World", na=False)]

    for year in year_columns:
        filtered[year] = pd.to_numeric(filtered[year], errors="coerce")

    long = filtered.melt(
        id_vars=["Country Name", "Country Code", "Indicator Name", "Indicator Code"],
        value_vars=year_columns,
        var_name="Year",
        value_name="Value",
    )
    panel = long.pivot_table(
        index=["Country Name", "Country Code", "Year"],
        columns="Indicator Name",
        values="Value",
        aggfunc="first",
    ).reset_index()
    panel["Year"] = panel["Year"].astype(int)
    panel.columns.name = None

    feature_columns = [c for c in panel.columns if c not in {"Country Name", "Country Code", "Year"}]
    missing_report = (
        panel[feature_columns]
        .isna()
        .mean()
        .sort_values(ascending=False)
        .rename("missing_share")
        .reset_index()
        .rename(columns={"index": "feature"})
    )

    min_non_null = int(np.ceil(min_feature_availability * len(panel)))
    panel = panel.dropna(axis=1, thresh=min_non_null)
    panel = panel.dropna(axis=0, how="any")

    country_counts = panel["Country Name"].value_counts()
    complete_countries = country_counts[country_counts == len(years)].index
    panel = panel[panel["Country Name"].isin(complete_countries)].copy()
    panel = panel.sort_values(["Country Name", "Year"]).reset_index(drop=True)
    return panel, missing_report


def summarize_data_quality(panel: pd.DataFrame, missing_report: pd.DataFrame) -> pd.DataFrame:
    """Build a compact audit trail for the final modeling dataset."""
    retained_features = len(panel.columns) - 3
    removed_features = int((missing_report["missing_share"] > 0.30).sum())
    complete_countries = panel["Country Name"].nunique()
    rows = [
        ("complete_countries", complete_countries),
        ("years", panel["Year"].nunique()),
        ("country_year_rows", len(panel)),
        ("retained_features", retained_features),
        ("features_above_30pct_missing_before_filter", removed_features),
        ("minimum_year", int(panel["Year"].min())),
        ("maximum_year", int(panel["Year"].max())),
    ]
    return pd.DataFrame(rows, columns=["metric", "value"])


def _year_feature_frame(panel: pd.DataFrame, year: int) -> pd.DataFrame:
    frame = panel[panel["Year"] == year].drop(columns=["Year", "Country Code"])
    return frame.set_index("Country Name").sort_index()


def analyze_year(panel: pd.DataFrame, year: int) -> YearResult:
    """Scale one year of data, cluster it, and build PCA coordinates."""
    raw_features = _year_feature_frame(panel, year)
    scaler = StandardScaler()
    scaled_values = scaler.fit_transform(raw_features)
    scaled_features = pd.DataFrame(
        scaled_values,
        index=raw_features.index,
        columns=raw_features.columns,
    )

    hc = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=HIERARCHICAL_DISTANCE_THRESHOLDS[year],
        linkage="ward",
    )
    kmeans = KMeans(n_clusters=KMEANS_CLUSTERS[year], random_state=42, n_init=20)
    optics = OPTICS(
        min_samples=max(2, min(len(scaled_features.columns), len(scaled_features) - 1)),
        eps=OPTICS_EPS[year],
        metric="minkowski",
    )

    clusters = pd.DataFrame(index=scaled_features.index)
    clusters["Hierarchical Cluster"] = hc.fit_predict(scaled_features)
    clusters["K-Means Cluster"] = kmeans.fit_predict(scaled_features)
    clusters["OPTICS Cluster"] = optics.fit_predict(scaled_features)
    clusters = clusters.reset_index()
    clusters.insert(1, "Year", year)
    clusters.insert(2, "Period", PERIOD_NAMES[year])

    pca = PCA(n_components=2, random_state=42)
    pca_values = pca.fit_transform(scaled_features)
    pca_df = pd.DataFrame(
        pca_values,
        index=scaled_features.index,
        columns=["PC1", "PC2"],
    )
    pca_df["Hierarchical Cluster"] = clusters.set_index("Country Name")[
        "Hierarchical Cluster"
    ]
    pca_df["explained_variance_pc1"] = pca.explained_variance_ratio_[0]
    pca_df["explained_variance_pc2"] = pca.explained_variance_ratio_[1]
    pca_df = pca_df.reset_index()
    pca_df.insert(1, "Year", year)
    pca_df.insert(2, "Period", PERIOD_NAMES[year])

    return YearResult(
        year=year,
        period=PERIOD_NAMES[year],
        raw_features=raw_features,
        scaled_features=scaled_features,
        clusters=clusters,
        pca=pca_df,
    )


def evaluate_kmeans_grid(
    scaled_features: pd.DataFrame,
    year: int,
    min_clusters: int = 2,
    max_clusters: int = 12,
) -> pd.DataFrame:
    rows = []
    upper = min(max_clusters, len(scaled_features) - 1)
    for k in range(min_clusters, upper + 1):
        labels = KMeans(n_clusters=k, random_state=42, n_init=20).fit_predict(scaled_features)
        rows.append(
            {
                "Year": year,
                "Period": PERIOD_NAMES[year],
                "k": k,
                "silhouette": silhouette_score(scaled_features, labels),
                "davies_bouldin": davies_bouldin_score(scaled_features, labels),
                "calinski_harabasz": calinski_harabasz_score(scaled_features, labels),
            }
        )
    return pd.DataFrame(rows)


def _safe_cluster_scores(
    scaled_features: pd.DataFrame,
    labels: pd.Series | np.ndarray,
) -> dict[str, float | int]:
    """Return validation scores when the label structure makes them meaningful."""
    labels = pd.Series(labels)
    non_noise = labels != -1
    usable_labels = labels[non_noise]
    usable_features = scaled_features.loc[non_noise.to_numpy()]
    n_clusters = usable_labels.nunique()

    if n_clusters < 2 or n_clusters >= len(usable_labels):
        return {
            "n_clusters": int(n_clusters),
            "noise_points": int((labels == -1).sum()),
            "silhouette": np.nan,
            "davies_bouldin": np.nan,
            "calinski_harabasz": np.nan,
        }

    return {
        "n_clusters": int(n_clusters),
        "noise_points": int((labels == -1).sum()),
        "silhouette": silhouette_score(usable_features, usable_labels),
        "davies_bouldin": davies_bouldin_score(usable_features, usable_labels),
        "calinski_harabasz": calinski_harabasz_score(usable_features, usable_labels),
    }


def cluster_validation_metrics(year_results: dict[int, YearResult]) -> pd.DataFrame:
    """Compare the fitted clustering methods using standard internal metrics."""
    rows = []
    method_columns = {
        "Hierarchical": "Hierarchical Cluster",
        "K-Means": "K-Means Cluster",
        "OPTICS": "OPTICS Cluster",
    }
    for year, result in year_results.items():
        labels_by_country = result.clusters.set_index("Country Name")
        for method, column in method_columns.items():
            scores = _safe_cluster_scores(result.scaled_features, labels_by_country[column])
            rows.append(
                {
                    "Year": year,
                    "Period": PERIOD_NAMES[year],
                    "Method": method,
                    **scores,
                }
            )
    return pd.DataFrame(rows)


def build_transition_table(year_results: dict[int, YearResult]) -> pd.DataFrame:
    transition = None
    for year, result in year_results.items():
        labels = result.clusters[["Country Name", "Hierarchical Cluster"]].copy()
        labels = labels.rename(columns={"Hierarchical Cluster": PERIOD_NAMES[year]})
        transition = labels if transition is None else transition.merge(labels, on="Country Name")
    return transition.set_index("Country Name").sort_values(list(PERIOD_NAMES.values()))


def jaccard_cluster_matrix(transition: pd.DataFrame) -> pd.DataFrame:
    labels = []
    memberships: dict[str, set[str]] = {}
    for period in transition.columns:
        for cluster in sorted(transition[period].unique()):
            label = f"{period} C{cluster}"
            labels.append(label)
            memberships[label] = set(transition.index[transition[period] == cluster])

    matrix = pd.DataFrame(0.0, index=labels, columns=labels)
    for left in labels:
        for right in labels:
            union = memberships[left] | memberships[right]
            matrix.loc[left, right] = (
                len(memberships[left] & memberships[right]) / len(union) if union else 0
            )
    return matrix


def _pair_membership_jaccard(labels_a: pd.Series, labels_b: pd.Series) -> float:
    countries = list(labels_a.index)
    pairs_a = {
        pair
        for pair in combinations(countries, 2)
        if labels_a.loc[pair[0]] == labels_a.loc[pair[1]]
    }
    pairs_b = {
        pair
        for pair in combinations(countries, 2)
        if labels_b.loc[pair[0]] == labels_b.loc[pair[1]]
    }
    union = pairs_a | pairs_b
    return len(pairs_a & pairs_b) / len(union) if union else 1.0


def partition_stability_metrics(transition: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for period_a, period_b in combinations(transition.columns, 2):
        labels_a = transition[period_a]
        labels_b = transition[period_b]
        rows.append(
            {
                "Period A": period_a,
                "Period B": period_b,
                "Adjusted Rand Index": adjusted_rand_score(labels_a, labels_b),
                "Normalized Mutual Information": normalized_mutual_info_score(labels_a, labels_b),
                "Pairwise Co-membership Jaccard": _pair_membership_jaccard(labels_a, labels_b),
                "Same Numeric Label Share": float((labels_a == labels_b).mean()),
            }
        )
    return pd.DataFrame(rows)


def _country_peer_group(transition: pd.DataFrame, country: str, period: str) -> set[str]:
    cluster_id = transition.loc[country, period]
    peers = set(transition.index[transition[period] == cluster_id])
    peers.discard(country)
    return peers


def _set_jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def country_mobility_typology(transition: pd.DataFrame) -> pd.DataFrame:
    """Classify each country by how much its same-cluster peer group changed."""
    periods = list(transition.columns)
    rows = []
    for country in transition.index:
        peer_sets = {
            period: _country_peer_group(transition, country, period)
            for period in periods
        }
        pre_early = _set_jaccard(peer_sets[periods[0]], peer_sets[periods[1]])
        early_mid = _set_jaccard(peer_sets[periods[1]], peer_sets[periods[2]])
        pre_mid = _set_jaccard(peer_sets[periods[0]], peer_sets[periods[2]])
        average_retention = float(np.mean([pre_early, early_mid, pre_mid]))

        if pre_early >= 0.50 and early_mid >= 0.50 and pre_mid >= 0.50:
            mobility_type = "stable peer group"
        elif pre_early < 0.50 and pre_mid >= 0.50:
            mobility_type = "temporary mover"
        elif pre_mid < 0.35 and early_mid >= 0.50:
            mobility_type = "persistent mover"
        elif average_retention < 0.35:
            mobility_type = "high mobility"
        else:
            mobility_type = "moderate mobility"

        rows.append(
            {
                "Country Name": country,
                "Mobility Type": mobility_type,
                "Average Peer Retention": average_retention,
                f"{periods[0]} to {periods[1]} Peer Jaccard": pre_early,
                f"{periods[1]} to {periods[2]} Peer Jaccard": early_mid,
                f"{periods[0]} to {periods[2]} Peer Jaccard": pre_mid,
                **{period: transition.loc[country, period] for period in periods},
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values(["Mobility Type", "Average Peer Retention", "Country Name"])
        .reset_index(drop=True)
    )


def cluster_feature_profiles(year_results: dict[int, YearResult], top_n: int = 8) -> pd.DataFrame:
    rows = []
    for year, result in year_results.items():
        labels = result.clusters.set_index("Country Name")["Hierarchical Cluster"]
        joined = result.scaled_features.join(labels)
        means = joined.groupby("Hierarchical Cluster").mean(numeric_only=True)

        for cluster_id, row in means.iterrows():
            ordered = row.sort_values(ascending=False)
            for direction, features in [
                ("high", ordered.head(top_n)),
                ("low", ordered.tail(top_n).sort_values()),
            ]:
                for feature, value in features.items():
                    rows.append(
                        {
                            "Year": year,
                            "Period": PERIOD_NAMES[year],
                            "Hierarchical Cluster": cluster_id,
                            "Direction": direction,
                            "Feature": feature,
                            "Standardized Mean": value,
                        }
                    )
    return pd.DataFrame(rows)


def cluster_profile_summary(
    year_results: dict[int, YearResult],
    feature_profiles: pd.DataFrame,
    top_n: int = 5,
) -> pd.DataFrame:
    """Create one interpretable profile row for each period-cluster pair."""
    rows = []
    grouped_profiles = feature_profiles.groupby(["Year", "Hierarchical Cluster", "Direction"])
    for year, result in year_results.items():
        clusters = result.clusters.sort_values(["Hierarchical Cluster", "Country Name"])
        for cluster_id, cluster_rows in clusters.groupby("Hierarchical Cluster"):
            high = grouped_profiles.get_group((year, cluster_id, "high"))
            low = grouped_profiles.get_group((year, cluster_id, "low"))
            high_features = high.nlargest(top_n, "Standardized Mean")["Feature"].tolist()
            low_features = low.nsmallest(top_n, "Standardized Mean")["Feature"].tolist()
            examples = cluster_rows["Country Name"].head(8).tolist()
            rows.append(
                {
                    "Year": year,
                    "Period": PERIOD_NAMES[year],
                    "Hierarchical Cluster": cluster_id,
                    "Countries": len(cluster_rows),
                    "Example Countries": "; ".join(examples),
                    "Above-Average Features": "; ".join(high_features),
                    "Below-Average Features": "; ".join(low_features),
                }
            )
    return pd.DataFrame(rows)


def plot_transition_heatmap(transition: pd.DataFrame, output_path: Path) -> None:
    height = max(10, min(34, len(transition) * 0.22))
    plt.figure(figsize=(8, height))
    sns.heatmap(transition, cmap="viridis", cbar=True, linewidths=0.2, linecolor="white")
    plt.title("Hierarchical Cluster Transitions, 2019-2021", weight="bold")
    plt.xlabel("")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def plot_pca(year_results: dict[int, YearResult], output_path: Path) -> None:
    fig, axes = plt.subplots(1, len(year_results), figsize=(16, 5), sharex=False, sharey=False)
    for ax, (year, result) in zip(axes, year_results.items()):
        pca_df = result.pca
        sns.scatterplot(
            data=pca_df,
            x="PC1",
            y="PC2",
            hue="Hierarchical Cluster",
            palette="tab10",
            s=45,
            edgecolor="white",
            linewidth=0.4,
            ax=ax,
        )
        variance = pca_df[["explained_variance_pc1", "explained_variance_pc2"]].iloc[0]
        explained = 100 * float(variance.sum())
        ax.set_title(f"{PERIOD_NAMES[year]} ({explained:.1f}% PCA variance)")
        ax.legend(title="Cluster", loc="best", fontsize=8)
    fig.suptitle("Country Positions in First Two Principal Components", weight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def plot_jaccard(matrix: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(12, 10))
    sns.heatmap(matrix, cmap="mako", vmin=0, vmax=1, square=True, linewidths=0.2)
    plt.title("Cluster Membership Jaccard Similarity", weight="bold")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def plot_kmeans_metrics(metrics: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    metric_specs = [
        ("silhouette", "Silhouette", "higher is better"),
        ("davies_bouldin", "Davies-Bouldin", "lower is better"),
        ("calinski_harabasz", "Calinski-Harabasz", "higher is better"),
    ]
    for ax, (metric, title, note) in zip(axes, metric_specs):
        sns.lineplot(data=metrics, x="k", y=metric, hue="Period", marker="o", ax=ax)
        ax.set_title(f"{title} ({note})")
        ax.set_xlabel("K")
        ax.set_ylabel("")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def plot_missingness(missing_report: pd.DataFrame, output_path: Path, top_n: int = 12) -> None:
    top_missing = missing_report.head(top_n).copy()
    top_missing["missing_pct"] = 100 * top_missing["missing_share"]
    top_missing["feature_wrapped"] = top_missing["feature"].map(_wrapped_feature)

    plt.figure(figsize=(12, 7))
    sns.barplot(data=top_missing, x="missing_pct", y="feature_wrapped", color="#4C78A8")
    plt.axvline(30, color="#D55E00", linestyle="--", linewidth=1.5)
    plt.title("Highest Missingness Among Selected WDI Indicators", weight="bold")
    plt.xlabel("Missing values before feature filtering (%)")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def plot_mobility_typology(mobility: pd.DataFrame, output_path: Path) -> None:
    counts = (
        mobility["Mobility Type"]
        .value_counts()
        .rename_axis("Mobility Type")
        .reset_index(name="Countries")
        .sort_values("Countries", ascending=False)
    )
    plt.figure(figsize=(10, 5))
    sns.barplot(data=counts, x="Countries", y="Mobility Type", color="#59A14F")
    plt.title("Country Mobility Typology", weight="bold")
    plt.xlabel("Number of countries")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def _wrapped_feature(text: str, width: int = 42) -> str:
    return "\n".join(wrap(text, width=width))


def plot_feature_profiles(profiles: pd.DataFrame, output_path: Path) -> None:
    top = profiles[profiles["Direction"] == "high"].copy()
    top = top.sort_values(["Year", "Hierarchical Cluster", "Standardized Mean"], ascending=[True, True, False])
    top = top.groupby(["Year", "Hierarchical Cluster"]).head(4)
    top["Feature Wrapped"] = top["Feature"].map(_wrapped_feature)
    top["Panel"] = top["Period"] + " C" + top["Hierarchical Cluster"].astype(str)

    plt.figure(figsize=(14, max(8, len(top) * 0.22)))
    sns.barplot(
        data=top,
        y="Feature Wrapped",
        x="Standardized Mean",
        hue="Panel",
        dodge=False,
        palette="tab20",
    )
    plt.title("Top Above-Average Features by Hierarchical Cluster", weight="bold")
    plt.xlabel("Cluster standardized mean")
    plt.ylabel("")
    plt.legend(title="Period/cluster", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def write_summary(
    output_path: Path,
    panel: pd.DataFrame,
    year_results: dict[int, YearResult],
    stability: pd.DataFrame,
    mobility: pd.DataFrame,
) -> None:
    cluster_lines = []
    for year, result in year_results.items():
        counts = (
            result.clusters["Hierarchical Cluster"]
            .value_counts()
            .sort_index()
            .rename_axis("cluster")
            .reset_index(name="countries")
        )
        count_text = ", ".join(f"C{row.cluster}: {row.countries}" for row in counts.itertuples())
        cluster_lines.append(f"- {PERIOD_NAMES[year]} ({year}): {count_text}")

    stability_lines = []
    for row in stability.to_dict(orient="records"):
        stability_lines.append(
            "- "
            f"{row['Period A']} to {row['Period B']}: "
            f"ARI={row['Adjusted Rand Index']:.3f}, "
            f"NMI={row['Normalized Mutual Information']:.3f}, "
            f"pairwise Jaccard={row['Pairwise Co-membership Jaccard']:.3f}"
        )

    mobility_counts = (
        mobility["Mobility Type"]
        .value_counts()
        .rename_axis("mobility_type")
        .reset_index(name="countries")
        .sort_values("countries", ascending=False)
    )
    mobility_lines = [
        f"- {row.mobility_type}: {row.countries}"
        for row in mobility_counts.itertuples(index=False)
    ]

    text = "\n".join(
        [
            "# Analysis Summary",
            "",
            f"- Complete countries retained: {panel['Country Name'].nunique()}",
            f"- Years analyzed: {', '.join(str(y) for y in YEARS)}",
            f"- Features retained after missingness filtering: {len(panel.columns) - 3}",
            "",
            "## Hierarchical Cluster Sizes",
            *cluster_lines,
            "",
            "## Label-Invariant Stability Metrics",
            *stability_lines,
            "",
            "Adjusted Rand Index, Normalized Mutual Information, and pairwise co-membership",
            "Jaccard compare partitions without assuming that numeric cluster labels are aligned",
            "across years.",
            "",
            "## Country Mobility Typology",
            *mobility_lines,
            "",
            "Country mobility is based on same-cluster peer-group retention, not raw",
            "numeric cluster IDs.",
            "",
        ]
    )
    output_path.write_text(text)


def run_analysis(data_path: str | Path, output_dir: str | Path = "outputs") -> dict[str, Path]:
    """Run the full analysis and return key output paths."""
    data_path = Path(data_path)
    output_dir = Path(output_dir)
    tables_dir = output_dir / "tables"
    figures_dir = output_dir / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    panel, missing_report = load_wdi_panel(data_path)
    panel.to_csv(tables_dir / "clean_panel.csv", index=False)
    missing_report.to_csv(tables_dir / "feature_missingness.csv", index=False)
    data_quality = summarize_data_quality(panel, missing_report)
    data_quality.to_csv(tables_dir / "data_quality_summary.csv", index=False)

    year_results = {year: analyze_year(panel, year) for year in YEARS}
    for year, result in year_results.items():
        result.clusters.to_csv(tables_dir / f"clusters_{year}.csv", index=False)
        result.pca.to_csv(tables_dir / f"pca_{year}.csv", index=False)

    transition = build_transition_table(year_results)
    transition.to_csv(tables_dir / "cluster_transitions.csv")

    jaccard = jaccard_cluster_matrix(transition)
    jaccard.to_csv(tables_dir / "cluster_jaccard_matrix.csv")

    stability = partition_stability_metrics(transition)
    stability.to_csv(tables_dir / "partition_stability_metrics.csv", index=False)

    profiles = cluster_feature_profiles(year_results)
    profiles.to_csv(tables_dir / "cluster_feature_profiles.csv", index=False)
    profile_summary = cluster_profile_summary(year_results, profiles)
    profile_summary.to_csv(tables_dir / "cluster_profile_summary.csv", index=False)

    kmeans_metrics = pd.concat(
        [evaluate_kmeans_grid(result.scaled_features, year) for year, result in year_results.items()],
        ignore_index=True,
    )
    kmeans_metrics.to_csv(tables_dir / "kmeans_grid_metrics.csv", index=False)

    validation = cluster_validation_metrics(year_results)
    validation.to_csv(tables_dir / "cluster_validation_metrics.csv", index=False)

    mobility = country_mobility_typology(transition)
    mobility.to_csv(tables_dir / "country_mobility_typology.csv", index=False)

    plot_transition_heatmap(transition, figures_dir / "cluster_transition_heatmap.png")
    plot_pca(year_results, figures_dir / "pca_cluster_scatter.png")
    plot_jaccard(jaccard, figures_dir / "cluster_jaccard_heatmap.png")
    plot_kmeans_metrics(kmeans_metrics, figures_dir / "kmeans_grid_metrics.png")
    plot_missingness(missing_report, figures_dir / "feature_missingness.png")
    plot_mobility_typology(mobility, figures_dir / "country_mobility_typology.png")
    plot_feature_profiles(profiles, figures_dir / "top_cluster_features.png")

    write_summary(output_dir / "analysis_summary.md", panel, year_results, stability, mobility)

    return {
        "summary": output_dir / "analysis_summary.md",
        "clean_panel": tables_dir / "clean_panel.csv",
        "transitions": tables_dir / "cluster_transitions.csv",
        "stability": tables_dir / "partition_stability_metrics.csv",
        "mobility": tables_dir / "country_mobility_typology.csv",
        "validation": tables_dir / "cluster_validation_metrics.csv",
        "figures": figures_dir,
    }
