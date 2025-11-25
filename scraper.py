#!/usr/bin/env python3
"""
DOC Great Walks Availability Scraper

Scrapes availability data from the DOC booking system and stores it in CSV format.
Designed to run daily via GitHub Actions.
"""

import requests
import json
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import time

# Constants
API_URL = "https://prod-nz-rdr.recreation-management.tylerapp.com/nzrdr/rdr/search/greatwalkplacefacility"
CONFIG_FILE = "config/walks.json"
DATA_DIR = "data"

# Headers matching the R code exactly
HEADERS = {
    "accept": "application/json",
    "accept-language": "en,en-AU;q=0.9,en-NZ;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://bookings.doc.govt.nz",
    "priority": "u=1, i",
    "referer": "https://bookings.doc.govt.nz/",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
}


def load_config() -> Dict[str, Any]:
    """Load configuration from walks.json"""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def scrape_walk_availability(place_id: int, walk_name: str, arrival_date: str, nights: int) -> List[Dict[str, Any]]:
    """
    Scrape availability for a specific walk, arrival date, and duration.

    Returns a list of facility availability records.
    """
    payload = {
        "accomodation": "",
        "placeId": place_id,
        "customerClassificationId": 0,
        "arrivalDate": arrival_date,
        "nights": nights
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)

        # Handle specific error codes
        if response.status_code == 403:
            print(f"  ⚠ Access denied (403) - API may be blocking automated requests")
            print(f"    This often happens when running from cloud/data center IPs")
            return []

        response.raise_for_status()

        data = response.json()
        records = []

        if not data.get("GreatWalkFacilityData"):
            print(f"  No facility data returned for {walk_name} on {arrival_date}")
            return records

        # Process each facility
        for facility in data["GreatWalkFacilityData"]:
            facility_name = facility.get("FacilityName", "Unknown")
            facility_id = facility.get("FacilityId", None)

            # Process each date within this facility's data
            date_data = facility.get("GreatWalkFacilityDateData", [])

            for date_entry in date_data:
                record = {
                    "walk_name": walk_name,
                    "place_id": place_id,
                    "facility_name": facility_name,
                    "facility_id": facility_id,
                    "target_date": date_entry.get("ArrivalDate", ""),
                    "total_capacity": date_entry.get("TotalCapacity", 0),
                    "total_available": date_entry.get("TotalAvailable", 0),
                    "booking_status": date_entry.get("BookingStatus", ""),
                    "price": date_entry.get("Price", 0.0),
                }
                records.append(record)

        return records

    except requests.exceptions.RequestException as e:
        print(f"  Error scraping {walk_name}: {e}")
        return []


def scrape_walk_full_year(place_id: int, walk_name: str, days_ahead: int, nights_per_request: int) -> List[Dict[str, Any]]:
    """
    Scrape availability for a walk for the specified number of days ahead.

    Since the API returns data for a range of nights, we make multiple requests
    to cover the full year ahead.
    """
    all_records = []
    current_date = datetime.now()

    # Calculate how many requests we need to cover the full period
    # We'll request in chunks, moving forward by nights_per_request days each time
    requests_needed = (days_ahead // nights_per_request) + 1

    print(f"\nScraping {walk_name} (placeId: {place_id})")
    print(f"  Making {requests_needed} requests to cover {days_ahead} days ahead...")

    for i in range(requests_needed):
        start_date = current_date + timedelta(days=i * nights_per_request)
        arrival_date_str = start_date.strftime("%Y-%m-%d")

        print(f"  Request {i+1}/{requests_needed}: Starting from {arrival_date_str}")

        records = scrape_walk_availability(place_id, walk_name, arrival_date_str, nights_per_request)
        all_records.extend(records)

        # Be nice to the API - small delay between requests
        if i < requests_needed - 1:
            time.sleep(1)

    print(f"  Collected {len(all_records)} facility-date records")
    return all_records


def save_scrape_results(records: List[Dict[str, Any]], check_timestamp: datetime):
    """
    Save scrape results to a CSV file.

    File structure: data/YYYY/MM/YYYY-MM-DD-HHMM.csv
    """
    if not records:
        print("No records to save")
        return

    # Create directory structure
    year_dir = Path(DATA_DIR) / check_timestamp.strftime("%Y")
    month_dir = year_dir / check_timestamp.strftime("%m")
    month_dir.mkdir(parents=True, exist_ok=True)

    # Create filename with timestamp
    filename = month_dir / f"{check_timestamp.strftime('%Y-%m-%d-%H%M')}.csv"

    # Add check timestamp to each record
    for record in records:
        record["check_timestamp"] = check_timestamp.isoformat()

    # Write CSV
    fieldnames = [
        "check_timestamp",
        "walk_name",
        "place_id",
        "facility_name",
        "facility_id",
        "target_date",
        "total_capacity",
        "total_available",
        "booking_status",
        "price"
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"\n✓ Saved {len(records)} records to {filename}")
    return filename


def main():
    """Main scraping workflow"""
    print("="*60)
    print("DOC Great Walks Availability Scraper")
    print("="*60)

    # Load configuration
    config = load_config()
    enabled_walks = [w for w in config["walks"] if w.get("enabled", False) and w.get("placeId") is not None]

    if not enabled_walks:
        print("\n⚠ No walks enabled in config/walks.json")
        print("Please update the config file with placeIds and set enabled=true")
        return

    print(f"\nEnabled walks: {len(enabled_walks)}")
    for walk in enabled_walks:
        print(f"  - {walk['name']} (placeId: {walk['placeId']})")

    # Get scraping parameters
    days_ahead = config["scraping"].get("days_ahead", 365)
    nights_per_request = config["scraping"].get("nights_per_request", 30)

    print(f"\nScraping parameters:")
    print(f"  Days ahead: {days_ahead}")
    print(f"  Nights per request: {nights_per_request}")

    # Record the check timestamp
    check_timestamp = datetime.now()
    print(f"\nCheck timestamp: {check_timestamp.isoformat()}")

    # Scrape each walk
    all_records = []
    for walk in enabled_walks:
        records = scrape_walk_full_year(
            walk["placeId"],
            walk["name"],
            days_ahead,
            nights_per_request
        )
        all_records.extend(records)

        # Be nice to the API between walks
        time.sleep(2)

    # Save results
    if all_records:
        save_scrape_results(all_records, check_timestamp)
        print(f"\n✓ Scraping complete! Total records: {len(all_records)}")
    else:
        print("\n⚠ No data collected")


if __name__ == "__main__":
    main()
