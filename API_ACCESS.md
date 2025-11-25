# API Access & Bot Protection

## The Issue

The DOC booking API (`prod-nz-rdr.recreation-management.tylerapp.com`) has bot protection that may block requests from:
- Data center IPs (like GitHub Actions)
- Cloud providers (AWS, Azure, GCP)
- VPS/hosting providers

You may see **403 Access Denied** errors when running from these environments.

## Solutions

### Option 1: Run Locally (Recommended for now)

Run the scraper from your local machine instead of GitHub Actions:

```bash
# Set up
git clone <your-repo>
cd great-walk-tracker
pip install -r requirements.txt

# Run manually
python scraper.py

# Commit and push results
git add data/
git commit -m "Data update: $(date)"
git push
```

**Schedule it locally:**
- **Windows**: Use Task Scheduler
- **Mac/Linux**: Use cron

```bash
# Example cron (daily at noon)
0 12 * * * cd /path/to/great-walk-tracker && python scraper.py && git add data/ && git commit -m "Data update" && git push
```

### Option 2: Self-Hosted GitHub Runner

Use a [self-hosted GitHub Actions runner](https://docs.github.com/en/actions/hosting-your-own-runners) on your home computer or NZ-based VPS.

Update `.github/workflows/scrape.yml`:
```yaml
jobs:
  scrape:
    runs-on: self-hosted  # ← Change this
```

### Option 3: Residential Proxy

Use a residential proxy service (costs money):
- Bright Data
- Oxylabs
- SmartProxy

Update `scraper.py` to use proxies:
```python
proxies = {
    "http": "http://your-proxy:port",
    "https": "https://your-proxy:port"
}
response = requests.post(API_URL, headers=HEADERS, json=payload, proxies=proxies)
```

### Option 4: Contact DOC

If you're doing research or analysis, consider reaching out to DOC:
- Explain your use case
- Ask if they have an official API or data export
- They may whitelist your IP or provide data directly

## Testing API Access

Test if the API works from your current environment:

```bash
python test_scraper.py
```

If you see:
- ✓ **Success** → API access works, you can use GitHub Actions
- ✗ **403 Access denied** → API is blocking you, use Option 1, 2, or 3

## Current Status

- **Your R code**: Works (probably running from your local machine with residential IP)
- **GitHub Actions**: May be blocked (data center IPs)
- **Recommended**: Start with Option 1 (local cron job)

## Alternative: Manual Trigger

If GitHub Actions don't work automatically, you can:
1. Run the scraper manually on your local machine daily
2. Commit and push the data
3. Keep GitHub as the data storage/version control

This is actually quite reliable and doesn't depend on the API allowing cloud IPs.
