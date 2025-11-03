#!/usr/bin/env python3
"""
Download all media (photos and videos) from tweets and add columns with local file paths.
This script reads a CSV file with dedicated media columns, downloads each media file,
and creates a new CSV with additional columns for local file paths.
"""

import csv
import glob
import os
import sys
from datetime import datetime
from urllib.parse import urlparse

import requests


def create_media_directories(base_media_dir):
    """Create directories for downloaded media within a specific base directory."""
    photos_dir = os.path.join(base_media_dir, "photos")
    videos_dir = os.path.join(base_media_dir, "videos")
    os.makedirs(photos_dir, exist_ok=True)
    os.makedirs(videos_dir, exist_ok=True)
    return photos_dir, videos_dir


def get_file_extension(url):
    """Extract file extension from URL."""
    # Parse the URL
    parsed_url = urlparse(url)

    # Get the path component
    path = parsed_url.path

    # Extract the extension
    _, ext = os.path.splitext(path)

    # If there's no extension or it's unusual (like parameters), use defaults
    if not ext or len(ext) > 5:
        if "video" in url:
            return ".mp4"
        else:
            return ".jpg"

    return ext


def download_file(url, save_path, timeout=30):
    """
    Download a file from URL and save it to the specified path.

    Args:
        url: URL of the file to download
        save_path: Path where the file should be saved
        timeout: Timeout in seconds for the request

    Returns:
        True if download was successful, False otherwise
    """
    try:
        # Make a request to get the file
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses

        # Save the file
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False


def sanitize_filename(filename):
    """Sanitize filename to be valid on all operating systems."""
    # Replace invalid characters
    invalid_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    for char in invalid_chars:
        filename = filename.replace(char, "_")

    # Limit length to avoid file system limitations
    if len(filename) > 100:
        filename = filename[:100]

    return filename


