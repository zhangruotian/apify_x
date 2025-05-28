#!/usr/bin/env python3
"""
Check which tweets in the CSV file have different types of media (photos, videos).
This script works with the CSV format that uses dedicated columns for each media item.
"""

import csv
import glob
import os
import sys


def find_latest_csv():
    """Find the most recent CSV file in the current directory."""
    csv_files = glob.glob("*.csv")
    if not csv_files:
        return None

    # Sort by modification time, most recent first
    latest_file = max(csv_files, key=os.path.getmtime)
    return latest_file


def check_media(csv_file):
    """
    Check for tweets with media in the CSV file.

    Args:
        csv_file: Path to the CSV file containing tweet data

    Returns:
        dict: Summary statistics about the media in the tweets
    """
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found!")
        return None

    print(f"Checking for media in {csv_file}...")

    # Initialize counters
    total_tweets = 0
    with_photo = 0
    with_video = 0
    with_multiple_media = 0

    # Track tweets with media for summary
    tweets_with_media = []

    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        # Try to read the file using csv.DictReader
        try:
            reader = csv.DictReader(f)

            # Check if the CSV has the expected format with dedicated media columns
            header = reader.fieldnames if reader.fieldnames else []
            photo_columns = [
                col
                for col in header
                if col.startswith("photo") and col != "photo_count"
            ]
            video_columns = [
                col
                for col in header
                if col.startswith("video") and col != "video_count"
            ]

            if not photo_columns and not video_columns:
                print(
                    "Warning: This CSV doesn't seem to have the expected dedicated media columns."
                )
                print(
                    "This script expects columns like photo1, photo2, video1, video2, etc."
                )

            for row in reader:
                total_tweets += 1

                # Check for photos
                has_photo = False
                photo_count = 0
                for col in photo_columns:
                    if row.get(col, "").strip():
                        has_photo = True
                        photo_count += 1

                # Check for videos
                has_video = False
                video_count = 0
                for col in video_columns:
                    if row.get(col, "").strip():
                        has_video = True
                        video_count += 1

                # Count tweets with each media type
                if has_photo:
                    with_photo += 1

                if has_video:
                    with_video += 1

                # Count tweets with multiple media types
                if has_photo and has_video:
                    with_multiple_media += 1

                # Add to the list of tweets with media
                if has_photo or has_video:
                    tweets_with_media.append(
                        {
                            "tweet_id": row.get("tweet_id", "unknown"),
                            "screen_name": row.get("screen_name", "unknown"),
                            "has_photo": has_photo,
                            "has_video": has_video,
                            "photo_count": photo_count,
                            "video_count": video_count,
                            "total_media": photo_count + video_count,
                        }
                    )
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
            return None

    # Prepare summary statistics
    if total_tweets == 0:
        print("No tweets found in the CSV file.")
        return None

    media_percentage = (
        (len(tweets_with_media) / total_tweets) * 100 if total_tweets > 0 else 0
    )
    video_percentage = (with_video / total_tweets) * 100 if total_tweets > 0 else 0
    photo_percentage = (with_photo / total_tweets) * 100 if total_tweets > 0 else 0

    # Print summary
    print("\n===== MEDIA SUMMARY =====")
    print(f"Total tweets: {total_tweets}")
    print(f"Tweets with any media: {len(tweets_with_media)} ({media_percentage:.1f}%)")
    print(f"Tweets with photos: {with_photo} ({photo_percentage:.1f}%)")
    print(f"Tweets with videos: {with_video} ({video_percentage:.1f}%)")
    print(f"Tweets with both photos and videos: {with_multiple_media}")

    # Print tweets with most media items
    if tweets_with_media:
        tweets_with_media.sort(key=lambda x: x["total_media"], reverse=True)

        print("\n===== TWEETS WITH MOST MEDIA =====")
        for i, tweet in enumerate(tweets_with_media[:5]):
            media_types = []
            if tweet["has_photo"]:
                media_types.append(f"PHOTOS ({tweet['photo_count']})")
            if tweet["has_video"]:
                media_types.append(f"VIDEOS ({tweet['video_count']})")

            print(f"{i+1}. Tweet ID: {tweet['tweet_id']}, @{tweet['screen_name']}")
            print(f"   Media types: {', '.join(media_types)}")
            print(f"   Total media items: {tweet['total_media']}")

    # Return summary statistics for potential further use
    return {
        "total_tweets": total_tweets,
        "with_media": len(tweets_with_media),
        "with_photo": with_photo,
        "with_video": with_video,
        "with_multiple_media": with_multiple_media,
        "top_media_tweets": tweets_with_media[:5] if tweets_with_media else [],
    }


if __name__ == "__main__":
    # Configure these parameters directly
    csv_file = "tweets_20250505_160019_csv_20250505_170000.csv"  # Path to your CSV file

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

    # Check media in the CSV file
    check_media(csv_file)

    print("\nTip: To examine specific tweets with video content:")
    print("  python check_videos.py")
