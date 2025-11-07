#!/usr/bin/env python3
"""
Clean Twitter flood datasets:
1. Remove rows with FILE_MISSING in video_key_frames
2. Remove orphaned media files (videos, key frames, photos) not referenced in CSV
3. Report statistics after cleaning
"""

import os
import json
import pandas as pd
from pathlib import Path
import shutil


def get_all_media_paths_from_csv(df, project_root):
    """
    Collect all media file paths referenced in CSV.
    
    Returns:
        tuple: (video_paths, key_frame_paths, photo_paths) as sets of absolute paths
    """
    video_paths = set()
    key_frame_paths = set()
    photo_paths = set()
    
    for idx, row in df.iterrows():
        # Get video paths
        for i in range(1, 6):
            video_col = f"video{i}_local_path"
            if pd.notna(row.get(video_col)) and str(row[video_col]).strip():
                video_path = str(row[video_col]).strip()
                # Convert to cleaned path
                if "/media/videos/" in video_path:
                    video_path = video_path.replace("/media/videos/", "/media_cleaned/videos/")
                elif video_path.startswith("media/videos/"):
                    # Extract dataset name from path if possible
                    dataset_name = "assam_flood"  # Default, will be detected from CSV path
                    video_path = f"twitter/{dataset_name}/media_cleaned/videos/{os.path.basename(video_path)}"
                
                abs_path = project_root / video_path
                if abs_path.exists():
                    video_paths.add(abs_path)
        
        # Get video key frames
        if pd.notna(row.get("video_key_frames")) and isinstance(row["video_key_frames"], str):
            video_frames_val = row["video_key_frames"]
            if video_frames_val.strip() and video_frames_val != "FILE_MISSING":
                try:
                    key_frames = json.loads(video_frames_val)
                    for frame_path in key_frames:
                        abs_path = project_root / frame_path
                        if abs_path.exists():
                            key_frame_paths.add(abs_path)
                except:
                    pass
        
        # Get photo paths (from photo columns and all_images)
        for i in range(1, 10):
            photo_col = f"photo{i}_local_path"
            if pd.notna(row.get(photo_col)) and str(row[photo_col]).strip():
                photo_path = str(row[photo_col]).strip()
                # Convert to cleaned path
                if "/media/photos/" in photo_path:
                    photo_path = photo_path.replace("/media/photos/", "/media_cleaned/photos/")
                elif photo_path.startswith("media/photos/"):
                    dataset_name = "assam_flood"  # Default
                    photo_path = f"twitter/{dataset_name}/media_cleaned/photos/{os.path.basename(photo_path)}"
                
                abs_path = project_root / photo_path
                if abs_path.exists():
                    photo_paths.add(abs_path)
        
        # Get all_images
        if pd.notna(row.get("all_images")) and isinstance(row["all_images"], str):
            all_images_val = row["all_images"]
            if all_images_val.strip():
                try:
                    all_images = json.loads(all_images_val)
                    for img_path in all_images:
                        abs_path = project_root / img_path
                        if abs_path.exists():
                            photo_paths.add(abs_path)
                except:
                    pass
    
    return video_paths, key_frame_paths, photo_paths


