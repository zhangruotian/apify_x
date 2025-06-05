#!/usr/bin/env python
# Clean up videos that are not in the current CSV dataset

import os
from pathlib import Path

import pandas as pd


def cleanup_videos(csv_file, videos_dir):
    """
    Remove videos from videos_dir that are not listed in the CSV file.

    Args:
        csv_file (str): Path to the CSV file with video data
        videos_dir (str): Path to the directory containing downloaded videos

    Returns:
        tuple: (removed_count, total_videos, saved_space)
    """
    # Check if videos directory exists
    if not os.path.isdir(videos_dir):
        print(f"Error: Videos directory not found: {videos_dir}")
        return 0, 0, 0

    # Check if CSV file exists
    if not os.path.isfile(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        return 0, 0, 0

    print(f"Reading post IDs from: {csv_file}")

    # Read the CSV file to get post IDs
    try:
        df = pd.read_csv(csv_file)
        if "id" not in df.columns:
            print("Error: CSV file must contain 'id' column")
            return 0, 0, 0

        # Get all valid post IDs from the CSV
        valid_ids = set(str(id) for id in df["id"])
        print(f"Found {len(valid_ids)} valid post IDs in CSV")
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return 0, 0, 0

    # Get all video files in the directory
    video_files = list(Path(videos_dir).glob("tiktok_*.mp4"))
    total_videos = len(video_files)

    if total_videos == 0:
        print("No videos found in the directory")
        return 0, 0, 0

    print(f"Found {total_videos} videos in {videos_dir}")

    # Check each video file and remove if not in valid_ids
    removed_count = 0
    saved_bytes = 0

    for video_path in video_files:
        # Extract post ID from filename (format: tiktok_<post_id>.mp4)
        filename = video_path.name
        if not filename.startswith("tiktok_") or not filename.endswith(".mp4"):
            continue

        # Extract the post ID from the filename
        post_id = filename[7:-4]  # Remove "tiktok_" prefix and ".mp4" suffix

        # If post ID is not in the valid IDs, remove the file
        if post_id not in valid_ids:
            try:
                # Get file size before removing
                file_size = os.path.getsize(video_path)

                # Remove the file
                os.remove(video_path)
                removed_count += 1
                saved_bytes += file_size

                print(f"Removed: {filename} ({file_size / (1024*1024):.2f} MB)")
            except Exception as e:
                print(f"Error removing {filename}: {str(e)}")

    # Convert saved bytes to MB for reporting
    saved_space_mb = saved_bytes / (1024 * 1024)

    return removed_count, total_videos, saved_space_mb


def main():
    # Set default paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(script_dir, "csvs", "tiktok_posts_20240801_to_20241031.csv")
    videos_dir = os.path.join(script_dir, "media", "videos")

    # Run the cleanup
    removed, total, saved_space = cleanup_videos(csv_file, videos_dir)

    # Report results
    if removed > 0:
        print(f"\nCleanup complete: Removed {removed} of {total} videos")
        print(f"Freed up {saved_space:.2f} MB of disk space")
    else:
        print("\nNo videos were removed")


if __name__ == "__main__":
    main()
