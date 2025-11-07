#!/usr/bin/env python3
"""
Batch process Twitter flood datasets to extract video key frames.
"""

import subprocess
import sys
from pathlib import Path

# Define datasets to process
DATASETS = {
    "bangladesh_flood": {
        "csv_path": "twitter/bangladesh_flood/csvs/filtered_tweets_aug_to_oct_2024_with_local_paths_20250604_133037.csv",
        "name": "Bangladesh Flood"
    },
    "kerala_flood": {
        "csv_path": "twitter/kerala_flood/csvs/filtered_kerala_flood_tweets_20240715_20240901_with_local_paths_20250721_181731.csv",
        "name": "Kerala Flood"
    },
    "pakistan_flood": {
        "csv_path": "twitter/pakistan_flood/csvs/filtered_pakistan_flood_tweets_20220601_20221101_with_local_paths_20250721_175020.csv",
        "name": "Pakistan Flood"
    }
}

def main():
    """Process all datasets"""
    print("🎬 Starting batch video key frame extraction")
    print("=" * 60)
    print(f"📋 Processing {len(DATASETS)} datasets")
    print("=" * 60)
    print()
    
    project_root = Path(__file__).parent.parent
    results = []
    
    for dataset_key, dataset_info in DATASETS.items():
        csv_path = dataset_info["csv_path"]
        name = dataset_info["name"]
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
        print(f"{'='*60}\n")
        
        try:
            # Run extract_video_key_frames.py
            cmd = [
                sys.executable,
                "twitter/extract_video_key_frames.py",
                str(full_csv_path)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                print(f"\n✅ Completed extraction for: {name}\n")
                results.append({
                    "dataset": name,
                    "status": "completed"
                })
            else:
                print(f"\n❌ Failed extraction for: {name}\n")
                results.append({
                    "dataset": name,
                    "status": "error",
                    "error": f"Exit code: {result.returncode}"
                })
        except Exception as e:
            print(f"\n❌ Error processing {name}: {e}\n")
            results.append({
                "dataset": name,
                "status": "error",
                "error": str(e)
            })
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Extraction Summary")
    print("=" * 60)
    for result in results:
        status_icon = "✅" if result["status"] == "completed" else "❌" if result["status"] == "error" else "⚠️"
        print(f"{status_icon} {result['dataset']}: {result['status']}")
        if "error" in result:
            print(f"   Error: {result['error']}")
    
    print("\n" + "=" * 60)
    print("🔍 Starting verification...")
    print("=" * 60)
    print()
    
    # Verify results
    verification_results = []
    for dataset_key, dataset_info in DATASETS.items():
        csv_path = dataset_info["csv_path"]
        name = dataset_info["name"]
        full_csv_path = project_root / csv_path
        
        if not full_csv_path.exists():
            continue
        
        print(f"\n{'='*60}")
        print(f"🔍 Verifying: {name}")
        print(f"{'='*60}\n")
        
        try:
            cmd = [
                sys.executable,
                "twitter/verify_csv_media.py",
                str(full_csv_path)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                capture_output=False,
                text=True
            )
            
            verification_results.append({
                "dataset": name,
                "verified": result.returncode == 0
            })
        except Exception as e:
            print(f"❌ Verification error for {name}: {e}")
            verification_results.append({
                "dataset": name,
                "verified": False
            })
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 Final Summary")
    print("=" * 60)
    print("\nExtraction Results:")
    for result in results:
        status_icon = "✅" if result["status"] == "completed" else "❌" if result["status"] == "error" else "⚠️"
        print(f"  {status_icon} {result['dataset']}: {result['status']}")
    
    print("\nVerification Results:")
    for result in verification_results:
        status_icon = "✅" if result["verified"] else "❌"
        print(f"  {status_icon} {result['dataset']}: {'Verified' if result['verified'] else 'Failed'}")
    
    print("\n🎉 Batch processing completed!")


if __name__ == "__main__":
    main()

