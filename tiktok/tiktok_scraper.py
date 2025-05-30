#!/usr/bin/env python
# TikTok Scraper using Apify API

import datetime
import json
import os
import sys

from apify_client import ApifyClient
from dotenv import load_dotenv

# Import the CSV conversion function
try:
    from extract_tiktok_data import convert_jsonl_to_csv

    CSV_CONVERSION_AVAILABLE = True
except ImportError:
    print(
        "Warning: extract_tiktok_data.py module not found. CSV conversion will be skipped."
    )
    CSV_CONVERSION_AVAILABLE = False

# Load environment variables from .env file
load_dotenv()

# Get Apify API token from environment variable
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

# Initialize the ApifyClient with your API token
client = ApifyClient(APIFY_API_TOKEN)


def scrape_tiktok_and_save_jsonl(
    start_urls=[],
    keywords=None,
    max_items=1000,
    date_range="DEFAULT",
    location=None,
    sort_type="RELEVANCE",
    output_base_filename="tiktok_posts",
    convert_to_csv=True,
):
    """
    Scrape TikTok for posts matching the given parameters and save to JSONL.

    Args:
        start_urls (list): List of TikTok URLs to scrape (profiles, videos, searches, hashtags, etc.)
        keywords (list): List of keywords to search for
        max_items (int): Maximum number of items to retrieve
        date_range (str): Date range for posts - "DEFAULT", "PAST_WEEK", "PAST_MONTH", "PAST_YEAR"
        location (str): Location code, e.g., "US"
        sort_type (str): Sort type - "RELEVANCE", "LIKES", "NEWEST"
        output_base_filename (str): Base name for the output file
        convert_to_csv (bool): Whether to also convert the JSONL to CSV

    Returns:
        tuple: (jsonl_path, csv_path) - Paths to the created files (csv_path may be None)
    """
    print(f"Starting TikTok scraper with {max_items} max items")

    if start_urls:
        print(f"Starting URLs: {', '.join(start_urls)}")
    if keywords:
        print(f"Keywords: {', '.join(keywords)}")

    # TikTok Scraper actor ID
    actor_id = "5K30i8aFccKNF5ICs"

    # Prepare the actor input
    run_input = {
        "maxItems": max_items,
        "dateRange": date_range,
        "sortType": sort_type,
    }

    # Add optional parameters if provided
    if start_urls:
        run_input["startUrls"] = start_urls
    if keywords:
        run_input["keywords"] = keywords
    if location:
        run_input["location"] = location

    # Create timestamp and output path
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    jsonl_path = f"{output_base_filename}_{timestamp}.jsonl"

    try:
        # Run the actor and wait for it to finish
        print("Starting Apify actor run...")
        run = client.actor(actor_id).call(run_input=run_input)

        if not run:
            print("Error: The actor run returned None")
            return None, None

        if "defaultDatasetId" not in run:
            print("Error: The actor run did not return a defaultDatasetId")
            return None, None

        # Open file for writing
        with open(jsonl_path, "w", encoding="utf-8") as jsonl_file:
            # Process posts and write to file as we go
            print("Fetching and processing TikTok posts...")
            count = 0

            for post in client.dataset(run["defaultDatasetId"]).iterate_items():
                # Write complete post data to JSONL (one JSON object per line)
                jsonl_file.write(json.dumps(post, ensure_ascii=False) + "\n")

                # Update progress
                count += 1
                if count % 10 == 0:
                    print(f"Processed {count} posts so far...")

                if count >= max_items:
                    break

        print(f"Successfully processed {count} TikTok posts")
        print(f"Data saved to JSONL: {jsonl_path}")

        # Convert to CSV if requested and available
        csv_path = None
        if convert_to_csv and CSV_CONVERSION_AVAILABLE and count > 0:
            print("\nConverting JSONL to CSV with dedicated media columns...")
            csv_path = convert_jsonl_to_csv(jsonl_path)

        return jsonl_path, csv_path

    except Exception as e:
        print(f"Error during TikTok scraping: {str(e)}")
        return None, None


if __name__ == "__main__":
    # Configure these parameters as needed

    # Option 1: Scrape specific URLs
    start_urls = []

    # Option 2: Use keywords search
    keywords = [
        "Sylhet Flood",
        "Sylhet flood",
        "sylhet flood",
        "SylhetFlood",
        "sylhetflood",
        "Flood In Sylhet",
        "FloodInSylhet",
        "flood in sylhet",
    ]

    # General settings
    max_items = 5000
    date_range = "DEFAULT"  # Options: "DEFAULT", "PAST_WEEK", "PAST_MONTH", "PAST_YEAR"
    location = None
    sort_type = "RELEVANCE"  # Options: "RELEVANCE", "LIKES", "NEWEST"
    convert_to_csv = True  # Whether to also convert the JSONL to CSV

    print(f"Using parameters: Max items: {max_items}, Sort by: {sort_type}")
    print(
        "To use different parameters, edit the values in the __main__ section of this script"
    )

    # Check if API token is available
    if not APIFY_API_TOKEN:
        print(
            "Error: Apify API token not found. Please set the APIFY_API_TOKEN environment variable."
        )
        print(
            "You can find your API token in the Apify Console: https://console.apify.com/account/integrations"
        )
        sys.exit(1)

    # Run the scraper and save to JSONL
    jsonl_file, csv_file = scrape_tiktok_and_save_jsonl(
        start_urls=start_urls,
        keywords=keywords,
        max_items=max_items,
        date_range=date_range,
        location=location,
        sort_type=sort_type,
        convert_to_csv=convert_to_csv,
    )

    if jsonl_file:
        print("\nProcess complete!")
        print(f"JSONL file: {jsonl_file} (contains complete nested data structure)")

        if csv_file:
            print(
                f"CSV file: {csv_file} (contains flattened data with dedicated media columns)"
            )
    else:
        print("Failed to scrape TikTok posts and save data.")
