#!/usr/bin/env python
# Twitter Scraper using Apify API with new actor ID

import datetime
import json
import os
import sys

from apify_client import ApifyClient
from dotenv import load_dotenv

# Import the CSV conversion function
try:
    from extract_tweet_data import convert_jsonl_to_csv

    CSV_CONVERSION_AVAILABLE = True
except ImportError:
    print(
        "Warning: extract_tweet_data.py module not found. CSV conversion will be skipped."
    )
    CSV_CONVERSION_AVAILABLE = False

# Load environment variables from .env file
load_dotenv()

# Get Apify API token from environment variable
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

# Initialize the ApifyClient with your API token
client = ApifyClient(APIFY_API_TOKEN)


def scrape_twitter_and_save_jsonl(
    query, max_tweets, search_type, output_dir="bangladesh_flood", convert_to_csv=True
):
    """
    Scrape Twitter for tweets matching the given query and save to JSONL.
    Optionally also converts to CSV with dedicated media columns.

    Args:
        query (str): Search query for Twitter
        max_tweets (int): Maximum number of tweets to retrieve
        sort_by (str): Sort type - "Top" or "Latest"
        output_dir (str): Directory to save the output files (e.g., "assam_flood")
        convert_to_csv (bool): Whether to also convert the JSONL to CSV

    Returns:
        tuple: (jsonl_path, csv_path) - Paths to the created files (csv_path may be None)
    """
    print(f"Starting Twitter scraper for query: '{query}', sort by: {search_type}")

    # New Twitter Scraper actor ID
    actor_id = "ghSpYIW3L1RvT57NT"

    # Prepare the actor input based on new actor's requirements
    run_input = {
        "query": query,
        "search_type": search_type,
        "max_posts": max_tweets,
    }

    # Create timestamp and output paths
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Ensure the output directories exist
    json_dir = os.path.join(output_dir, "jsons")
    csv_dir = os.path.join(output_dir, "csvs")
    os.makedirs(json_dir, exist_ok=True)
    os.makedirs(csv_dir, exist_ok=True)

    base_filename = f"{query}_{timestamp}"
    jsonl_path = os.path.join(json_dir, f"{base_filename}.jsonl")

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
            # Process tweets and write to file as we go
            print("Fetching and processing tweets...")
            count = 0

            for tweet in client.dataset(run["defaultDatasetId"]).iterate_items():
                # Write complete tweet data to JSONL (one JSON object per line)
                jsonl_file.write(json.dumps(tweet, ensure_ascii=False) + "\n")

                # Update progress
                count += 1
                if count % 10 == 0:
                    print(f"Processed {count} tweets so far...")

                if count >= max_tweets:
                    break

        print(f"Successfully processed {count} tweets")
        print(f"Data saved to JSONL: {jsonl_path}")

        # Convert to CSV if requested and available
        csv_path = None
        if convert_to_csv and CSV_CONVERSION_AVAILABLE and count > 0:
            print("\nConverting JSONL to CSV with dedicated media columns...")
            csv_path = convert_jsonl_to_csv(jsonl_path, output_csv_dir=csv_dir)

        return jsonl_path, csv_path

    except Exception as e:
        print(f"Error during Twitter scraping: {str(e)}")
        return None, None


if __name__ == "__main__":
    # --- Configuration ---
    # This script scrapes tweets for a specific campaign.
    campaign_name = "kerala_flood"  # <--- Change this for a new campaign
    query = "WayanadFlood"  # <--- Change this to the desired search query for the campaign
    max_tweets = 3000  # Maximum number of tweets to retrieve
    search_type = "Top"  # Options: "Top" or "Latest"
    convert_to_csv = True  # Whether to also convert the JSONL to CSV
    # -------------------

    # Define the main output directory for the campaign.
    # The `scrape_twitter_and_save_jsonl` function will create this directory
    # and its subdirectories ('jsons', 'csvs') if they don't exist.
    output_dir = os.path.join("twitter", campaign_name)

    print(f"Starting scraper for campaign: '{campaign_name}' with query: '{query}'")
    print(
        f"Using parameters: Max tweets: {max_tweets}, Sort by: {search_type}, Output to: '{output_dir}'"
    )
    print(
        "To use different parameters, edit the configuration in the __main__ section of this script"
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

    # Run the scraper and save to JSONL (and optionally to CSV)
    jsonl_file, csv_file = scrape_twitter_and_save_jsonl(
        query,
        max_tweets,
        search_type,
        output_dir=output_dir,
        convert_to_csv=convert_to_csv,
    )

    if jsonl_file:
        print("\nProcess complete!")
        print(f"JSONL file: {jsonl_file} (contains complete nested data structure)")

        if csv_file:
            print(
                f"CSV file: {csv_file} (contains flattened data with dedicated media columns)"
            )

            # Offer to run the media analysis
            print("\nTo analyze media content in these tweets:")
            print("  python check_media.py")
            print("  python check_videos.py")
    else:
        print("Failed to scrape tweets and save data.")
