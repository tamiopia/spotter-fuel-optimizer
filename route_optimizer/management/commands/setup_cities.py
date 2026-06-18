"""
Management command: python manage.py setup_cities

Downloads US city coordinates from GeoNames (free, no account needed)
and saves them as uscities.csv in the project root.

Run this once before starting the server for the first time.
"""
import io
import zipfile
import requests
import pandas as pd
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

GEONAMES_URL = "https://download.geonames.org/export/dump/cities500.zip"

GEONAMES_COLS = [
    'geonameid', 'name', 'asciiname', 'alternatenames', 'latitude', 'longitude',
    'feature_class', 'feature_code', 'country_code', 'cc2', 'admin1_code',
    'admin2_code', 'admin3_code', 'admin4_code', 'population', 'elevation',
    'dem', 'timezone', 'modification_date',
]

US_STATES = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN',
    'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV',
    'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN',
    'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC',
}


class Command(BaseCommand):
    help = 'Download US city coordinates from GeoNames and save as uscities.csv'

    def handle(self, *args, **options):
        output_path = Path(settings.BASE_DIR) / 'uscities.csv'

        if output_path.exists():
            self.stdout.write(f'uscities.csv already exists at {output_path}. Skipping download.')
            self.stdout.write('Delete it and re-run to refresh.')
            return

        self.stdout.write('Downloading cities500.zip from GeoNames (~25 MB)...')
        try:
            response = requests.get(GEONAMES_URL, stream=True, timeout=120)
            response.raise_for_status()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Download failed: {e}'))
            return

        content = b''
        total = 0
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            content += chunk
            total += len(chunk)
            self.stdout.write(f'  downloaded {total // (1024*1024)} MB...', ending='\r')
        self.stdout.write('')

        self.stdout.write('Extracting and filtering to US cities...')
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                with zf.open('cities500.txt') as f:
                    df = pd.read_csv(
                        f,
                        sep='\t',
                        header=None,
                        names=GEONAMES_COLS,
                        dtype=str,
                        low_memory=False,
                    )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Extraction failed: {e}'))
            return

        self.stdout.write(f'Total cities worldwide: {len(df)}')

        # Filter to US populated places
        us = df[
            (df['country_code'] == 'US') &
            (df['feature_class'] == 'P') &
            (df['admin1_code'].isin(US_STATES))
        ].copy()

        us['lat'] = pd.to_numeric(us['latitude'], errors='coerce')
        us['lng'] = pd.to_numeric(us['longitude'], errors='coerce')
        us = us.dropna(subset=['lat', 'lng'])

        result = us[['asciiname', 'admin1_code', 'lat', 'lng']].copy()
        result.columns = ['city_ascii', 'state_id', 'lat', 'lng']
        result = result.drop_duplicates(subset=['city_ascii', 'state_id'])

        result.to_csv(output_path, index=False)

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Saved {len(result)} US cities to {output_path}\n'
            f'Now run: python manage.py runserver'
        ))
