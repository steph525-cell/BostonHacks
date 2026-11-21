# Meet Me Halfway — BostonHacks 2026 UI update

## Included

- `app.py`: updated Streamlit experience (Where → Vibe → Meeting Results → Hardest to Please).
- `logic.py`: recommendation engine and explainability helpers; same transit 70/30 **internal** components, overall default 70% transit / 30% preferences.
- `requirements.txt`: Python dependencies.
- `.streamlit/config.toml`: light color theme.

## IMPORTANT: keep your existing data folder

This zip does **not** include your station and place CSV files because they were not uploaded in this conversation. Keep the `data/` folder from your existing GitHub repository intact, including at least:

- `data/stations_sample.csv` or `data/stations.csv`
- `data/places_sample.csv` or `data/places.csv`

The application automatically chooses the real dataset if present, otherwise the sample dataset. Your original `assets/roasts.txt` remains optional and compatible.

## Update the deployed Streamlit Cloud app

1. Make a new `ui-redesign` branch from your existing repository.
2. Copy these files to the repository root, replacing `app.py`, `logic.py`, and `requirements.txt` as appropriate. Copy `.streamlit/config.toml` into `.streamlit/`.
3. **Do not delete** the repository's existing `data/`, `.streamlit/secrets.toml`, or `assets/` folders.
4. Test locally or in GitHub Codespaces with `pip install -r requirements.txt` then `streamlit run app.py`.
5. Test demo group, 2–5 friends, the line/station selector, all preferences, both results pages, zero eligible results, and editing inputs after generating results.
6. Merge the branch into whichever branch your Streamlit Cloud app deploys from (typically `main`).

## Technical notes

- Transit times are estimates using straight-line station distance, walking, and transfer penalties. They are **not actual MBTA route times**, timetable predictions, or live arrivals.
- The results map shows pins; it does **not** draw real subway routes.
- A compromise suggestion recalculates matching **for the same top-ranked places**, not for a re-ranked result set.
- The UI is inspired by the BostonHacks KV, not an exact reproduction of its official artwork.

## Validation completed

- Python source files compile.
- Synthetic data unit-style checks passed for ranking, fairness, 5-field match breakdown, Hardest to Please, counterfactual improvement, duplicate business names, missing coordinates, and no eligible places.
- Full Streamlit browser verification has **not** been performed: the real/sample CSV data folder was not provided, and Streamlit was not installed in the validation environment.
