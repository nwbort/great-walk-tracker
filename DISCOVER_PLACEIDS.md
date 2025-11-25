# How to Discover Great Walk placeIds

The DOC booking system uses `placeId` values to identify each Great Walk. Here's how to find them manually:

## Method 1: Browser Developer Tools (Recommended)

1. Open https://bookings.doc.govt.nz/ in your browser
2. Open Developer Tools (F12)
3. Go to the Network tab
4. Navigate to a Great Walk booking page (e.g., click on "Milford Track")
5. Look for XHR/Fetch requests to `recreation-management.tylerapp.com`
6. Check the request payload - you should see `"placeId": XXX`
7. Record the placeId for that walk

## Method 2: URL Inspection

Some booking URLs contain placeId:
```
https://bookings.doc.govt.nz/Saturn/Facilities/SearchViewGW.aspx?placeId=XXX
```

Try navigating to different Great Walks and check if the URL contains placeId.

## Method 3: JavaScript Console

On the DOC booking page:
1. Open Developer Console (F12 → Console)
2. Type: `window.location.search` or inspect page variables
3. Look for placeId references in the page's JavaScript

## Recording Your Findings

Once you find a placeId, update `config/walks.json`:

```json
{
  "name": "Milford Track",
  "placeId": 123,  // ← Add the placeId here
  "enabled": true   // ← Set to true to start scraping
}
```

## Known placeIds

- **Heaphy Track**: 876 ✓
- **Milford Track**: ? (from search results, possibly 432?)
- **Others**: TBD

## Testing a placeId

Once you have a placeId, you can test it:

```bash
curl -X POST "https://prod-nz-rdr.recreation-management.tylerapp.com/nzrdr/rdr/search/greatwalkplacefacility" \
  -H "accept: application/json" \
  -H "content-type: application/json" \
  -H "origin: https://bookings.doc.govt.nz" \
  -H "referer: https://bookings.doc.govt.nz/" \
  -d '{"placeId":876,"arrivalDate":"2025-12-31","nights":5}'
```

Replace `876` with the placeId you want to test.

## Alternative: Check R Code History

If you have other R scripts that query different walks, check for placeId values in those scripts.
