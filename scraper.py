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
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Constants
API_URL = "https://prod-nz-rdr.recreation-management.tylerapp.com/nzrdr/rdr/search/greatwalkplacefacility"
CONFIG_FILE = "config/walks.json"
DATA_DIR = "data"

# Thread-safe print lock for parallel processing
print_lock = threading.Lock()

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


def safe_print(*args, **kwargs):
    """Thread-safe print function"""
    with print_lock:
        print(*args, **kwargs)


def load_config() -> Dict[str, Any]:
    """Load configuration from walks.json"""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def scrape_walk_availability(place_id: int, walk_name: str, arrival_date: str, nights: int, request_num: int = None, total_requests: int = None) -> List[Dict[str, Any]]:
    """
    Scrape availability for a specific walk, arrival date, and duration.

    Returns a list of facility availability records.
    """
    progress_str = f"[{request_num}/{total_requests}] " if request_num and total_requests else ""

    safe_print(f"  {progress_str}🌐 Fetching {walk_name} from {arrival_date} ({nights} nights)...")

    payload = {
        "accomodation": "",
        "placeId": place_id,
        "customerClassificationId": 0,
        "arrivalDate": arrival_date,
        "nights": nights
    }

    request_start = time.time()
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
        request_time = time.time() - request_start

        # Handle specific error codes
        if response.status_code == 403:
            safe_print(f"  {progress_str}⚠ Access denied (403) - API may be blocking automated requests")
            safe_print(f"    This often happens when running from cloud/data center IPs")
            return []

        response.raise_for_status()

        data = response.json()
        records = []

        if not data.get("GreatWalkFacilityData"):
            safe_print(f"  {progress_str}⚠ No facility data returned for {walk_name} on {arrival_date}")
            return records

        # Process each facility
        facilities_count = 0
        for facility in data["GreatWalkFacilityData"]:
            facilities_count += 1
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

        safe_print(f"  {progress_str}✓ Got {len(records)} records from {facilities_count} facilities ({request_time:.2f}s)")
        return records

    except requests.exceptions.RequestException as e:
        request_time = time.time() - request_start
        safe_print(f"  {progress_str}✗ Error scraping {walk_name}: {e} ({request_time:.2f}s)")
        return []


