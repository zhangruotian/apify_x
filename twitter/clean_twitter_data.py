#!/usr/bin/env python3
"""
Twitter Flood Data Cleaning Script

This script uses OpenAI API to classify Twitter posts and filter out
non-flood disaster related content. It processes CSV files and creates
new cleaned datasets with corresponding media files.
"""

import json
import os
import shutil
import time
from typing import Dict, List, Tuple

import pandas as pd
from openai import OpenAI

# Configuration
DATASETS = {
    "assam_flood": {
        "csv_path": "twitter/assam_flood/csvs/filtered_assam_flood_tweets_20240501_20240801_with_local_paths_20250721_172531.csv",
        "media_dir": "twitter/assam_flood/media",
        "output_csv": "twitter/assam_flood/csvs/cleaned_assam_flood_tweets.csv",
        "output_media_dir": "twitter/assam_flood/media_cleaned",
    },
    "bangladesh_flood": {
        "csv_path": "twitter/bangladesh_flood/csvs/filtered_tweets_aug_to_oct_2024_with_local_paths_20250604_133037.csv",
        "media_dir": "twitter/bangladesh_flood/media",
        "output_csv": "twitter/bangladesh_flood/csvs/cleaned_bangladesh_flood_tweets.csv",
        "output_media_dir": "twitter/bangladesh_flood/media_cleaned",
    },
    "kerala_flood": {
        "csv_path": "twitter/kerala_flood/csvs/filtered_kerala_flood_tweets_20240715_20240901_with_local_paths_20250721_181731.csv",
        "media_dir": "twitter/kerala_flood/media",
        "output_csv": "twitter/kerala_flood/csvs/cleaned_kerala_flood_tweets.csv",
        "output_media_dir": "twitter/kerala_flood/media_cleaned",
    },
    "pakistan_flood": {
        "csv_path": "twitter/pakistan_flood/csvs/filtered_pakistan_flood_tweets_20220601_20221101_with_local_paths_20250721_175020.csv",
        "media_dir": "twitter/pakistan_flood/media",
        "output_csv": "twitter/pakistan_flood/csvs/cleaned_pakistan_flood_tweets.csv",
        "output_media_dir": "twitter/pakistan_flood/media_cleaned",
    },
}


def setup_openai_client():
    """Setup OpenAI client with API key from environment variable"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)


def classify_tweet_content(
    client: OpenAI, tweet_text: str, hashtags: str = "", max_retries: int = 3
) -> Tuple[bool, str]:
    """
    Use OpenAI API to classify if a tweet is about flood disasters.

    Args:
        client: OpenAI client instance
        tweet_text: The tweet text content
        hashtags: Hashtags from the tweet
        max_retries: Maximum number of retries for API calls

    Returns:
        Tuple of (is_flood_related: bool, reasoning: str)
    """

    # Combine text and hashtags for analysis
    full_content = f"Tweet: {tweet_text}"
    if hashtags:
        full_content += f"\nHashtags: {hashtags}"

    prompt = f"""
You are analyzing social media content to determine if it's about flood disasters (natural calamities involving flooding).

Please analyze the following content and determine if it's about FLOOD DISASTERS specifically:

{full_content}

Criteria for flood disaster content:
- Must be about actual flooding events (water overflow, inundation, submersion)
- Natural disasters involving floods (rivers overflowing, heavy rain flooding, etc.)
- Flood damage, rescue operations, flood relief efforts
- Flood warnings, flood monitoring, flood management

NOT flood disaster content:
- Metaphorical use of "flood" (flood of emotions, flood of messages)
- Non-disaster floods (artificial flooding, controlled flooding)
- Other natural disasters without flooding (earthquakes, fires without flooding)
- General weather reports without flooding
- Political content using flood metaphors

