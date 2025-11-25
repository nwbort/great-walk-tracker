# Testing API Access

## Quick Test

Run this from your local machine to test if the DOC API is accessible:

### R Version (Recommended)

```r
source("test_scraper.R")
```

Or from command line:
```bash
Rscript test_scraper.R
```

### Python Version

```bash
python test_scraper.py
```

## What You'll See

### ✓ Success (API works)
```
✓ SUCCESS! API access is working.

Found 5 facilities:

  Facility 1: Clinton Hut
    Dates available: 5
    First date: 2025-12-25
    Available: 12/40
    Price: $70
    Status: Available
...
```

**This means:** You can run the scraper from this machine! Use local cron job or self-hosted runner.

### ✗ Failed (API blocked)
```
✗ FAILED: Access Denied (403)

The API is blocking requests from your IP/environment.
```

**This means:** The API is blocking your current IP. See `API_ACCESS.md` for solutions.

## Next Steps

### If Test Succeeds
You can run the full scraper:
```bash
python scraper.py
```

Or set up a local cron job (see `API_ACCESS.md`)

### If Test Fails
See `API_ACCESS.md` for alternative approaches:
- Residential proxy
- Contact DOC for official access
- Self-hosted runner on a different network

## Testing Different Walks

Edit the test script to try different placeIds:

**R**: Change line ~26
```r
test_walk <- list(name = "Routeburn Track", placeId = 874)
```

**Python**: Change line ~18
```python
test_walk = {"name": "Routeburn Track", "placeId": 874}
```

All placeIds are in `config/walks.json`
