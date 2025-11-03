#!/usr/bin/env python3
"""
Quick Status Check for Cleaned Twitter Data

This script quickly shows the status of your cleaned datasets without making any changes.
"""

import os

import pandas as pd


def quick_check_dataset(dataset_name: str, csv_path: str, media_dir: str):
    """Quick check of a single dataset"""
    print(f"\n📋 {dataset_name.upper()}")
    print("-" * 30)

    # Check CSV
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        print(f"   📄 CSV: ✅ {len(df):,} records")

        # Count expected media
        expected_photos = set()
        expected_videos = set()

        for _, row in df.iterrows():
            for i in range(1, 10):
                photo_col = f"photo{i}_local_path"
                if (
                    photo_col in row
                    and pd.notna(row[photo_col])
                    and row[photo_col].strip()
                ):
                    expected_photos.add(os.path.basename(row[photo_col].strip()))

            for i in range(1, 6):
                video_col = f"video{i}_local_path"
                if (
                    video_col in row
                    and pd.notna(row[video_col])
                    and row[video_col].strip()
                ):
                    expected_videos.add(os.path.basename(row[video_col].strip()))

        print(f"   📸 Expected photos: {len(expected_photos)}")
        print(f"   🎥 Expected videos: {len(expected_videos)}")

    else:
        print("   📄 CSV: ❌ Not found")
        return

    # Check media directory
    if os.path.exists(media_dir):
        photos_dir = os.path.join(media_dir, "photos")
        videos_dir = os.path.join(media_dir, "videos")

        actual_photos = 0
        actual_videos = 0

        if os.path.exists(photos_dir):
            actual_photos = len(
                [
                    f
                    for f in os.listdir(photos_dir)
                    if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
                ]
            )

        if os.path.exists(videos_dir):
            actual_videos = len(
                [
                    f
                    for f in os.listdir(videos_dir)
                    if f.lower().endswith((".mp4", ".avi", ".mov", ".webm"))
                ]
            )

        print(f"   📁 Actual photos: {actual_photos}")
        print(f"   📁 Actual videos: {actual_videos}")

        # Check correspondence
        photos_match = len(expected_photos) == actual_photos
        videos_match = len(expected_videos) == actual_videos

        if photos_match and videos_match:
            print("   ✅ Status: PERFECT")
        else:
            print("   ⚠️  Status: MISMATCH")
            if not photos_match:
                print(
                    f"      📸 Photo mismatch: expected {len(expected_photos)}, found {actual_photos}"
                )
            if not videos_match:
                print(
                    f"      🎥 Video mismatch: expected {len(expected_videos)}, found {actual_videos}"
                )
    else:
        print("   📁 Media dir: ❌ Not found")


def main():
    print("🔍 Quick Status Check - Cleaned Twitter Datasets")
    print("=" * 50)

    datasets = {
        "assam_flood": {
            "csv": "twitter/assam_flood/csvs/cleaned_assam_flood_tweets.csv",
            "media": "twitter/assam_flood/media_cleaned",
        },
        "bangladesh_flood": {
            "csv": "twitter/bangladesh_flood/csvs/cleaned_bangladesh_flood_tweets.csv",
            "media": "twitter/bangladesh_flood/media_cleaned",
        },
        "kerala_flood": {
            "csv": "twitter/kerala_flood/csvs/cleaned_kerala_flood_tweets.csv",
            "media": "twitter/kerala_flood/media_cleaned",
        },
        "pakistan_flood": {
            "csv": "twitter/pakistan_flood/csvs/cleaned_pakistan_flood_tweets.csv",
            "media": "twitter/pakistan_flood/media_cleaned",
        },
    }

    total_records = 0
    perfect_datasets = 0

    for dataset_name, config in datasets.items():
        quick_check_dataset(dataset_name, config["csv"], config["media"])

        # Count records
        if os.path.exists(config["csv"]):
            df = pd.read_csv(config["csv"])
            total_records += len(df)

            # Check if perfect
            if os.path.exists(config["media"]):
                # Quick correspondence check
                expected_photos = set()
                expected_videos = set()

                for _, row in df.iterrows():
                    for i in range(1, 10):
                        photo_col = f"photo{i}_local_path"
                        if (
                            photo_col in row
                            and pd.notna(row[photo_col])
                            and row[photo_col].strip()
                        ):
                            expected_photos.add(
                                os.path.basename(row[photo_col].strip())
                            )

                    for i in range(1, 6):
                        video_col = f"video{i}_local_path"
                        if (
                            video_col in row
                            and pd.notna(row[video_col])
                            and row[video_col].strip()
                        ):
                            expected_videos.add(
                                os.path.basename(row[video_col].strip())
                            )

                photos_dir = os.path.join(config["media"], "photos")
                videos_dir = os.path.join(config["media"], "videos")

                actual_photos = 0
                actual_videos = 0

                if os.path.exists(photos_dir):
                    actual_photos = len(
                        [
                            f
                            for f in os.listdir(photos_dir)
                            if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
                        ]
                    )

                if os.path.exists(videos_dir):
                    actual_videos = len(
                        [
                            f
                            for f in os.listdir(videos_dir)
                            if f.lower().endswith((".mp4", ".avi", ".mov", ".webm"))
                        ]
                    )

                if (
                    len(expected_photos) == actual_photos
                    and len(expected_videos) == actual_videos
                ):
                    perfect_datasets += 1

    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    print(f"   📄 Total cleaned records: {total_records:,}")
    print(f"   ✅ Perfect datasets: {perfect_datasets}/4")
    print(f"   ⚠️  Datasets with issues: {4 - perfect_datasets}/4")

    if perfect_datasets == 4:
        print("\n🎉 All datasets are perfect! You're ready to use the cleaned data.")
    else:
        print("\n🔧 Some datasets have media correspondence issues.")
        print("   Run: python twitter/fix_media_correspondence.py")
        print("   This will fix the issues without re-running AI classification.")

    # Check if original cleaning report exists
    if os.path.exists("twitter/cleaning_report.json"):
        print("\n📄 Original cleaning report available: twitter/cleaning_report.json")

    # Check classification logs
    print("\n📜 Classification logs:")
    for dataset_name in datasets.keys():
        log_path = f"twitter/{dataset_name}/csvs/cleaned_{dataset_name}_tweets_classification_log.json"
        if os.path.exists(log_path):
            print(f"   ✅ {dataset_name}: Available")
        else:
            print(f"   ❌ {dataset_name}: Missing")


if __name__ == "__main__":
    main()
