#!/usr/bin/env Rscript
# Quick test of the DOC API with one walk

library(httr)
library(jsonlite)

# API endpoint
api_url <- "https://prod-nz-rdr.recreation-management.tylerapp.com/nzrdr/rdr/search/greatwalkplacefacility"

# Headers matching the R code
headers <- c(
  accept = "application/json",
  `accept-language` = "en,en-AU;q=0.9,en-NZ;q=0.8,en-GB;q=0.7,en-US;q=0.6",
  `content-type` = "application/json",
  dnt = "1",
  origin = "https://bookings.doc.govt.nz",
  priority = "u=1, i",
  referer = "https://bookings.doc.govt.nz/",
  `sec-ch-ua` = '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
  `sec-ch-ua-mobile` = "?0",
  `sec-ch-ua-platform` = '"Windows"',
  `sec-fetch-dest` = "empty",
  `sec-fetch-mode` = "cors",
  `sec-fetch-site` = "cross-site",
  `user-agent` = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)

# Test data - Milford Track
test_walk <- list(
  name = "Milford Track",
  placeId = 873
)

# Calculate arrival date (30 days from now)
arrival_date <- format(Sys.Date() + 30, "%Y-%m-%d")

# Request payload
payload <- list(
  accomodation = "",
  placeId = test_walk$placeId,
  customerClassificationId = 0,
  arrivalDate = arrival_date,
  nights = 5
)

cat("=========================================\n")
cat("Testing DOC API Access\n")
cat("=========================================\n\n")
cat("Walk:", test_walk$name, "\n")
cat("PlaceId:", test_walk$placeId, "\n")
cat("Arrival date:", arrival_date, "\n\n")

# Make request
cat("Making API request...\n")

tryCatch({

  res <- POST(
    url = api_url,
    add_headers(.headers = headers),
    body = toJSON(payload, auto_unbox = TRUE),
    encode = "json"
  )

  cat("Status code:", status_code(res), "\n\n")

  if (status_code(res) == 200) {
    cat("✓ SUCCESS! API access is working.\n\n")

    data <- content(res)

    if (!is.null(data$GreatWalkFacilityData) && length(data$GreatWalkFacilityData) > 0) {
      facilities <- data$GreatWalkFacilityData
      cat("Found", length(facilities), "facilities:\n\n")

      # Show first 3 facilities
      for (i in seq_len(min(3, length(facilities)))) {
        facility <- facilities[[i]]
        facility_name <- facility$FacilityName %||% "Unknown"

        cat("  Facility", i, ":", facility_name, "\n")

        if (!is.null(facility$GreatWalkFacilityDateData) && length(facility$GreatWalkFacilityDateData) > 0) {
          dates <- facility$GreatWalkFacilityDateData
          cat("    Dates available:", length(dates), "\n")

          first_date <- dates[[1]]
          cat("    First date:", first_date$ArrivalDate %||% "Unknown", "\n")
          cat("    Available:", first_date$TotalAvailable %||% 0, "/", first_date$TotalCapacity %||% 0, "\n")
          cat("    Price: $", first_date$Price %||% 0, "\n")
          cat("    Status:", first_date$BookingStatus %||% "Unknown", "\n")
        }
        cat("\n")
      }

      if (length(facilities) > 3) {
        cat("  ... and", length(facilities) - 3, "more facilities\n\n")
      }

      cat("=========================================\n")
      cat("RESULT: API is accessible from your environment!\n")
      cat("You can run the scraper from this machine.\n")
      cat("=========================================\n")

    } else {
      cat("⚠ No facility data returned\n")
    }

  } else if (status_code(res) == 403) {
    cat("✗ FAILED: Access Denied (403)\n\n")
    cat("The API is blocking requests from your IP/environment.\n")
    cat("This usually happens when running from:\n")
    cat("  - Data centers\n")
    cat("  - Cloud providers (AWS, GCP, Azure)\n")
    cat("  - VPS hosting\n\n")
    cat("See API_ACCESS.md for solutions.\n")

  } else {
    cat("✗ FAILED: HTTP", status_code(res), "\n")
    cat("Response:", content(res, "text", encoding = "UTF-8"), "\n")
  }

}, error = function(e) {
  cat("✗ ERROR:", e$message, "\n")
})
