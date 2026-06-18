# Fuel Route Optimizer API

A Django REST API that calculates the cheapest fuel stops for a road trip across the US.

## Overview

Given a start and end location, the API plans your route, identifies where you need to refuel (every 500 miles at 10 MPG), and selects the cheapest truck stop near each refuel point from a database of 8,000+ US fuel stations.

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get an OpenRouteService API key

Sign up for free at https://openrouteservice.org/dev/#/signup (no credit card required).

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```
ORS_API_KEY=your_key_here
FUEL_CSV_PATH=fuel_prices.csv
SEARCH_RADIUS_MILES=50
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
```

### 5. Place the fuel prices CSV

Copy `fuel-prices-for-be-assessment.csv` to the project root and rename it to `fuel_prices.csv`.

### 6. Run migrations

```bash
python manage.py migrate
```

### 7. Start the server

```bash
python manage.py runserver
```

On startup, the server geocodes ~400 city/state pairs (takes 1–2 minutes). Watch for:

```
Loaded 7843 fuel stations across 398 cities
```

## API Usage

### Endpoint

```
POST /api/route/
Content-Type: application/json
```

### Request

```json
{
    "start": "New York, NY",
    "end": "Los Angeles, CA"
}
```

### Example with curl

```bash
curl -X POST http://localhost:8000/api/route/ \
  -H "Content-Type: application/json" \
  -d '{"start": "New York, NY", "end": "Los Angeles, CA"}'
```

### Sample Response

```json
{
    "start": "New York, NY",
    "end": "Los Angeles, CA",
    "total_distance_miles": 2789.4,
    "total_duration_hours": 40.2,
    "num_fuel_stops": 5,
    "total_gallons": 250.0,
    "total_fuel_cost": 824.65,
    "fuel_stops": [
        {
            "stop_number": 1,
            "mile_marker": 500,
            "truckstop_name": "PILOT TRAVEL CENTER #492",
            "city": "Seymour",
            "state": "IN",
            "retail_price_per_gallon": 3.149,
            "gallons_purchased": 50.0,
            "stop_cost": 157.45,
            "lat": 38.958,
            "lng": -85.889
        }
    ],
    "route_polyline": "a~l~Fjk~uOwHJy@P..."
}
```

## How It Works

- **At startup**: the server reads the fuel prices CSV, filters to US stations, and geocodes ~400 unique city/state pairs using OpenRouteService — this takes 1–2 minutes but happens only once.
- **Per request**: geocodes your start and end locations (2 API calls), then fetches the driving route (1 API call) — 3 total.
- **Fuel stop placement**: for a 2,789-mile trip, stops are needed at miles 500, 1000, 1500, 2000, and 2500, so the algorithm finds the geographic point on the route at each of those mile markers.
- **Station selection**: at each waypoint, all stations within 50 miles are found using the Haversine formula (pure Python, no API), then the cheapest one is selected.
- **Cost calculation**: each stop buys exactly 50 gallons (500 miles ÷ 10 MPG) at the station's retail price.

## Performance

- Startup geocoding: ~400 API calls, runs once, takes 1–2 minutes
- Per-request API calls: 3 (2 geocodes + 1 directions)
- Station search: O(n) over 8k records in memory, completes in <10ms
- Total response time: ~1–2 seconds (dominated by network latency)

## Running Tests

```bash
python manage.py test route_optimizer.tests
```
