#!/usr/bin/env python3
"""Quick test of the scraper with one walk"""

import requests
import json
from datetime import datetime, timedelta

API_URL = "https://prod-nz-rdr.recreation-management.tylerapp.com/nzrdr/rdr/search/greatwalkplacefacility"

HEADERS = {
    "accept": "application/json",
    "accept-language": "en,en-AU;q=0.9,en-NZ;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "content-type": "application/json",
    "origin": "https://bookings.doc.govt.nz",
    "referer": "https://bookings.doc.govt.nz/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
}

# Test with Milford Track
test_walk = {"name": "Milford Track", "placeId": 873}

arrival_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

payload = {
    "accomodation": "",
    "placeId": test_walk["placeId"],
    "customerClassificationId": 0,
    "arrivalDate": arrival_date,
    "nights": 5
}

print(f"Testing {test_walk['name']} (placeId: {test_walk['placeId']})")
print(f"Arrival date: {arrival_date}")
print(f"Payload: {json.dumps(payload, indent=2)}\n")

try:
    response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=15)
    print(f"Status code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success!\n")

        if data.get("GreatWalkFacilityData"):
            facilities = data["GreatWalkFacilityData"]
            print(f"Found {len(facilities)} facilities:")

            for facility in facilities[:3]:  # Show first 3
                name = facility.get("FacilityName", "Unknown")
                dates = facility.get("GreatWalkFacilityDateData", [])
                print(f"\n  {name}")
                print(f"    Dates available: {len(dates)}")

                if dates:
                    first_date = dates[0]
                    print(f"    First date: {first_date.get('ArrivalDate')}")
                    print(f"    Available: {first_date.get('TotalAvailable')}/{first_date.get('TotalCapacity')}")
                    print(f"    Price: ${first_date.get('Price', 0):.2f}")

            if len(facilities) > 3:
                print(f"\n  ... and {len(facilities) - 3} more facilities")
        else:
            print("⚠ No facility data returned")
    else:
        print(f"✗ Failed: {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"✗ Error: {e}")