def clean_dataset(dataset_name, csv_path, project_root):
    """
    Clean a single dataset.
    
    Returns:
        dict with cleaning statistics
    """
    print(f"\n{'='*70}")
    print(f"🧹 Cleaning: {dataset_name}")
    print(f"{'='*70}")
    
    # Read CSV
    print(f"\n📖 Reading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    original_rows = len(df)
    print(f"   Original rows: {original_rows}")
    
    # Step 1: Remove rows with FILE_MISSING
    print(f"\n1️⃣  Removing rows with FILE_MISSING...")
    before_remove = len(df)
    df = df[df.get("video_key_frames", "") != "FILE_MISSING"]
    after_remove = len(df)
    removed_file_missing = before_remove - after_remove
    print(f"   Removed {removed_file_missing} rows with FILE_MISSING")
    print(f"   Remaining rows: {after_remove}")
    
    # Step 2: Collect all media paths referenced in CSV
    print(f"\n2️⃣  Collecting media paths from CSV...")
    video_paths, key_frame_paths, photo_paths = get_all_media_paths_from_csv(df, project_root)
    print(f"   Videos referenced: {len(video_paths)}")
    print(f"   Key frames referenced: {len(key_frame_paths)}")
    print(f"   Photos referenced: {len(photo_paths)}")
    
    # Step 3: Find media directories
    csv_parent = Path(csv_path).parent.parent
    media_cleaned_dir = csv_parent / "media_cleaned"
    
    if not media_cleaned_dir.exists():
        print(f"   ⚠️  media_cleaned directory not found: {media_cleaned_dir}")
        return {
            "dataset": dataset_name,
            "original_rows": original_rows,
            "removed_file_missing": removed_file_missing,
            "final_rows": after_remove,
            "orphaned_videos": 0,
            "orphaned_key_frames": 0,
            "orphaned_photos": 0
        }
    
    videos_dir = media_cleaned_dir / "videos"
    photos_dir = media_cleaned_dir / "photos"
    
    # Step 4: Find orphaned files
    print(f"\n3️⃣  Finding orphaned media files...")
    
    orphaned_videos = []
    if videos_dir.exists():
        for video_file in videos_dir.glob("*.mp4"):
            if video_file not in video_paths:
                orphaned_videos.append(video_file)
    
    orphaned_key_frames = []
    if photos_dir.exists():
        for frame_file in photos_dir.glob("*keyframe*.jpg"):
            if frame_file not in key_frame_paths:
                orphaned_key_frames.append(frame_file)
    
    orphaned_photos = []
    if photos_dir.exists():
        for photo_file in photos_dir.glob("*.jpg"):
            if photo_file not in photo_paths and photo_file not in key_frame_paths:
                orphaned_photos.append(photo_file)
        # Also check PNG files
        for photo_file in photos_dir.glob("*.png"):
            if photo_file not in photo_paths:
                orphaned_photos.append(photo_file)
    
    print(f"   Orphaned videos: {len(orphaned_videos)}")
    print(f"   Orphaned key frames: {len(orphaned_key_frames)}")
    print(f"   Orphaned photos: {len(orphaned_photos)}")
    
    # Step 5: Delete orphaned files
    print(f"\n4️⃣  Deleting orphaned files...")
    deleted_videos = 0
    deleted_key_frames = 0
    deleted_photos = 0
    
    for video_file in orphaned_videos:
        try:
            video_file.unlink()
            deleted_videos += 1
        except Exception as e:
            print(f"   ⚠️  Failed to delete {video_file.name}: {e}")
    
    for frame_file in orphaned_key_frames:
        try:
            frame_file.unlink()
            deleted_key_frames += 1
        except Exception as e:
            print(f"   ⚠️  Failed to delete {frame_file.name}: {e}")
    
    for photo_file in orphaned_photos:
        try:
            photo_file.unlink()
            deleted_photos += 1
        except Exception as e:
            print(f"   ⚠️  Failed to delete {photo_file.name}: {e}")
    
    print(f"   ✅ Deleted {deleted_videos} videos")
    print(f"   ✅ Deleted {deleted_key_frames} key frames")
    print(f"   ✅ Deleted {deleted_photos} photos")
    
    # Step 6: Save cleaned CSV
    print(f"\n5️⃣  Saving cleaned CSV...")
    df.to_csv(csv_path, index=False, na_rep='')
    print(f"   ✅ Saved to: {csv_path}")
    
    return {
        "dataset": dataset_name,
        "original_rows": original_rows,
        "removed_file_missing": removed_file_missing,
        "final_rows": after_remove,
        "orphaned_videos": len(orphaned_videos),
        "orphaned_key_frames": len(orphaned_key_frames),
        "orphaned_photos": len(orphaned_photos),
        "deleted_videos": deleted_videos,
        "deleted_key_frames": deleted_key_frames,
        "deleted_photos": deleted_photos
    }


def verify_media_correspondence(dataset_name, csv_path, project_root):
    """
    Verify that all media files in CSV exist and all media files on disk are referenced.
    """
    df = pd.read_csv(csv_path)
    
    # Collect all media paths from CSV
    video_paths, key_frame_paths, photo_paths = get_all_media_paths_from_csv(df, project_root)
    
    # Find media directories
    csv_parent = Path(csv_path).parent.parent
    media_cleaned_dir = csv_parent / "media_cleaned"
    
    missing_files = []
    orphaned_files = []
    
    if media_cleaned_dir.exists():
        videos_dir = media_cleaned_dir / "videos"
        photos_dir = media_cleaned_dir / "photos"
        
        # Check for missing files
        all_referenced = video_paths | key_frame_paths | photo_paths
        for file_path in all_referenced:
            if not file_path.exists():
                missing_files.append(file_path)
        
        # Check for orphaned files
        if videos_dir.exists():
            for video_file in videos_dir.glob("*.mp4"):
                if video_file not in video_paths:
                    orphaned_files.append(video_file)
        
        if photos_dir.exists():
            for photo_file in photos_dir.glob("*"):
                if photo_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    if photo_file not in key_frame_paths and photo_file not in photo_paths:
                        orphaned_files.append(photo_file)
    
    return {
        "missing_files": len(missing_files),
        "orphaned_files": len(orphaned_files),
        "all_match": len(missing_files) == 0 and len(orphaned_files) == 0
    }


def main():
    """Main function"""
    project_root = Path(__file__).parent.parent
    
    datasets = {
        "Assam Flood": "twitter/assam_flood/csvs/filtered_assam_flood_tweets_20240501_20240801_with_local_paths_20250721_172531.csv",
        "Bangladesh Flood": "twitter/bangladesh_flood/csvs/filtered_tweets_aug_to_oct_2024_with_local_paths_20250604_133037.csv",
        "Kerala Flood": "twitter/kerala_flood/csvs/filtered_kerala_flood_tweets_20240715_20240901_with_local_paths_20250721_181731.csv",
        "Pakistan Flood": "twitter/pakistan_flood/csvs/filtered_pakistan_flood_tweets_20220601_20221101_with_local_paths_20250721_175020.csv",
    }
    
    print("="*70)
    print("🧹 Twitter Flood Datasets Cleaning")
    print("="*70)
    print("\nTasks:")
    print("  1. Remove rows with FILE_MISSING in video_key_frames")
    print("  2. Remove orphaned media files (not referenced in CSV)")
    print("  3. Verify media correspondence")
    print("="*70)
    
    results = []
    
    # Clean each dataset
    for dataset_name, csv_path in datasets.items():
        full_csv_path = project_root / csv_path
        
        if not full_csv_path.exists():
            print(f"\n⚠️  Skipping {dataset_name}: CSV not found at {csv_path}")
            continue
        
        result = clean_dataset(dataset_name, str(full_csv_path), project_root)
        results.append(result)
    
    # Verify all datasets
    print(f"\n\n{'='*70}")
    print("🔍 Verification")
    print(f"{'='*70}")
    
    verification_results = []
    for dataset_name, csv_path in datasets.items():
        full_csv_path = project_root / csv_path
        if full_csv_path.exists():
            print(f"\n📊 Verifying {dataset_name}...")
            verify_result = verify_media_correspondence(dataset_name, str(full_csv_path), project_root)
            verify_result["dataset"] = dataset_name
            verification_results.append(verify_result)
            
            if verify_result["all_match"]:
                print(f"   ✅ All media files match!")
            else:
                print(f"   ⚠️  Missing files: {verify_result['missing_files']}")
                print(f"   ⚠️  Orphaned files: {verify_result['orphaned_files']}")
    
    # Final summary
    print(f"\n\n{'='*70}")
    print("📊 Final Summary")
    print(f"{'='*70}")
    
    print(f"\n{'Dataset':<20} {'Original':<10} {'Removed':<10} {'Final':<10} {'Deleted Media':<20}")
    print("-" * 70)
    
    for result in results:
        deleted_media = result.get("deleted_videos", 0) + result.get("deleted_key_frames", 0) + result.get("deleted_photos", 0)
        print(f"{result['dataset']:<20} {result['original_rows']:<10} {result['removed_file_missing']:<10} {result['final_rows']:<10} {deleted_media:<20}")
    
    print(f"\n{'='*70}")
    print("📈 Media Correspondence")
    print(f"{'='*70}")
    
    for verify_result in verification_results:
        status = "✅ Perfect" if verify_result["all_match"] else "⚠️  Issues"
        print(f"{verify_result['dataset']:<20} {status}")
        if not verify_result["all_match"]:
            print(f"   Missing: {verify_result['missing_files']}, Orphaned: {verify_result['orphaned_files']}")
    
    print(f"\n{'='*70}")
    print("✅ Cleaning completed!")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()

