#!/usr/bin/env python3
"""
Debug script to analyze media file correspondence issues
"""

import os

import pandas as pd


def debug_media_correspondence(dataset_name: str, csv_path: str, media_dir: str):
    """
    Debug media file correspondence for a specific dataset
    """
    print(f"\n🔍 Debugging {dataset_name.upper()} media correspondence")
    print("=" * 60)

    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return

    # Load CSV
    df = pd.read_csv(csv_path)
    print(f"📊 Total CSV records: {len(df)}")

    # Analyze photo correspondence
    print("\n📸 PHOTO ANALYSIS:")
    analyze_media_type(
        df,
        media_dir,
        "photos",
        ["photo" + str(i) + "_local_path" for i in range(1, 10)],
    )

    # Analyze video correspondence
    print("\n🎥 VIDEO ANALYSIS:")
    analyze_media_type(
        df, media_dir, "videos", ["video" + str(i) + "_local_path" for i in range(1, 6)]
    )


def analyze_media_type(
    df: pd.DataFrame, media_dir: str, media_type: str, path_columns: list
):
    """
    Analyze correspondence for a specific media type (photos or videos)
    """
    media_subdir = os.path.join(media_dir, media_type)

    # Collect expected files from CSV
    expected_files = set()
    csv_references = []

    for _, row in df.iterrows():
        for col in path_columns:
            if col in row and pd.notna(row[col]) and row[col].strip():
                file_path = row[col].strip()
                filename = os.path.basename(file_path)
                expected_files.add(filename)
                csv_references.append(
                    {
                        "tweet_id": row["tweet_id"],
                        "column": col,
                        "path": file_path,
                        "filename": filename,
                    }
                )

    print(f"   📄 CSV references: {len(csv_references)}")
    print(f"   📁 Unique expected files: {len(expected_files)}")

    # Check what actually exists in media directory
    actual_files = set()
    if os.path.exists(media_subdir):
        if media_type == "photos":
            extensions = (".jpg", ".jpeg", ".png", ".gif")
        else:  # videos
            extensions = (".mp4", ".avi", ".mov", ".webm")

        actual_files = set(
            [f for f in os.listdir(media_subdir) if f.lower().endswith(extensions)]
        )
        print(f"   💾 Actual files found: {len(actual_files)}")
    else:
        print(f"   ❌ Media directory not found: {media_subdir}")
        return

    # Find missing and extra files
    missing_files = expected_files - actual_files
    extra_files = actual_files - expected_files

    print(f"   🔴 Missing files: {len(missing_files)}")
    print(f"   🟡 Extra files: {len(extra_files)}")

    # Show sample missing files and their CSV references
    if missing_files:
        print("\n   📋 Sample missing files (first 10):")
        for i, missing_file in enumerate(list(missing_files)[:10]):
            print(f"      {i+1}. {missing_file}")

            # Find which CSV records reference this missing file
            referencing_tweets = [
                ref for ref in csv_references if ref["filename"] == missing_file
            ]
            for ref in referencing_tweets[:2]:  # Show first 2 references
                print(
                    f"         → Tweet {ref['tweet_id']} in {ref['column']}: {ref['path']}"
                )

    # Show sample extra files
    if extra_files:
        print("\n   📋 Sample extra files (first 10):")
        for i, extra_file in enumerate(list(extra_files)[:10]):
            print(f"      {i+1}. {extra_file}")

    # Analyze path patterns
    print("\n   🔍 Path analysis:")
    path_patterns = {}
    for ref in csv_references:
        path_dir = os.path.dirname(ref["path"])
        if path_dir in path_patterns:
            path_patterns[path_dir] += 1
        else:
            path_patterns[path_dir] = 1

    print("      Path patterns in CSV:")
    for pattern, count in sorted(
        path_patterns.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"        {pattern}: {count} files")


def check_path_formats(csv_path: str):
    """
    Check the format of media paths in CSV
    """
    print("\n📝 PATH FORMAT ANALYSIS")
    print("=" * 30)

    df = pd.read_csv(csv_path)

    # Sample some media paths
    media_columns = []
    for i in range(1, 10):
        media_columns.append(f"photo{i}_local_path")
    for i in range(1, 6):
        media_columns.append(f"video{i}_local_path")

    sample_paths = []
    for col in media_columns:
        if col in df.columns:
            non_null_paths = df[col].dropna()
            if len(non_null_paths) > 0:
                sample_paths.extend(non_null_paths.head(5).tolist())

    print("📋 Sample media paths from CSV:")
    for i, path in enumerate(sample_paths[:10]):
        if path and str(path).strip():
            print(f"   {i+1}. {path}")


def main():
    """
    Debug all datasets
    """
    print("🐛 Twitter Media Correspondence Debugger")
    print("=" * 50)

    datasets = {
        "assam_flood": {
            "csv": "twitter/assam_flood/csvs/filtered_assam_flood_tweets_20240501_20240801_with_local_paths_20250721_172531.csv",
            "media": "twitter/assam_flood/media",
        },
        "bangladesh_flood": {
            "csv": "twitter/bangladesh_flood/csvs/filtered_tweets_aug_to_oct_2024_with_local_paths_20250604_133037.csv",
            "media": "twitter/bangladesh_flood/media",
        },
        "kerala_flood": {
            "csv": "twitter/kerala_flood/csvs/filtered_kerala_flood_tweets_20240715_20240901_with_local_paths_20250721_181731.csv",
            "media": "twitter/kerala_flood/media",
        },
        "pakistan_flood": {
            "csv": "twitter/pakistan_flood/csvs/filtered_pakistan_flood_tweets_20220601_20221101_with_local_paths_20250721_175020.csv",
            "media": "twitter/pakistan_flood/media",
        },
    }

    # Focus on Bangladesh since it has issues
    print("🎯 Focusing on Bangladesh dataset (has issues):")
    debug_media_correspondence(
        "bangladesh_flood",
        datasets["bangladesh_flood"]["csv"],
        datasets["bangladesh_flood"]["media"],
    )

    # Check path formats
    check_path_formats(datasets["bangladesh_flood"]["csv"])

    # Quick check other datasets
    print("\n" + "=" * 60)
    print("📋 QUICK CHECK - OTHER DATASETS")
    print("=" * 60)

    for name, config in datasets.items():
        if name != "bangladesh_flood":
            print(f"\n🔍 {name.upper()}:")
            if os.path.exists(config["csv"]) and os.path.exists(config["media"]):
                df = pd.read_csv(config["csv"])

                # Count expected vs actual files quickly
                photos_dir = os.path.join(config["media"], "photos")
                videos_dir = os.path.join(config["media"], "videos")

                expected_photos = set()
                expected_videos = set()

                for _, row in df.iterrows():
                    for i in range(1, 10):
                        col = f"photo{i}_local_path"
                        if col in row and pd.notna(row[col]) and row[col].strip():
                            expected_photos.add(os.path.basename(row[col].strip()))

                    for i in range(1, 6):
                        col = f"video{i}_local_path"
                        if col in row and pd.notna(row[col]) and row[col].strip():
                            expected_videos.add(os.path.basename(row[col].strip()))

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

                print(
                    f"   📸 Photos: Expected {len(expected_photos)}, Found {actual_photos}"
                )
                print(
                    f"   🎥 Videos: Expected {len(expected_videos)}, Found {actual_videos}"
                )

                if (
                    len(expected_photos) == actual_photos
                    and len(expected_videos) == actual_videos
                ):
                    print("   ✅ Perfect correspondence")
                else:
                    print("   ⚠️  Potential issues")
            else:
                print("   ❌ Files not found")


if __name__ == "__main__":
    main()