def process_csv_and_download_media(csv_file, campaign_base_dir):
    """
    Process the CSV file, download media, and create a new CSV with local paths.

    Args:
        csv_file: Path to the CSV file containing tweet data
        campaign_base_dir: The base directory for the campaign (e.g., 'twitter/assam_flood')

    Returns:
        Path to the new CSV file with local paths
    """
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found!")
        return None

    # Create directories for media inside the campaign folder
    media_dir = os.path.join(campaign_base_dir, "media")
    photos_dir, videos_dir = create_media_directories(media_dir)

    # Generate output CSV filename to be saved in the campaign's csvs folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(csv_file))[0]
    output_csv_name = f"{base_name}_with_local_paths_{timestamp}.csv"
    output_csv_path = os.path.join(campaign_base_dir, "csvs", output_csv_name)

    # Track stats
    total_tweets = 0
    total_photos = 0
    total_videos = 0
    downloaded_photos = 0
    downloaded_videos = 0
    failed_downloads = 0

    # Open the input CSV
    with open(csv_file, "r", encoding="utf-8", newline="") as infile:
        reader = csv.DictReader(infile)

        # Check if reader has fieldnames
        if not reader.fieldnames:
            print("Error: CSV file appears to be empty or malformed.")
            return None

        # Find photo and video columns
        photo_columns = [
            col
            for col in reader.fieldnames
            if col.startswith("photo") and col != "photo_count"
        ]
        video_columns = [
            col
            for col in reader.fieldnames
            if col.startswith("video") and col != "video_count"
        ]

        if not photo_columns and not video_columns:
            print("Warning: This CSV doesn't seem to have the expected media columns.")
            print(
                "This script expects columns like photo1, photo2, video1, video2, etc."
            )
            return None

        print(
            f"Found {len(photo_columns)} photo columns and {len(video_columns)} video columns"
        )

        # Create new fieldnames with local path columns
        new_fieldnames = list(reader.fieldnames)

        # Add local path columns
        for col in photo_columns:
            new_fieldnames.append(f"{col}_local_path")

        for col in video_columns:
            new_fieldnames.append(f"{col}_local_path")

        # Prepare to write the new CSV
        all_rows = []

        # Process each row
        for row in reader:
            total_tweets += 1

            # Process each photo
            for col in photo_columns:
                photo_url = row.get(col, "").strip()
                if photo_url:
                    total_photos += 1

                    # Create a unique filename based on tweet ID and photo column
                    tweet_id = row.get("tweet_id", "unknown")
                    screen_name = row.get("screen_name", "unknown")

                    # Get file extension from URL
                    ext = get_file_extension(photo_url)

                    # Create filename
                    filename = f"{tweet_id}_{sanitize_filename(screen_name)}_{col}{ext}"
                    save_path = os.path.join(photos_dir, filename)

                    # Download the photo
                    print(f"Downloading photo: {photo_url}")
                    if download_file(photo_url, save_path):
                        downloaded_photos += 1
                        row[f"{col}_local_path"] = save_path
                    else:
                        failed_downloads += 1
                        row[f"{col}_local_path"] = ""
                else:
                    row[f"{col}_local_path"] = ""

            # Process each video
            for col in video_columns:
                video_url = row.get(col, "").strip()
                if video_url:
                    total_videos += 1

                    # Create a unique filename based on tweet ID and video column
                    tweet_id = row.get("tweet_id", "unknown")
                    screen_name = row.get("screen_name", "unknown")

                    # Get file extension from URL
                    ext = get_file_extension(video_url)

                    # Create filename
                    filename = f"{tweet_id}_{sanitize_filename(screen_name)}_{col}{ext}"
                    save_path = os.path.join(videos_dir, filename)

                    # Download the video
                    print(f"Downloading video: {video_url}")
                    if download_file(
                        video_url, save_path, timeout=120
                    ):  # Longer timeout for videos
                        downloaded_videos += 1
                        row[f"{col}_local_path"] = save_path
                    else:
                        failed_downloads += 1
                        row[f"{col}_local_path"] = ""
                else:
                    row[f"{col}_local_path"] = ""

            # Add the processed row
            all_rows.append(row)

            # Show progress every 5 tweets
            if total_tweets % 5 == 0:
                print(
                    f"Processed {total_tweets} tweets, downloaded {downloaded_photos} photos and {downloaded_videos} videos"
                )

        # Write to the new CSV
        with open(output_csv_path, "w", encoding="utf-8", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=new_fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)

    # Print summary
    print("\n===== DOWNLOAD SUMMARY =====")
    print(f"Total tweets processed: {total_tweets}")
    print(f"Total photos found: {total_photos}")
    print(f"Total videos found: {total_videos}")
    print(f"Photos successfully downloaded: {downloaded_photos}")
    print(f"Videos successfully downloaded: {downloaded_videos}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"\nNew CSV file with local paths: {output_csv_path}")

    return output_csv_path


if __name__ == "__main__":
    # --- Configuration ---
    # This script will download media for the specified campaign.
    # It automatically finds the most recent 'filtered' CSV in the campaign's 'csvs' directory.
    campaign_name = "kerala_flood"  # <--- Change this for other campaigns
    # -------------------

    # Define base directory for the campaign
    campaign_dir = os.path.join("twitter", campaign_name)
    csv_dir = os.path.join(campaign_dir, "csvs")

    # Check if the campaign directory exists
    if not os.path.isdir(campaign_dir):
        print(f"Error: Campaign directory '{campaign_dir}' not found.")
        print(
            "Please ensure the campaign name is correct and the directory structure is in place."
        )
        sys.exit(1)

    # Find the latest "filtered" CSV file in the campaign's CSV directory
    print(f"Searching for filtered CSV files in: {csv_dir}")
    filtered_csv_files = glob.glob(os.path.join(csv_dir, "filtered_*.csv"))
    if not filtered_csv_files:
        print(f"Error: No filtered CSV files found in '{csv_dir}'.")
        print("Please run the filtering script (filter_tweets.py) first.")
        sys.exit(1)

    # Get the most recently modified file
    latest_filtered_csv = max(filtered_csv_files, key=os.path.getmtime)
    print(f"Using the latest filtered CSV file: {latest_filtered_csv}")

    # Process the CSV and download media
    output_csv = process_csv_and_download_media(latest_filtered_csv, campaign_dir)

    if output_csv:
        print("\nMedia download complete!")
        print(
            f"You can find all media files in the '{os.path.join(campaign_dir, 'media')}' directory."
        )
        print(
            f"The new CSV file '{os.path.basename(output_csv)}' includes additional columns with local file paths."
        )
        print("\nTo analyze media content after downloading:")
        print("  python check_media.py")
        print("  python check_videos.py")
    else:
        print("Failed to process the CSV and download media.")
