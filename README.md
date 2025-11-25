# DOC Great Walks Availability Tracker

Automated tracking of accommodation availability for New Zealand's Great Walks. This system scrapes the DOC booking website daily to monitor:

1. **Actual usage**: How full are huts/campsites on/near the day itself
2. **Booking velocity**: How quickly do spots book out as the target date approaches

## 🎯 Purpose

Track availability across all 10 DOC Great Walks over time to understand booking patterns, peak seasons, and facility utilization.

## 📊 Data Structure

Data is stored in CSV format, optimized for git efficiency:

```
data/
  YYYY/
    MM/
      YYYY-MM-DD-HHMM.csv  # One file per scrape
```

Each CSV contains:
- `check_timestamp`: When we scraped the data
- `walk_name`: Name of the Great Walk
- `place_id`: DOC system ID for the walk
- `facility_name`: Hut or campsite name
- `facility_id`: DOC system ID for the facility
- `target_date`: The date being booked
- `total_capacity`: Total beds/sites
- `total_available`: Available beds/sites
- `booking_status`: Status (e.g., "Available", "Fully Booked")
- `price`: Price in NZD

### Why This Structure?

- **Git-friendly**: New file per scrape = no merge conflicts
- **Query-friendly**: Easy to grep/filter by any dimension
- **Compresses well**: CSV compresses efficiently in git
- **Simple**: Any tool can read CSV (Python, R, Excel, etc.)

## 🚀 Setup

### 1. Configure Great Walks

Edit `config/walks.json` to add placeIds for each walk:

```json
{
  "name": "Milford Track",
  "placeId": 123,
  "enabled": true
}
```

**Finding placeIds**: See [DISCOVER_PLACEIDS.md](DISCOVER_PLACEIDS.md) for instructions.

### 2. Enable GitHub Actions

The scraper runs automatically via GitHub Actions:
- **Schedule**: Daily at 00:00 UTC (Noon NZDT)
- **Manual**: Can be triggered via Actions tab

### 3. Run Manually (Optional)

```bash
pip install -r requirements.txt
python scraper.py
```

## 📝 Configuration

`config/walks.json`:

- `walks`: List of Great Walks to track
  - `name`: Walk name
  - `placeId`: DOC system ID (see DISCOVER_PLACEIDS.md)
  - `enabled`: Set to `true` to track
- `scraping`:
  - `days_ahead`: How many days ahead to check (default: 365)
  - `nights_per_request`: Nights to request per API call (default: 30)
  - `schedule_utc`: When to run (GitHub Actions cron schedule)

## 📈 Analysis Ideas

With this data, you can analyze:

1. **Booking velocity**: For popular dates (e.g., New Year's), how quickly do they sell out?
2. **Utilization rates**: What's the actual occupancy? (check availability close to target date)
3. **Seasonal patterns**: When are different walks most popular?
4. **Facility comparison**: Which huts book out fastest on a given walk?
5. **Year-over-year trends**: Is demand increasing or decreasing?

### Example Queries

```bash
# All availability checks for Perry Saddle Hut on 2025-12-31
grep "2025-12-31.*Perry Saddle Hut" data/**/*.csv

# How did 2025-12-31 availability change over time?
grep ",2025-12-31," data/**/*.csv | grep "Heaphy Track"

# All fully booked facilities yesterday
grep "$(date -d yesterday +%Y-%m-%d)" data/**/*.csv | grep "Fully Booked"
```

## 🏔️ Great Walks

New Zealand's 10 official Great Walks:

1. **Milford Track** - Fiordland (4 days)
2. **Routeburn Track** - Fiordland/Mt Aspiring (2-3 days)
3. **Kepler Track** - Fiordland (3-4 days)
4. **Heaphy Track** - Kahurangi (4-6 days) ✓ *configured*
5. **Abel Tasman Coast Track** - Abel Tasman (3-5 days)
6. **Tongariro Northern Circuit** - Tongariro (3-4 days)
7. **Lake Waikaremoana Track** - Te Urewera (3-4 days)
8. **Whanganui Journey** - Whanganui (3-5 days, canoe)
9. **Rakiura Track** - Stewart Island (3 days)
10. **Paparoa Track** - Paparoa (2-3 days)

## 🔧 Technical Details

### API

The DOC booking system uses Tyler Technologies' Recreation Management platform:

- **Endpoint**: `https://prod-nz-rdr.recreation-management.tylerapp.com/nzrdr/rdr/search/greatwalkplacefacility`
- **Method**: POST
- **Payload**: `{placeId, arrivalDate, nights}`
- **Response**: Nested JSON with facility and date data

### Rate Limiting

The scraper:
- Waits 1 second between requests for the same walk
- Waits 2 seconds between different walks
- Total runtime: ~5-10 minutes for all walks (full year)

### GitHub Actions

- Runs on Ubuntu latest
- Python 3.11
- Auto-commits results to the repo
- Can be manually triggered via workflow_dispatch

## 📚 Files

- `scraper.py` - Main scraping script
- `config/walks.json` - Walk configuration
- `requirements.txt` - Python dependencies
- `DISCOVER_PLACEIDS.md` - Guide to finding placeIds
- `.github/workflows/scrape.yml` - GitHub Actions workflow
- `data/` - Scraped data (git-tracked)

## 🤝 Contributing

To add more walks:
1. Find the placeId (see DISCOVER_PLACEIDS.md)
2. Add to config/walks.json with `enabled: true`
3. Commit and push

## 📄 License

Data is sourced from DOC's public booking system. Please use responsibly and don't overload their servers.

---

**Status**: Currently tracking Heaphy Track. Additional walks need placeIds discovered.
