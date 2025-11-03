#!/usr/bin/env python3
"""
Fix Media Correspondence Script

This script checks the cleaned datasets and fixes media file correspondence issues
without re-running the expensive AI classification process.
"""

import json
import os
import shutil

import pandas as pd


def check_cleaned_dataset_status(
    dataset_name: str, output_csv: str, output_media_dir: str, original_media_dir: str
):
    """
    Check the status of a cleaned dataset and fix media correspondence if needed
    """
    print(f"\n🔍 Checking {dataset_name.upper()} cleaned dataset...")
    print("=" * 50)

    # Check if cleaned CSV exists
    if not os.path.exists(output_csv):
        print(f"❌ Cleaned CSV not found: {output_csv}")
        return False

    # Load cleaned CSV
    df = pd.read_csv(output_csv)
    print(f"📄 Cleaned CSV loaded: {len(df)} records")

    # Check cleaned media directory
    if not os.path.exists(output_media_dir):
        print(f"❌ Cleaned media directory not found: {output_media_dir}")
        return False

    # Analyze expected vs actual media files
    expected_photos, expected_videos = get_expected_media_from_csv(df)
    actual_photos, actual_videos = get_actual_media_from_dir(output_media_dir)

    print(f"📸 Photos - Expected: {len(expected_photos)}, Actual: {len(actual_photos)}")
    print(f"🎥 Videos - Expected: {len(expected_videos)}, Actual: {len(actual_videos)}")

    missing_photos = expected_photos - actual_photos
    missing_videos = expected_videos - actual_videos

    print(f"🔴 Missing photos: {len(missing_photos)}")
    print(f"🔴 Missing videos: {len(missing_videos)}")

    if len(missing_photos) == 0 and len(missing_videos) == 0:
        print("✅ Perfect correspondence - no action needed!")
        return True

    # If there are missing files, try to fix them
    print("\n🔧 Attempting to fix missing media files...")
    fixed_photos = fix_missing_media(
        missing_photos, original_media_dir, output_media_dir, "photos"
    )
    fixed_videos = fix_missing_media(
        missing_videos, original_media_dir, output_media_dir, "videos"
    )

    print(f"✅ Fixed photos: {fixed_photos}/{len(missing_photos)}")
    print(f"✅ Fixed videos: {fixed_videos}/{len(missing_videos)}")

    # Re-check after fixing
    actual_photos_after, actual_videos_after = get_actual_media_from_dir(
        output_media_dir
    )
    missing_photos_after = expected_photos - actual_photos_after
    missing_videos_after = expected_videos - actual_videos_after

    if len(missing_photos_after) == 0 and len(missing_videos_after) == 0:
        print("🎉 All media files fixed successfully!")
        return True
    else:
        print(
            f"⚠️ Still missing: {len(missing_photos_after)} photos, {len(missing_videos_after)} videos"
        )
        return False


def get_expected_media_from_csv(df: pd.DataFrame) -> tuple:
    """Extract expected media files from cleaned CSV"""
    expected_photos = set()
    expected_videos = set()

    for _, row in df.iterrows():
        # Check photo paths
        for i in range(1, 10):
            photo_col = f"photo{i}_local_path"
            if photo_col in row and pd.notna(row[photo_col]) and row[photo_col].strip():
                filename = os.path.basename(row[photo_col].strip())
                expected_photos.add(filename)

        # Check video paths
        for i in range(1, 6):
            video_col = f"video{i}_local_path"
            if video_col in row and pd.notna(row[video_col]) and row[video_col].strip():
                filename = os.path.basename(row[video_col].strip())
                expected_videos.add(filename)

    return expected_photos, expected_videos


def get_actual_media_from_dir(media_dir: str) -> tuple:
    """Get actual media files from directory"""
    photos_dir = os.path.join(media_dir, "photos")
    videos_dir = os.path.join(media_dir, "videos")

    actual_photos = set()
    actual_videos = set()

    if os.path.exists(photos_dir):
        actual_photos = set(
            [
                f
                for f in os.listdir(photos_dir)
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
            ]
        )

    if os.path.exists(videos_dir):
        actual_videos = set(
            [
                f
                for f in os.listdir(videos_dir)
                if f.lower().endswith((".mp4", ".avi", ".mov", ".webm"))
            ]
        )

    return actual_photos, actual_videos


def fix_missing_media(
    missing_files: set, original_media_dir: str, output_media_dir: str, media_type: str
) -> int:
    """
    Fix missing media files by copying from original directory
    """
    if not missing_files:
        return 0

    original_subdir = os.path.join(original_media_dir, media_type)
    output_subdir = os.path.join(output_media_dir, media_type)

    if not os.path.exists(original_subdir):
        print(f"⚠️ Original {media_type} directory not found: {original_subdir}")
        return 0

    # Create output directory if it doesn't exist
    os.makedirs(output_subdir, exist_ok=True)

    fixed_count = 0

    for filename in missing_files:
        source_file = os.path.join(original_subdir, filename)
        dest_file = os.path.join(output_subdir, filename)

        if os.path.exists(source_file):
            try:
                shutil.copy2(source_file, dest_file)
                fixed_count += 1
                print(f"   ✅ Copied: {filename}")
            except Exception as e:
                print(f"   ❌ Failed to copy {filename}: {e}")
        else:
            print(f"   ⚠️ Source file not found: {filename}")

    return fixed_count


