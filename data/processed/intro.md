# AuroraBid Processed Data Overview

This directory contains the processed features used by AuroraBid during training and real-time bidding simulations.

## Folder Structure

```
data/processed/
├── user_features.parquet       # Static or embedding-based user features
├── context_features.parquet    # Contextual features like time, location, device
├── history_features.parquet    # Aggregated past behavior features
├── combined_features.parquet   # Final joined table per request_id
```

## Feature Sources

- **User features**: extracted from demographics, tags, or pre-trained embeddings
- **Context features**: include hour of day, day of week, device type, media source
- **History features**: recent CTR, conversion windows, recency/frequency stats
- **Combined features**: produced by joining all components keyed on `request_id`

## Format & Access

All data is stored in **Parquet** format for efficient disk and memory access.
These files are read and served via the `feature_store.py` module in `src/features/`.

## Usage

This folder acts as a local mock for Redis/Kafka. During training or testing:

```python
from src.features.feature_store import LocalFeatureStore
store = LocalFeatureStore("data/processed")
store.load()
```

## Notes
- Keep this folder in sync with your feature generation pipeline.
- Do not modify `combined_features.parquet` manually—it is generated via pipeline.
- Production system may replace this with Redis streams or online feature store.

---

For detailed schema definitions, refer to `schema.json` in the project root.

