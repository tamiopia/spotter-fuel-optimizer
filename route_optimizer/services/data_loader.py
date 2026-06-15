"""
Loads fuel station CSV and enriches with coordinates from a local US cities dataset.
No geocoding API calls — uses SimpleMaps uscities.csv (offline, instant startup).

One-time setup:
  Download uscities.csv (free, no account) from simplemaps.com/data/us-cities
  Place it in the project root alongside fuel_prices.csv
"""
import logging
import pandas as pd
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

STATIONS: list = []
STATIONS_READY = False

US_STATES = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN',
    'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV',
    'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN',
    'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC',
}


def _load_cities_lookup() -> dict:
    """
    Build a (CITY_UPPER, STATE) -> (lat, lng) dict from SimpleMaps uscities.csv.
    The file must be placed in the project root (same folder as manage.py).
    """
    cities_path = Path(settings.BASE_DIR) / 'uscities.csv'
    if not cities_path.exists():
        raise FileNotFoundError(
            "uscities.csv not found in project root.\n"
            "Download the free US cities dataset from simplemaps.com/data/us-cities\n"
            "and place uscities.csv in the same folder as manage.py."
        )

    df = pd.read_csv(cities_path, usecols=['city_ascii', 'state_id', 'lat', 'lng'])
    lookup = {}
    for _, row in df.iterrows():
        key = (str(row['city_ascii']).strip().upper(), str(row['state_id']).strip().upper())
        # Keep first entry for each city/state (largest city wins when duplicates exist)
        if key not in lookup:
            lookup[key] = (float(row['lat']), float(row['lng']))
    return lookup


def load_station_data() -> None:
    """
    Read fuel CSV, join against local cities dataset for coordinates, populate STATIONS.
    Runs synchronously — completes in under 1 second, no network calls.
    """
    global STATIONS, STATIONS_READY

    csv_path = settings.FUEL_CSV_PATH
    if not csv_path.exists():
        logger.warning(f"Fuel CSV not found at {csv_path}. Station data not loaded.")
        return

    # Load city coordinates from local dataset
    try:
        city_lookup = _load_cities_lookup()
        logger.info(f"Loaded {len(city_lookup)} US city coordinates from uscities.csv")
    except FileNotFoundError as e:
        logger.error(str(e))
        return

    # Load and clean fuel station CSV
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    df = df[df['State'].str.strip().isin(US_STATES)].copy()
    df['Retail Price'] = pd.to_numeric(df['Retail Price'], errors='coerce')
    df = df.dropna(subset=['Retail Price'])
    df = df.sort_values('Retail Price').drop_duplicates(subset=['OPIS Truckstop ID'], keep='first')

    for col in ['City', 'State', 'Truckstop Name']:
        if col in df.columns:
            df[col] = df[col].str.strip()

    # Join stations with city coordinates
    stations = []
    unmatched_cities = set()

    for _, row in df.iterrows():
        city_key = (row['City'].upper(), row['State'].upper())
        coords = city_lookup.get(city_key)

        if coords is None:
            # Try dropping punctuation/spacing variations (e.g. "ST. LOUIS" -> "ST LOUIS")
            normalized = (
                row['City'].upper().replace('.', '').replace('-', ' '),
                row['State'].upper(),
            )
            coords = city_lookup.get(normalized)

        if coords:
            lat, lng = coords
            stations.append({
                'id': row['OPIS Truckstop ID'],
                'name': row['Truckstop Name'],
                'city': row['City'],
                'state': row['State'],
                'retail_price': float(row['Retail Price']),
                'lat': lat,
                'lng': lng,
            })
        else:
            unmatched_cities.add(city_key)

    STATIONS = stations
    STATIONS_READY = True

    if unmatched_cities:
        logger.info(
            f"Could not match {len(unmatched_cities)} cities to coordinates "
            f"(those stations skipped). Sample: {list(unmatched_cities)[:5]}"
        )

    logger.info(f"Loaded {len(STATIONS)} fuel stations. Ready.")
