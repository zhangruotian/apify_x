#!/usr/bin/env python3
"""
Check which tweets in the CSV file have videos.
This script specifically focuses on video content, providing detailed information
about video URLs and their quality. It works with the CSV format that uses dedicated
video columns (video1, video2, etc.).
"""

import csv
import glob
import os
import sys
from urllib.parse import parse_qs, urlparse


def find_latest_csv():
    """Find the most recent CSV file in the current directory."""
    csv_files = glob.glob("*.csv")
    if not csv_files:
        return None

    # Sort by modification time, most recent first
    latest_file = max(csv_files, key=os.path.getmtime)
    return latest_file


def analyze_video_url(url):
    """Analyze a video URL for information about resolution and format."""
    result = {"url": url}

    # Parse URL parts
    parsed_url = urlparse(url)

    # Get resolution from URL path
    path = parsed_url.path
    if "vid/avc1/" in path:
        try:
            resolution = path.split("vid/avc1/")[1].split("/")[0]
            result["resolution"] = resolution
        except (IndexError, ValueError):
            result["resolution"] = "unknown"
    else:
        result["resolution"] = "unknown"

    # Check for video quality in query parameters
    query_params = parse_qs(parsed_url.query)
    if "tag" in query_params:
        result["tag"] = query_params["tag"][0]

    # Detect format from URL
    if path.endswith(".mp4"):
        result["format"] = "MP4"
    elif path.endswith(".m3u8"):
        result["format"] = "HLS"
    else:
        result["format"] = "unknown"

    return result


def check_videos(csv_file, verbose=False):
    """Check for tweets with videos in the CSV file with detailed information."""
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found!")
        return None

    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        # Check if reader has fieldnames
        if not reader.fieldnames:
            print("Error: CSV file appears to be empty or malformed.")
            return None

        # Find all video columns
        video_columns = [
            col
            for col in reader.fieldnames
            if col.startswith("video") and col != "video_count"
        ]

        if not video_columns:
            print("Warning: This CSV doesn't seem to have the expected video columns.")
            print("This script expects columns like video1, video2, etc.")
            return None

        print(f"Checking for videos in {csv_file}...")
        print(f"Found {len(video_columns)} video columns: {', '.join(video_columns)}")

        count = 0
        video_tweets = []

        for row in reader:
            # Check if any video column has content
            urls = []
            for col in video_columns:
                if row.get(col, "").strip():
                    urls.append(row[col])

            # Check if this row has a video
            if urls:
                count += 1
                tweet_id = row.get("tweet_id", "unknown")
                screen_name = row.get("screen_name", "unknown")
                text = row.get("text", "")

                # Truncate tweet text if too long
                if len(text) > 100:
                    text = text[:97] + "..."

                # Analyze each video URL
                url_analyses = []
                for url in urls:
                    if url.strip():
                        url_analyses.append(analyze_video_url(url))

                # Store video tweet info
                video_tweet = {
                    "tweet_id": tweet_id,
                    "screen_name": screen_name,
                    "text": text,
                    "video_count": len(urls),
                    "urls": url_analyses,
                }
                video_tweets.append(video_tweet)

                # Print basic info
                print(f"Tweet {count}: ID={tweet_id}, By=@{screen_name}")
                print(f"Text: {text}")

                # Print URL analysis
                for i, analysis in enumerate(url_analyses):
                    print(
                        f"  Video {i+1}: {analysis['format']} - {analysis['resolution']}"
                    )
                    if verbose:
                        print(f"  URL: {analysis['url']}")

                print("-" * 80)

        if count == 0:
            print("No tweets with videos found.")
        else:
            print(f"Found {count} tweets with videos.")

            # Print summary of video formats/resolutions
            resolutions = {}
            formats = {}

            for tweet in video_tweets:
                for url_analysis in tweet["urls"]:
                    # Count formats
                    fmt = url_analysis["format"]
                    formats[fmt] = formats.get(fmt, 0) + 1

                    # Count resolutions
                    res = url_analysis["resolution"]
                    resolutions[res] = resolutions.get(res, 0) + 1

            print("\nVideo Format Distribution:")
            for fmt, count in sorted(formats.items(), key=lambda x: x[1], reverse=True):
                print(f"  {fmt}: {count} videos")

            print("\nVideo Resolution Distribution:")
            for res, count in sorted(
                resolutions.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"  {res}: {count} videos")

        return video_tweets


if __name__ == "__main__":
    # Configure these parameters directly
    csv_file = "tweets_20250505_160019_csv_20250505_170000.csv"  # Path to your CSV file
    verbose = False  # Set to True to show full video URLs

    # Check if file exists before running
    if not os.path.exists(csv_file):
        print(f"CSV file '{csv_file}' not found!")
        print("Looking for the most recent CSV file instead...")

        latest_csv = find_latest_csv()
        if latest_csv:
            print(f"Found most recent CSV file: {latest_csv}")
            csv_file = latest_csv
        else:
            print("No CSV files found in the current directory.")
            print(
                "Edit the csv_file parameter in the __main__ section to point to your CSV file."
            )
            sys.exit(1)

    print(f"Using CSV file: {csv_file}")

    # Check videos in the CSV file
    check_videos(csv_file, verbose)
