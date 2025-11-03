#!/usr/bin/env python
# Download TikTok videos from scraped data and add local paths to a new CSV.

import glob
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests


def download_video(video_url, output_path, post_id, retries=3, timeout=60):
    """
    Download a TikTok video from the given URL.

    Args:
        video_url (str): URL of the video to download
        output_path (str): Path to save the video
        post_id (str): TikTok post ID (used for error reporting)
        retries (int): Number of retries if download fails
        timeout (int): Timeout for the download request in seconds

    Returns:
        str: The output_path if download was successful, None otherwise.
    """
    if not isinstance(video_url, str) or not video_url.startswith("http"):
        # print(f"Skipping post {post_id}: Invalid video URL provided")
        return None

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Skip if file already exists
    if os.path.exists(output_path):
        print(f"Skipping post {post_id}: Video already exists at {output_path}")
        return output_path

    # Try to download with retries
    for attempt in range(retries):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.tiktok.com/",
            }

            response = requests.get(
                video_url, headers=headers, stream=True, timeout=timeout
            )

            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                # print(f"Downloaded video for post {post_id} to {output_path}")
                return output_path
            else:
                print(
                    f"Error downloading post {post_id} (Attempt {attempt+1}/{retries}): HTTP {response.status_code}"
                )

        except Exception as e:
            print(
                f"Error downloading post {post_id} (Attempt {attempt+1}/{retries}): {str(e)}"
            )

        if attempt < retries - 1:
            time.sleep(2**attempt)

    print(f"Failed to download video for post {post_id} after {retries} attempts")
    return None


def process_csv_and_download_media(csv_file, campaign_base_dir, max_workers=5):
    """
    Process a CSV file, download videos, and create a new CSV with local paths.

    Args:
        csv_file (str): Path to the CSV file containing post data.
        campaign_base_dir (str): The base directory for the campaign (e.g., 'tiktok/assam_flood').
        max_workers (int): Maximum number of concurrent downloads.

    Returns:
        Path to the new CSV file with local paths.
    """
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found!")
        return None

    # Create directories for media inside the campaign folder
    videos_dir = os.path.join(campaign_base_dir, "videos")
    os.makedirs(videos_dir, exist_ok=True)

    # Generate output CSV filename to be saved in the campaign's csvs folder
    base_name = os.path.splitext(os.path.basename(csv_file))[0]
    output_csv_name = f"{base_name}_with_local_paths.csv"
    output_csv_path = os.path.join(campaign_base_dir, "csvs", output_csv_name)

    # Read the CSV file
    df = pd.read_csv(csv_file)
    print(f"Read {len(df)} posts from {csv_file}")

    # Ensure required columns exist
    if "video_url" not in df.columns or "id" not in df.columns:
        print("Error: CSV file must contain 'video_url' and 'id' columns.")
        return None

    # Add the new column for local paths, initialized to empty
    df["video_local_path"] = ""

    # Prepare download tasks
    tasks = []
    for index, row in df.iterrows():
        post_id = str(row["id"])
        video_url = row["video_url"]
        filename = f"tiktok_{post_id}.mp4"
        output_path = os.path.join(videos_dir, filename)
        tasks.append((video_url, output_path, post_id, index))

    # Download videos in parallel and update the DataFrame
    successful_downloads = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(download_video, url, path, post_id): index
            for url, path, post_id, index in tasks
        }
        for i, future in enumerate(as_completed(future_to_task)):
            index = future_to_task[future]
            try:
                local_path = future.result()
                if local_path:
                    df.loc[index, "video_local_path"] = local_path
                    successful_downloads += 1
                # If local_path is None, the cell remains empty, indicating a failure.
            except Exception as exc:
                print(f"Task for post at index {index} generated an exception: {exc}")

            if (i + 1) % 20 == 0:
                print(f"Processed {i+1}/{len(tasks)} videos...")

    # Save the updated DataFrame to a new CSV file
    print(f"\nSaving new CSV with local paths to: {output_csv_path}")
    df.to_csv(output_csv_path, index=False, encoding="utf-8")

    # Print summary
    total_videos = len(tasks)
    print("\n===== DOWNLOAD SUMMARY =====")
    print(f"Total posts with video URLs: {total_videos}")
    print(f"Videos successfully downloaded: {successful_downloads}")
    print(f"Failed or skipped downloads: {total_videos - successful_downloads}")
    print(f"\nNew CSV file with local paths: {output_csv_path}")

    return output_csv_path


if __name__ == "__main__":
    # --- Configuration ---
    campaign_name = "south_asia_flood"  # <--- Change this for other campaigns
    max_workers = 10
    # -------------------

    # Define base directory for the campaign
    campaign_dir = os.path.join("tiktok", campaign_name)
    csv_dir = os.path.join(campaign_dir, "csvs")

    if not os.path.isdir(campaign_dir):
        print(f"Error: Campaign directory '{campaign_dir}' not found.")
        sys.exit(1)

    # Find the latest "filtered" CSV file in the campaign's CSV directory
    filtered_csv_files = glob.glob(os.path.join(csv_dir, "filtered_*.csv"))
    if not filtered_csv_files:
        print(f"Error: No filtered CSV files found in '{csv_dir}'.")
        print("Please run the filtering script (filter_by_date.py) first.")
        sys.exit(1)

    latest_filtered_csv = max(filtered_csv_files, key=os.path.getmtime)
    print(f"Using the latest filtered CSV file: {latest_filtered_csv}")

    # Process the CSV and download media
    process_csv_and_download_media(
        latest_filtered_csv, campaign_dir, max_workers=max_workers
    )