def scrape_walk_full_year(place_id: int, walk_name: str, days_ahead: int, nights_per_request: int, max_workers: int = 5) -> List[Dict[str, Any]]:
    """
    Scrape availability for a walk for the specified number of days ahead.

    Since the API returns data for a range of nights, we make multiple requests
    to cover the full year ahead. Uses parallel processing for faster scraping.
    """
    all_records = []
    current_date = datetime.now()

    # Calculate how many requests we need to cover the full period
    # We'll request in chunks, moving forward by nights_per_request days each time
    requests_needed = (days_ahead // nights_per_request) + 1

    safe_print(f"\n{'='*60}")
    safe_print(f"🚶 {walk_name} (placeId: {place_id})")
    safe_print(f"{'='*60}")
    safe_print(f"  📅 Date range: {requests_needed} requests to cover {days_ahead} days")
    safe_print(f"  🔄 Using {max_workers} parallel workers")

    start_time = time.time()

    # Prepare all requests
    requests = []
    for i in range(requests_needed):
        start_date = current_date + timedelta(days=i * nights_per_request)
        arrival_date_str = start_date.strftime("%Y-%m-%d")
        requests.append((i + 1, arrival_date_str))

    # Process requests in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_request = {
            executor.submit(
                scrape_walk_availability,
                place_id,
                walk_name,
                arrival_date_str,
                nights_per_request,
                request_num,
                requests_needed
            ): (request_num, arrival_date_str)
            for request_num, arrival_date_str in requests
        }

        # Collect results as they complete
        completed = 0
        for future in as_completed(future_to_request):
            completed += 1
            request_num, arrival_date_str = future_to_request[future]
            try:
                records = future.result()
                all_records.extend(records)
            except Exception as e:
                safe_print(f"  ✗ Exception for request {request_num}: {e}")

    elapsed_time = time.time() - start_time
    safe_print(f"\n  ✅ {walk_name} complete!")
    safe_print(f"     • Collected {len(all_records)} facility-date records")
    safe_print(f"     • Time: {elapsed_time:.2f}s ({elapsed_time/requests_needed:.2f}s per request)")

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
    print("\n" + "="*70)
    print("🏔️  DOC GREAT WALKS AVAILABILITY SCRAPER")
    print("="*70)

    overall_start = time.time()

    # Load configuration
    print("\n📋 Loading configuration...")
    config = load_config()
    enabled_walks = [w for w in config["walks"] if w.get("enabled", False) and w.get("placeId") is not None]

    if not enabled_walks:
        print("\n⚠ No walks enabled in config/walks.json")
        print("Please update the config file with placeIds and set enabled=true")
        return

    print(f"   ✓ Found {len(enabled_walks)} enabled walks:")
    for i, walk in enumerate(enabled_walks, 1):
        print(f"     {i}. {walk['name']} (placeId: {walk['placeId']})")

    # Get scraping parameters
    days_ahead = config["scraping"].get("days_ahead", 365)
    nights_per_request = config["scraping"].get("nights_per_request", 30)
    max_workers_per_walk = config["scraping"].get("max_workers_per_walk", 5)
    max_parallel_walks = config["scraping"].get("max_parallel_walks", 3)

    print(f"\n⚙️  Scraping parameters:")
    print(f"   • Days ahead: {days_ahead}")
    print(f"   • Nights per request: {nights_per_request}")
    print(f"   • Max workers per walk: {max_workers_per_walk}")
    print(f"   • Max parallel walks: {max_parallel_walks}")

    # Calculate total requests
    requests_per_walk = (days_ahead // nights_per_request) + 1
    total_requests = requests_per_walk * len(enabled_walks)
    print(f"   • Total API requests: {total_requests} ({requests_per_walk} per walk)")

    # Record the check timestamp
    check_timestamp = datetime.now()
    print(f"\n🕐 Check timestamp: {check_timestamp.isoformat()}")

    # Scrape walks in parallel
    print(f"\n🚀 Starting parallel scraping with {max_parallel_walks} concurrent walks...")
    print("="*70)

    all_records = []
    walk_results = {}

    with ThreadPoolExecutor(max_workers=max_parallel_walks) as executor:
        future_to_walk = {
            executor.submit(
                scrape_walk_full_year,
                walk["placeId"],
                walk["name"],
                days_ahead,
                nights_per_request,
                max_workers_per_walk
            ): walk["name"]
            for walk in enabled_walks
        }

        # Collect results as they complete
        completed_walks = 0
        for future in as_completed(future_to_walk):
            completed_walks += 1
            walk_name = future_to_walk[future]
            try:
                records = future.result()
                all_records.extend(records)
                walk_results[walk_name] = len(records)
                safe_print(f"\n📊 Progress: {completed_walks}/{len(enabled_walks)} walks completed")
            except Exception as e:
                safe_print(f"\n✗ Exception processing {walk_name}: {e}")
                walk_results[walk_name] = 0

    # Summary
    overall_time = time.time() - overall_start
    print("\n" + "="*70)
    print("📈 SCRAPING SUMMARY")
    print("="*70)
    print(f"\n⏱️  Total time: {overall_time:.2f}s ({overall_time/60:.2f} minutes)")
    print(f"📊 Total records collected: {len(all_records)}")
    print(f"\n📝 Records by walk:")
    for walk_name, count in walk_results.items():
        print(f"   • {walk_name}: {count} records")

    # Save results
    if all_records:
        print(f"\n💾 Saving results...")
        save_scrape_results(all_records, check_timestamp)
        print(f"\n✅ SCRAPING COMPLETE!")
    else:
        print("\n⚠️  WARNING: No data collected")


if __name__ == "__main__":
    main()
