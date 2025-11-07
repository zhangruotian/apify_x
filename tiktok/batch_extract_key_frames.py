#!/usr/bin/env python3
"""
Batch extract key frames from multiple TikTok flood datasets.
Processes all specified datasets.
"""

import sys
from pathlib import Path

# Import functions from extract_key_frames module
import importlib.util
spec = importlib.util.spec_from_file_location("extract_key_frames", 
                                               Path(__file__).parent / "extract_key_frames.py")
extract_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extract_module)

# Define all datasets to process
DATASETS = {
    "bangladesh_flood": {
        "csv_path": "tiktok/bangladesh_flood/csvs/tiktok_posts_20240801_to_20241031_with_local_paths.csv",
        "name": "Bangladesh Flood",
        "frames_dir": "tiktok/bangladesh_flood/frames"
    },
    "kerala_flood": {
        "csv_path": "tiktok/kerala_flood/csvs/filtered_kerala_flood_posts_20240715_20241101_with_local_paths.csv",
        "name": "Kerala Flood",
        "frames_dir": "tiktok/kerala_flood/frames"
    },
    "pakistan_flood": {
        "csv_path": "tiktok/pakistan_flood/csvs/filtered_pakistan_flood_posts_20220601_20230101_with_local_paths.csv",
        "name": "Pakistan Flood",
        "frames_dir": "tiktok/pakistan_flood/frames"
    },
    "south_asia_flood": {
        "csv_path": "tiktok/south_asia_flood/csvs/filtered_south_asia_flood_posts_with_local_paths.csv",
        "name": "South Asia Flood",
        "frames_dir": "tiktok/south_asia_flood/frames"
    },
}


def main():
    """Process all datasets"""
    print("🎬 Starting batch key frame extraction process")
    print("=" * 60)
    print(f"📋 Processing {len(DATASETS)} datasets")
    print("\n📝 Features:")
    print("   ✅ Extract up to 5 key frames per video")
    print("   ✅ Frames evenly distributed across video duration")
    print("   ✅ Visual difference detection for best frames")
    print("   ✅ Auto-skip videos that already have key frames")
    print("=" * 60)
    print()
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    
    # Process each dataset
    results = []
    for dataset_key, dataset_info in DATASETS.items():
        csv_path = dataset_info["csv_path"]
        name = dataset_info["name"]
        frames_dir = dataset_info["frames_dir"]
        
        # Convert to absolute path
        full_csv_path = project_root / csv_path
        
        if not full_csv_path.exists():
            print(f"⚠️  Skipping {name}: CSV file not found at {csv_path}")
            results.append({
                "dataset": name,
                "status": "skipped",
                "reason": "CSV file not found"
            })
            continue
        
        print(f"\n{'='*60}")
        print(f"📂 Processing: {name}")
        print(f"📄 CSV: {csv_path}")
        print(f"📁 Frames will be saved to: {frames_dir}")
        print(f"{'='*60}\n")
        
        try:
            # Process the CSV with custom frames directory
            extract_module.process_csv(str(full_csv_path), frames_base_dir=str(project_root / frames_dir))
            results.append({
                "dataset": name,
                "status": "completed"
            })
            print(f"\n✅ Completed processing: {name}\n")
        except Exception as e:
            print(f"\n❌ Error processing {name}: {e}\n")
            import traceback
            traceback.print_exc()
            results.append({
                "dataset": name,
                "status": "error",
                "error": str(e)
            })
    
    # Print final summary
    print("\n" + "=" * 60)
    print("📊 Final Summary")
    print("=" * 60)
    for result in results:
        status_icon = "✅" if result["status"] == "completed" else "❌" if result["status"] == "error" else "⚠️"
        print(f"{status_icon} {result['dataset']}: {result['status']}")
        if "error" in result:
            print(f"   Error: {result['error']}")
    
    print("\n🎉 Batch processing completed!")


if __name__ == "__main__":
    main()

