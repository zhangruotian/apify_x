#!/usr/bin/env python
# Download TikTok videos from scraped data

import argparse
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests


def download_video(video_url, output_path, post_id, retries=3, timeout=30):
    """
    Download a TikTok video from the given URL.

    Args:
        video_url (str): URL of the video to download
        output_path (str): Path to save the video
        post_id (str): TikTok post ID (used for error reporting)
        retries (int): Number of retries if download fails
        timeout (int): Timeout for the download request in seconds

    Returns:
        bool: True if download was successful, False otherwise
    """
    if not video_url:
        print(f"Skipping post {post_id}: No video URL provided")
        return False

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Skip if file already exists
    if os.path.exists(output_path):
        print(f"Skipping post {post_id}: Video already exists at {output_path}")
        return True

    # Try to download with retries
    for attempt in range(retries):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.tiktok.com/",
                "Accept": "video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive",
            }

            response = requests.get(
                video_url, headers=headers, stream=True, timeout=timeout
            )

            if response.status_code == 200:
                # Save the video
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)

                print(f"Downloaded video for post {post_id} to {output_path}")
                return True
            else:
                print(
                    f"Error downloading post {post_id} (Attempt {attempt+1}/{retries}): HTTP {response.status_code}"
                )

        except Exception as e:
            print(
                f"Error downloading post {post_id} (Attempt {attempt+1}/{retries}): {str(e)}"
            )

        # Wait before retrying (exponential backoff)
        if attempt < retries - 1:
            time.sleep(2**attempt)

    print(f"Failed to download video for post {post_id} after {retries} attempts")
    return False


def process_csv_file(csv_file, output_dir="media/videos", max_workers=5, limit=None):
    """
    Process a CSV file containing TikTok post data and download videos.

    Args:
        csv_file (str): Path to the CSV file
        output_dir (str): Directory to save downloaded videos
        max_workers (int): Maximum number of concurrent downloads
        limit (int): Maximum number of videos to download

    Returns:
        tuple: (successful_downloads, total_posts)
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Read the CSV file
    df = pd.read_csv(csv_file)

    # Check if required columns exist
    if "video_url" not in df.columns or "id" not in df.columns:
        print("Error: CSV file must contain 'video_url' and 'id' columns")
        return 0, 0

    # Limit the number of downloads if specified
    if limit:
        df = df.head(limit)

    # Filter out rows with missing video URLs
    df = df[df["video_url"].notna()]
    total_posts = len(df)

    if total_posts == 0:
        print("No videos to download")
        return 0, 0

    print(f"Found {total_posts} TikTok videos to download")

    # Prepare download tasks
    download_tasks = []
    for _, row in df.iterrows():
        post_id = str(row["id"])
        video_url = row["video_url"]

        # Construct filename: tiktok_<post_id>.mp4
        filename = f"tiktok_{post_id}.mp4"
        output_path = os.path.join(output_dir, filename)

        download_tasks.append((video_url, output_path, post_id))

    # Download videos in parallel
    successful_downloads = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(download_video, url, path, post_id)
            for url, path, post_id in download_tasks
        ]

        for future in futures:
            if future.result():
                successful_downloads += 1

    print(f"Downloaded {successful_downloads} of {total_posts} videos")
    return successful_downloads, total_posts


def main():
    parser = argparse.ArgumentParser(description="Download TikTok videos from CSV data")
    parser.add_argument(
        "--csv", "-c", help="Path to CSV file (default: latest in csvs directory)"
    )
    parser.add_argument(
        "--output", "-o", default="media/videos", help="Output directory for videos"
    )
    parser.add_argument(
        "--workers", "-w", type=int, default=5, help="Maximum concurrent downloads"
    )
    parser.add_argument(
        "--limit", "-l", type=int, help="Maximum number of videos to download"
    )

    args = parser.parse_args()

    # If CSV not specified, find the latest one
    csv_file = args.csv
    if not csv_file:
        # First look for filtered CSV files
        csvs_dir = os.path.join(os.path.dirname(__file__), "csvs")
        filtered_files = list(Path(csvs_dir).glob("tiktok_posts_*.csv"))

        if filtered_files:
            # Use the most recently modified filtered file
            csv_file = str(max(filtered_files, key=os.path.getmtime))
        else:
            # Look for any CSV files
            csv_files = list(Path(csvs_dir).glob("*.csv"))

            if csv_files:
                # Use the most recently modified CSV file
                csv_file = str(max(csv_files, key=os.path.getmtime))
            else:
                print("No CSV files found in the csvs directory")
                return

    print(f"Using CSV file: {csv_file}")

    # Process the CSV file and download videos
    successful, total = process_csv_file(
        csv_file=csv_file,
        output_dir=args.output,
        max_workers=args.workers,
        limit=args.limit,
    )

    # Report results
    if successful == total:
        print(f"All {successful} videos were downloaded successfully")
    else:
        print(f"{successful} of {total} videos were downloaded successfully")
        print(f"{total - successful} videos failed to download")


if __name__ == "__main__":
    main()