def verify_all_cleaned_datasets():
    """
    Check all cleaned datasets and fix any media correspondence issues
    """
    print("🔧 Media Correspondence Fixer")
    print("=" * 40)
    print(
        "This script checks and fixes cleaned datasets without re-running AI classification."
    )

    datasets = {
        "assam_flood": {
            "output_csv": "twitter/assam_flood/csvs/cleaned_assam_flood_tweets.csv",
            "output_media_dir": "twitter/assam_flood/media_cleaned",
            "original_media_dir": "twitter/assam_flood/media",
        },
        "bangladesh_flood": {
            "output_csv": "twitter/bangladesh_flood/csvs/cleaned_bangladesh_flood_tweets.csv",
            "output_media_dir": "twitter/bangladesh_flood/media_cleaned",
            "original_media_dir": "twitter/bangladesh_flood/media",
        },
        "kerala_flood": {
            "output_csv": "twitter/kerala_flood/csvs/cleaned_kerala_flood_tweets.csv",
            "output_media_dir": "twitter/kerala_flood/media_cleaned",
            "original_media_dir": "twitter/kerala_flood/media",
        },
        "pakistan_flood": {
            "output_csv": "twitter/pakistan_flood/csvs/cleaned_pakistan_flood_tweets.csv",
            "output_media_dir": "twitter/pakistan_flood/media_cleaned",
            "original_media_dir": "twitter/pakistan_flood/media",
        },
    }

    results = {}

    for dataset_name, config in datasets.items():
        try:
            success = check_cleaned_dataset_status(
                dataset_name,
                config["output_csv"],
                config["output_media_dir"],
                config["original_media_dir"],
            )
            results[dataset_name] = success
        except Exception as e:
            print(f"❌ Error processing {dataset_name}: {e}")
            results[dataset_name] = False

    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL STATUS SUMMARY")
    print("=" * 60)

    all_good = True
    for dataset_name, success in results.items():
        status = "✅ PERFECT" if success else "❌ ISSUES"
        print(f"   {dataset_name.upper()}: {status}")
        if not success:
            all_good = False

    if all_good:
        print("\n🎉 All datasets have perfect correspondence!")
        print("✅ Ready to use cleaned data!")
    else:
        print("\n⚠️ Some datasets still have issues.")
        print("💡 Check the detailed output above for specific problems.")

    return results


def show_cleaned_dataset_summary():
    """
    Show summary of all cleaned datasets
    """
    print("\n📋 CLEANED DATASETS SUMMARY")
    print("=" * 40)

    datasets = {
        "assam_flood": "twitter/assam_flood/csvs/cleaned_assam_flood_tweets.csv",
        "bangladesh_flood": "twitter/bangladesh_flood/csvs/cleaned_bangladesh_flood_tweets.csv",
        "kerala_flood": "twitter/kerala_flood/csvs/cleaned_kerala_flood_tweets.csv",
        "pakistan_flood": "twitter/pakistan_flood/csvs/cleaned_pakistan_flood_tweets.csv",
    }

    total_cleaned_records = 0

    for dataset_name, csv_path in datasets.items():
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            record_count = len(df)
            total_cleaned_records += record_count
            print(f"   📄 {dataset_name.upper()}: {record_count:,} cleaned records")
        else:
            print(f"   ❌ {dataset_name.upper()}: CSV not found")

    print(f"\n📊 Total cleaned records across all datasets: {total_cleaned_records:,}")

    # Check if classification logs exist
    print("\n📜 Classification logs:")
    for dataset_name in datasets.keys():
        log_path = f"twitter/{dataset_name}/csvs/cleaned_{dataset_name}_tweets_classification_log.json"
        if os.path.exists(log_path):
            print(f"   ✅ {dataset_name.upper()}: Log available")
        else:
            print(f"   ❌ {dataset_name.upper()}: Log missing")


def main():
    """
    Main execution function
    """
    print("🔧 Twitter Cleaned Data Verification & Repair Tool")
    print("=" * 60)
    print("This tool checks your cleaned datasets and fixes media file issues")
    print("without re-running the expensive AI classification process.")
    print("=" * 60)

    # Show current status
    show_cleaned_dataset_summary()

    # Check and fix all datasets
    results = verify_all_cleaned_datasets()

    # Save results report
    report_path = "twitter/media_fix_report.json"
    report_data = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "results": results,
        "summary": "Fixed media correspondence for cleaned datasets",
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Fix report saved to: {report_path}")

    if all(results.values()):
        print("\n🎉 SUCCESS: All cleaned datasets are ready to use!")
        print("✅ You can now proceed with your analysis.")
    else:
        print("\n⚠️ Some issues remain. Check the detailed output above.")


if __name__ == "__main__":
    main()
