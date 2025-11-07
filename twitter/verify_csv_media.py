#!/usr/bin/env python3
"""
Verify CSV and media file correspondence for Twitter video key frames extraction.
"""

import os
import json
import pandas as pd
from pathlib import Path


def verify_csv_and_media(csv_path):
    """
    Verify CSV file and media file correspondence.
    
    Args:
        csv_path: Path to CSV file
    """
    print("🔍 Starting verification process")
    print("=" * 60)
    
    # Read CSV
    print(f"\n📖 Reading CSV file: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(df)} rows")
    except Exception as e:
        print(f"❌ Failed to read CSV: {e}")
        return False
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Check required columns
    required_columns = ["video_key_frames", "all_images"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"⚠️  Missing columns: {missing_columns}")
        return False
    
    print(f"\n✅ All required columns present: {required_columns}")
    
    # Statistics
    stats = {
        "total_rows": len(df),
        "rows_with_video_key_frames": 0,
        "rows_with_all_images": 0,
        "rows_with_photos_only": 0,
        "rows_with_video_frames_only": 0,
        "rows_with_both": 0,
        "missing_files": [],
        "invalid_json": [],
        "path_mismatches": []
    }
    
    # Verify each row
    print("\n🔍 Verifying rows...")
    for idx, row in df.iterrows():
        row_num = idx + 1
        
        # Check video_key_frames
        has_video_frames = False
        video_frame_paths = []
        if pd.notna(row.get("video_key_frames")) and str(row["video_key_frames"]).strip():
            try:
                video_frame_paths = json.loads(row["video_key_frames"])
                if video_frame_paths:
                    has_video_frames = True
                    stats["rows_with_video_key_frames"] += 1
            except json.JSONDecodeError as e:
                stats["invalid_json"].append({
                    "row": row_num,
                    "column": "video_key_frames",
                    "error": str(e)
                })
        
        # Check all_images
        has_all_images = False
        all_image_paths = []
        if pd.notna(row.get("all_images")) and str(row["all_images"]).strip():
            try:
                all_image_paths = json.loads(row["all_images"])
                if all_image_paths:
                    has_all_images = True
                    stats["rows_with_all_images"] += 1
            except json.JSONDecodeError as e:
                stats["invalid_json"].append({
                    "row": row_num,
                    "column": "all_images",
                    "error": str(e)
                })
        
        # Check photo paths
        photo_paths = []
        for i in range(1, 10):
            photo_col = f"photo{i}_local_path"
            if photo_col in row and pd.notna(row[photo_col]) and str(row[photo_col]).strip():
                photo_path = str(row[photo_col]).strip()
                # Convert to cleaned path if needed
                if "/media/photos/" in photo_path:
                    photo_path = photo_path.replace("/media/photos/", "/media_cleaned/photos/")
                elif "media\\photos\\" in photo_path:
                    photo_path = photo_path.replace("media\\photos\\", "media_cleaned\\photos\\")
                photo_paths.append(photo_path)
        
        # Classify row type
        if photo_paths and has_video_frames:
            stats["rows_with_both"] += 1
        elif photo_paths and not has_video_frames:
            stats["rows_with_photos_only"] += 1
        elif not photo_paths and has_video_frames:
            stats["rows_with_video_frames_only"] += 1
        
        # Verify file existence for video_key_frames
        for frame_path in video_frame_paths:
            if not os.path.isabs(frame_path):
                abs_path = project_root / frame_path
            else:
                abs_path = Path(frame_path)
            
            if not abs_path.exists():
                stats["missing_files"].append({
                    "row": row_num,
                    "path": frame_path,
                    "type": "video_key_frame"
                })
        
        # Verify file existence for all_images
        for img_path in all_image_paths:
            if not os.path.isabs(img_path):
                abs_path = project_root / img_path
            else:
                abs_path = Path(img_path)
            
            if not abs_path.exists():
                stats["missing_files"].append({
                    "row": row_num,
                    "path": img_path,
                    "type": "all_images"
                })
        
        # Verify consistency: all_images should contain video_key_frames if both exist
        if has_video_frames and has_all_images:
            missing_in_all_images = set(video_frame_paths) - set(all_image_paths)
            if missing_in_all_images:
                stats["path_mismatches"].append({
                    "row": row_num,
                    "missing": list(missing_in_all_images),
                    "issue": "video_key_frames not in all_images"
                })
        
        # Progress indicator
        if row_num % 50 == 0:
            print(f"   Verified {row_num}/{stats['total_rows']} rows...")
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 Verification Results")
    print("=" * 60)
    print(f"\n📈 Statistics:")
    print(f"   Total rows: {stats['total_rows']}")
    print(f"   Rows with video_key_frames: {stats['rows_with_video_key_frames']}")
    print(f"   Rows with all_images: {stats['rows_with_all_images']}")
    print(f"   Rows with photos only: {stats['rows_with_photos_only']}")
    print(f"   Rows with video frames only: {stats['rows_with_video_frames_only']}")
    print(f"   Rows with both photos and video frames: {stats['rows_with_both']}")
    
    # Report issues
    if stats["invalid_json"]:
        print(f"\n⚠️  Invalid JSON entries: {len(stats['invalid_json'])}")
        for issue in stats["invalid_json"][:5]:  # Show first 5
            print(f"   Row {issue['row']}, Column {issue['column']}: {issue['error']}")
        if len(stats["invalid_json"]) > 5:
            print(f"   ... and {len(stats['invalid_json']) - 5} more")
    
    if stats["missing_files"]:
        print(f"\n❌ Missing files: {len(stats['missing_files'])}")
        for issue in stats["missing_files"][:10]:  # Show first 10
            print(f"   Row {issue['row']}: {issue['path']} ({issue['type']})")
        if len(stats["missing_files"]) > 10:
            print(f"   ... and {len(stats['missing_files']) - 10} more")
    else:
        print(f"\n✅ All files exist!")
    
    if stats["path_mismatches"]:
        print(f"\n⚠️  Path mismatches: {len(stats['path_mismatches'])}")
        for issue in stats["path_mismatches"][:5]:
            print(f"   Row {issue['row']}: {issue['issue']}")
            print(f"      Missing: {issue['missing']}")
        if len(stats["path_mismatches"]) > 5:
            print(f"   ... and {len(stats['path_mismatches']) - 5} more")
    else:
        print(f"\n✅ All paths are consistent!")
    
    # Test loading
    print("\n" + "=" * 60)
    print("🧪 Testing data loading")
    print("=" * 60)
    
    success_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Test loading video_key_frames
            if pd.notna(row.get("video_key_frames")) and str(row["video_key_frames"]).strip():
                video_frames = json.loads(row["video_key_frames"])
                assert isinstance(video_frames, list)
            
            # Test loading all_images
            if pd.notna(row.get("all_images")) and str(row["all_images"]).strip():
                all_images = json.loads(row["all_images"])
                assert isinstance(all_images, list)
            
            success_count += 1
        except Exception as e:
            error_count += 1
            if error_count <= 5:
                print(f"   ❌ Row {idx+1}: {str(e)[:100]}")
    
    print(f"\n✅ Successfully loaded: {success_count}/{stats['total_rows']} rows")
    if error_count > 0:
        print(f"❌ Failed to load: {error_count} rows")
    
    # Final verdict
    print("\n" + "=" * 60)
    if stats["missing_files"] or stats["invalid_json"] or stats["path_mismatches"] or error_count > 0:
        print("⚠️  Verification completed with issues")
        return False
    else:
        print("✅ Verification passed! All data is valid and consistent.")
        return True


def main():
    """Main function"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python verify_csv_media.py <csv_path>")
        print("\nExample:")
        print("  python verify_csv_media.py twitter/assam_flood/csvs/filtered_assam_flood_tweets_20240501_20240801_with_local_paths_20250721_172531.csv")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        sys.exit(1)
    
    success = verify_csv_and_media(csv_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

