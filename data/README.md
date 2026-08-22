# Data

This project uses the World Bank World Development Indicators CSV export.

The raw `WDICSV.csv` file is not meant to be committed because it is about 161 MB
in this working copy, which exceeds GitHub's normal file-size limit. To recreate
it locally, run from the project root:

```bash
python scripts/download_wdi.py --output-dir .
```

Then run the analysis:

```bash
python scripts/run_analysis.py --data WDICSV.csv --output outputs
```

The reproducible, lightweight outputs are written to `outputs/`.