Respond with a JSON object:
{{
    "is_flood_related": true/false,
    "reasoning": "Brief explanation of your decision",
    "confidence": "high/medium/low"
}}
"""

    for attempt in range(max_retries):
        try:
            print(
                f"🔄 Making API call (attempt {attempt + 1}/{max_retries})...",
                end=" ",
                flush=True,
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at classifying social media content about natural disasters.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_tokens=150,
                timeout=30,  # 30 second timeout
            )

            print("✅ Success")
            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            try:
                result = json.loads(result_text)
                return result["is_flood_related"], result["reasoning"]
            except json.JSONDecodeError:
                # Fallback: look for true/false in response
                if "true" in result_text.lower():
                    return True, result_text
                else:
                    return False, result_text

        except Exception as e:
            print(f"❌ Failed: {str(e)[:50]}...")
            if attempt < max_retries - 1:
                wait_time = 2**attempt
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)  # Exponential backoff
            else:
                # Default to keeping the tweet if classification fails
                print("⚠️ All API attempts failed, defaulting to keep tweet")
                return True, f"Classification failed after {max_retries} attempts: {e}"


def get_media_paths_from_row(row: pd.Series) -> List[str]:
    """Extract all media file paths from a CSV row"""
    media_paths = []

    # Check photo paths
    for i in range(1, 10):  # photo1 to photo9
        photo_col = f"photo{i}_local_path"
        if photo_col in row and pd.notna(row[photo_col]) and row[photo_col].strip():
            media_paths.append(row[photo_col].strip())

    # Check video paths
    for i in range(1, 6):  # video1 to video5
        video_col = f"video{i}_local_path"
        if video_col in row and pd.notna(row[video_col]) and row[video_col].strip():
            media_paths.append(row[video_col].strip())

    return media_paths


def copy_media_files(
    media_paths: List[str], source_media_dir: str, dest_media_dir: str
) -> List[str]:
    """Copy media files from source to destination directory"""
    copied_files = []

    # Create destination directories
    os.makedirs(os.path.join(dest_media_dir, "photos"), exist_ok=True)
    os.makedirs(os.path.join(dest_media_dir, "videos"), exist_ok=True)

    for media_path in media_paths:
        if not media_path:
            continue

        # Convert relative path to absolute
        source_file = media_path
        if not os.path.isabs(source_file):
            source_file = os.path.join(os.getcwd(), source_file)

        if os.path.exists(source_file):
            # Determine destination based on file extension
            filename = os.path.basename(source_file)
            if filename.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                dest_file = os.path.join(dest_media_dir, "photos", filename)
            elif filename.lower().endswith((".mp4", ".avi", ".mov", ".webm")):
                dest_file = os.path.join(dest_media_dir, "videos", filename)
            else:
                continue

            try:
                shutil.copy2(source_file, dest_file)
                copied_files.append(dest_file)
            except Exception as e:
                print(f"Failed to copy {source_file}: {e}")

    return copied_files


def update_media_paths_in_row(row: pd.Series, dest_media_dir: str) -> pd.Series:
    """Update media paths in the row to point to new cleaned directory"""
    updated_row = row.copy()

    # Update photo paths
    for i in range(1, 10):
        photo_col = f"photo{i}_local_path"
        if (
            photo_col in updated_row
            and pd.notna(updated_row[photo_col])
            and updated_row[photo_col].strip()
        ):
            original_path = updated_row[photo_col].strip()
            filename = os.path.basename(original_path)
            if filename.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                updated_row[photo_col] = os.path.join(
                    dest_media_dir, "photos", filename
                )

    # Update video paths
    for i in range(1, 6):
        video_col = f"video{i}_local_path"
        if (
            video_col in updated_row
            and pd.notna(updated_row[video_col])
            and updated_row[video_col].strip()
        ):
            original_path = updated_row[video_col].strip()
            filename = os.path.basename(original_path)
            if filename.lower().endswith((".mp4", ".avi", ".mov", ".webm")):
                updated_row[video_col] = os.path.join(
                    dest_media_dir, "videos", filename
                )

    return updated_row


def clean_dataset(dataset_name: str, config: Dict, client: OpenAI) -> Dict:
    """
    Clean a single dataset by filtering flood-related content

    Returns statistics about the cleaning process
    """
    print(f"\n🔄 Processing {dataset_name}...")

    # Load CSV
    df = pd.read_csv(config["csv_path"])
    total_records = len(df)
    print(f"📊 Total records: {total_records}")

    # Prepare for classification
    cleaned_rows = []
    removed_count = 0
    classification_log = []

    for idx, row in df.iterrows():
        # Show progress every record for better visibility
        progress_pct = ((idx + 1) / total_records) * 100
        print(f"\n🔍 Processing record {idx + 1}/{total_records} ({progress_pct:.1f}%)")
        print(f"   📝 Tweet ID: {row['tweet_id']}")

        # Extract content for classification
        tweet_text = str(row["text"]) if pd.notna(row["text"]) else ""
        print(f"   📄 Text preview: {tweet_text[:80]}...")

        # Extract hashtags (concatenate hashtag1-10)
        hashtags = []
        for i in range(1, 11):
            hashtag_col = f"hashtag{i}"
            if hashtag_col in row and pd.notna(row[hashtag_col]):
                hashtags.append(str(row[hashtag_col]))
        hashtags_str = " ".join(hashtags)
        if hashtags_str:
            print(f"   🏷️  Hashtags: {hashtags_str}")

        # Classify the tweet
        print("   🤖 Classifying with OpenAI...", end=" ")
        is_flood_related, reasoning = classify_tweet_content(
            client, tweet_text, hashtags_str
        )

        # Show classification result
        result_emoji = "✅" if is_flood_related else "❌"
        action = "KEEP" if is_flood_related else "REMOVE"
        print(f"\n   {result_emoji} Decision: {action}")
        print(f"   💭 Reasoning: {reasoning[:100]}...")

        classification_log.append(
            {
                "tweet_id": row["tweet_id"],
                "is_flood_related": is_flood_related,
                "reasoning": reasoning,
                "text_preview": (
                    tweet_text[:100] + "..." if len(tweet_text) > 100 else tweet_text
                ),
            }
        )

        if is_flood_related:
            # Get media paths
            media_paths = get_media_paths_from_row(row)
            if media_paths:
                print(f"   📁 Media files to copy: {len(media_paths)}")

            # Copy media files
            copied_files = copy_media_files(
                media_paths, config["media_dir"], config["output_media_dir"]
            )

            # Update media paths in row
            updated_row = update_media_paths_in_row(row, config["output_media_dir"])

            cleaned_rows.append(updated_row)
        else:
            removed_count += 1

        # Show running statistics
        kept_so_far = len(cleaned_rows)
        print(f"   📊 Running total: {kept_so_far} kept, {removed_count} removed")

    # Create cleaned DataFrame
    if cleaned_rows:
        cleaned_df = pd.DataFrame(cleaned_rows)

        # Save cleaned CSV
        os.makedirs(os.path.dirname(config["output_csv"]), exist_ok=True)
        cleaned_df.to_csv(config["output_csv"], index=False)

        kept_count = len(cleaned_df)
    else:
        kept_count = 0

    # Save classification log
    log_path = config["output_csv"].replace(".csv", "_classification_log.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(classification_log, f, indent=2, ensure_ascii=False)

    print(f"✅ {dataset_name} completed:")
    print(f"   📥 Original records: {total_records}")
    print(f"   📤 Kept records: {kept_count}")
    print(f"   🗑️  Removed records: {removed_count}")
    print(f"   📊 Removal rate: {removed_count/total_records*100:.1f}%")

    return {
        "dataset": dataset_name,
        "total_records": total_records,
        "kept_records": kept_count,
        "removed_records": removed_count,
        "removal_rate": removed_count / total_records * 100,
        "output_csv": config["output_csv"],
        "output_media_dir": config["output_media_dir"],
        "classification_log": log_path,
    }


def verify_data_correspondence(dataset_stats: List[Dict]) -> Dict:
    """Verify that CSV records and media files correspond correctly"""
    print("\n🔍 Verifying data correspondence...")

    verification_results = {}

    for stats in dataset_stats:
        dataset_name = stats["dataset"]
        csv_path = stats["output_csv"]
        media_dir = stats["output_media_dir"]

        print(f"\n📋 Verifying {dataset_name}...")

        if not os.path.exists(csv_path):
            print(f"❌ CSV file not found: {csv_path}")
            continue

        # Load cleaned CSV
        df = pd.read_csv(csv_path)

        # Count expected media files from CSV
        expected_photos = set()
        expected_videos = set()

        for _, row in df.iterrows():
            # Check photo paths
            for i in range(1, 10):
                photo_col = f"photo{i}_local_path"
                if (
                    photo_col in row
                    and pd.notna(row[photo_col])
                    and row[photo_col].strip()
                ):
                    expected_photos.add(os.path.basename(row[photo_col].strip()))

            # Check video paths
            for i in range(1, 6):
                video_col = f"video{i}_local_path"
                if (
                    video_col in row
                    and pd.notna(row[video_col])
                    and row[video_col].strip()
                ):
                    expected_videos.add(os.path.basename(row[video_col].strip()))

        # Count actual media files
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

        # Compare expected vs actual
        missing_photos = expected_photos - actual_photos
        extra_photos = actual_photos - expected_photos
        missing_videos = expected_videos - actual_videos
        extra_videos = actual_videos - expected_videos

        verification_results[dataset_name] = {
            "csv_records": len(df),
            "expected_photos": len(expected_photos),
            "actual_photos": len(actual_photos),
            "expected_videos": len(expected_videos),
            "actual_videos": len(actual_videos),
            "missing_photos": len(missing_photos),
            "extra_photos": len(extra_photos),
            "missing_videos": len(missing_videos),
            "extra_videos": len(extra_videos),
            "photos_match": len(missing_photos) == 0 and len(extra_photos) == 0,
            "videos_match": len(missing_videos) == 0 and len(extra_videos) == 0,
        }

        print(f"   📊 CSV records: {len(df)}")
        print(
            f"   📸 Photos - Expected: {len(expected_photos)}, Actual: {len(actual_photos)}"
        )
        print(
            f"   🎥 Videos - Expected: {len(expected_videos)}, Actual: {len(actual_videos)}"
        )

        if missing_photos:
            print(f"   ⚠️  Missing photos: {len(missing_photos)}")
        if extra_photos:
            print(f"   ⚠️  Extra photos: {len(extra_photos)}")
        if missing_videos:
            print(f"   ⚠️  Missing videos: {len(missing_videos)}")
        if extra_videos:
            print(f"   ⚠️  Extra videos: {len(extra_videos)}")

        if (
            verification_results[dataset_name]["photos_match"]
            and verification_results[dataset_name]["videos_match"]
        ):
            print("   ✅ Perfect correspondence!")
        else:
            print("   ❌ Data correspondence issues detected")

    return verification_results


def generate_final_report(dataset_stats: List[Dict], verification_results: Dict):
    """Generate final cleaning report"""
    print("\n" + "=" * 60)
    print("📊 TWITTER DATA CLEANING FINAL REPORT")
    print("=" * 60)

    total_original = sum(stats["total_records"] for stats in dataset_stats)
    total_kept = sum(stats["kept_records"] for stats in dataset_stats)
    total_removed = sum(stats["removed_records"] for stats in dataset_stats)

    print("\n🔢 OVERALL STATISTICS:")
    print(f"   📥 Total original records: {total_original:,}")
    print(f"   📤 Total kept records: {total_kept:,}")
    print(f"   🗑️  Total removed records: {total_removed:,}")
    print(f"   📊 Overall removal rate: {total_removed/total_original*100:.1f}%")

    print("\n📋 DATASET BREAKDOWN:")
    for stats in dataset_stats:
        print(f"\n   🏷️  {stats['dataset'].upper()}:")
        print(f"      📥 Original: {stats['total_records']:,}")
        print(f"      📤 Kept: {stats['kept_records']:,}")
        print(
            f"      🗑️  Removed: {stats['removed_records']:,} ({stats['removal_rate']:.1f}%)"
        )
        print(f"      📄 Output CSV: {stats['output_csv']}")
        print(f"      📁 Output Media: {stats['output_media_dir']}")

    print("\n🔍 DATA CORRESPONDENCE VERIFICATION:")
    for dataset_name, result in verification_results.items():
        status = (
            "✅ PERFECT"
            if (result["photos_match"] and result["videos_match"])
            else "❌ ISSUES"
        )
        print(f"   {dataset_name.upper()}: {status}")
        if not (result["photos_match"] and result["videos_match"]):
            print(
                f"      Missing photos: {result['missing_photos']}, Extra photos: {result['extra_photos']}"
            )
            print(
                f"      Missing videos: {result['missing_videos']}, Extra videos: {result['extra_videos']}"
            )

    # Save report to file
    report_path = "twitter/cleaning_report.json"
    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "overall_stats": {
            "total_original": total_original,
            "total_kept": total_kept,
            "total_removed": total_removed,
            "removal_rate": total_removed / total_original * 100,
        },
        "dataset_stats": dataset_stats,
        "verification_results": verification_results,
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Full report saved to: {report_path}")
    print("=" * 60)


def main():
    """Main execution function"""
    print("🚀 Starting Twitter Flood Data Cleaning Process")
    print("=" * 50)

    # Setup OpenAI client
    try:
        client = setup_openai_client()
        print("✅ OpenAI client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize OpenAI client: {e}")
        return

    # Process each dataset
    dataset_stats = []

    for dataset_name, config in DATASETS.items():
        try:
            stats = clean_dataset(dataset_name, config, client)
            dataset_stats.append(stats)
        except Exception as e:
            print(f"❌ Failed to process {dataset_name}: {e}")
            continue

    # Verify data correspondence
    try:
        verification_results = verify_data_correspondence(dataset_stats)
    except Exception as e:
        print(f"❌ Failed to verify data correspondence: {e}")
        verification_results = {}

    # Generate final report
    generate_final_report(dataset_stats, verification_results)

    print("\n🎉 Twitter data cleaning process completed!")


if __name__ == "__main__":
    main()
