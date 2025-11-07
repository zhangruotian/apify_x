#!/usr/bin/env python3
"""
Extract key frames from Twitter videos.
Extracts up to 5 key frames per video, ensuring they span the entire video duration.
Uses visual difference detection to select the most representative frames.
Saves frames to photos directory and records paths in CSV.
"""

import os
import sys
import subprocess
import cv2
import numpy as np
from pathlib import Path
import pandas as pd
import json


def get_video_duration(video_path):
    """
    Get video duration in seconds using ffprobe.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Duration in seconds, or None if failed
    """
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        if result.returncode == 0:
            duration = float(result.stdout.decode().strip())
            return duration
    except Exception as e:
        print(f"⚠️  Failed to get video duration: {e}")
    return None


def calculate_frame_difference(frame1, frame2):
    """
    Calculate visual difference between two frames.
    
    Args:
        frame1: First frame (numpy array)
        frame2: Second frame (numpy array)
        
    Returns:
        Difference score (higher = more different)
    """
    if frame1 is None or frame2 is None:
        return 0
    
    # Convert to grayscale if needed
    if len(frame1.shape) == 3:
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    else:
        gray1 = frame1
    
    if len(frame2.shape) == 3:
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    else:
        gray2 = frame2
    
    # Resize to same size if needed
    if gray1.shape != gray2.shape:
        h, w = min(gray1.shape[0], gray2.shape[0]), min(gray1.shape[1], gray2.shape[1])
        gray1 = cv2.resize(gray1, (w, h))
        gray2 = cv2.resize(gray2, (w, h))
    
    # Calculate absolute difference
    diff = cv2.absdiff(gray1, gray2)
    
    # Return mean difference
    return np.mean(diff)


def extract_key_frames(video_path, num_frames=5, output_dir=None):
    """
    Extract key frames from video.
    
    Strategy:
    1. Divide video into equal time segments
    2. Extract frames at regular intervals within each segment
    3. Calculate visual differences between consecutive frames
    4. Select the frame with maximum visual change in each segment
    
    Args:
        video_path: Path to video file
        num_frames: Maximum number of key frames to extract
        output_dir: Directory to save frames (should be photos directory)
        
    Returns:
        List of frame file paths (relative to project root), or empty list if failed
    """
    if not os.path.exists(video_path):
        print(f"⚠️  Video file not found: {video_path}")
        return []
    
    # Get video duration
    duration = get_video_duration(video_path)
    if duration is None:
        print(f"⚠️  Failed to get video duration for {video_path}")
        return []
    
    if duration < 1.0:  # Very short video
        num_frames = min(1, num_frames)
    
    # Create output directory if not provided
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(video_path), "..", "photos")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate base filename from video filename
    # Keep the full video name to avoid conflicts when a tweet has multiple videos
    video_name = Path(video_path).stem  # e.g., "1812879386582102328_navin_ankampali_video1"
    base_name = video_name  # Use full name to distinguish between video1, video2, etc.
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"⚠️  Failed to open video: {video_path}")
        return []
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if total_frames == 0:
        print(f"⚠️  Video has no frames: {video_path}")
        cap.release()
        return []
    
    # Calculate time segments
    segment_duration = duration / num_frames
    key_frame_times = []
    
    # Generate candidate times evenly distributed
    for i in range(num_frames):
        # Target time: middle of each segment
        target_time = (i + 0.5) * segment_duration
        # Ensure we don't exceed video duration
        target_time = min(target_time, duration - 0.1)
        key_frame_times.append(target_time)
    
    # Extract frames and calculate differences
    key_frames = []
    prev_frame = None
    
    # Read frames at candidate times and select best ones
    selected_frames = []
    
    for target_time in key_frame_times:
        # Seek to target time
        cap.set(cv2.CAP_PROP_POS_MSEC, target_time * 1000)
        
        # Extract a small window around target time to find best frame
        window_size = min(2.0, segment_duration * 0.5)  # 2 seconds or half segment
        start_time = max(0, target_time - window_size / 2)
        end_time = min(duration, target_time + window_size / 2)
        
        best_frame = None
        best_frame_time = target_time
        max_diff = 0
        
        # Sample frames in the window
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)
        sample_interval = 0.5  # Sample every 0.5 seconds
        
        current_time = start_time
        while current_time <= end_time:
            cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
            ret, frame = cap.read()
            
            if ret and frame is not None:
                # Calculate difference from previous frame
                if prev_frame is not None:
                    diff = calculate_frame_difference(prev_frame, frame)
                    if diff > max_diff:
                        max_diff = diff
                        best_frame = frame.copy()
                        best_frame_time = current_time
                else:
                    # First frame
                    best_frame = frame.copy()
                    best_frame_time = current_time
                    max_diff = 1000  # High value for first frame
            
            current_time += sample_interval
        
        # If no good frame found, use the target time frame
        if best_frame is None:
            cap.set(cv2.CAP_PROP_POS_MSEC, target_time * 1000)
            ret, frame = cap.read()
            if ret and frame is not None:
                best_frame = frame
                best_frame_time = target_time
        
        if best_frame is not None:
            selected_frames.append((best_frame_time, best_frame))
            prev_frame = best_frame
    
    cap.release()
    
    # Save selected frames
    frame_paths = []
    project_root = Path(__file__).parent.parent
    
    for idx, (frame_time, frame) in enumerate(selected_frames):
        # Generate filename: {base_name}_keyframe{idx+1}.jpg
        frame_filename = f"{base_name}_keyframe{idx+1:02d}.jpg"
        frame_path = output_dir / frame_filename
        
        # Save frame
        cv2.imwrite(str(frame_path), frame)
        if frame_path.exists():
            # Use relative path from project root
            rel_path = os.path.relpath(frame_path, project_root)
            frame_paths.append(rel_path)
    
    return frame_paths


def collect_photo_paths_from_row(row, project_root, csv_path=None):
    """
    Collect all original photo paths from a CSV row.
    
    Args:
        row: Pandas Series representing a CSV row
        project_root: Path to project root directory
        csv_path: Path to CSV file (for auto-detecting dataset name)
        
    Returns:
        List of photo paths (relative to project root)
    """
    photo_paths = []
    
    # Auto-detect dataset name if csv_path provided
    dataset_name = None
    if csv_path:
        csv_parent = Path(csv_path).parent.parent
        dataset_name = csv_parent.name
    
    # Get original photo paths (from photo1_local_path to photo9_local_path)
    for i in range(1, 10):
        photo_col = f"photo{i}_local_path"
        if photo_col in row and pd.notna(row[photo_col]) and str(row[photo_col]).strip():
            photo_path = str(row[photo_col]).strip()
            # Convert to cleaned media path if needed
            if "/media/photos/" in photo_path:
                photo_path = photo_path.replace("/media/photos/", "/media_cleaned/photos/")
            elif "media\\photos\\" in photo_path:
                photo_path = photo_path.replace("media\\photos\\", "media_cleaned\\photos\\")
            elif photo_path.startswith("media/photos/") and dataset_name:
                # Path without dataset prefix, need to add it
                photo_path = f"twitter/{dataset_name}/media_cleaned/photos/{os.path.basename(photo_path)}"
            
            # Convert to absolute path to check existence, then back to relative
            if not os.path.isabs(photo_path):
                abs_photo_path = project_root / photo_path
                if abs_photo_path.exists():
                    photo_paths.append(photo_path)
    
    return photo_paths


def process_csv(csv_path, output_csv_path=None, photos_dir=None):
    """
    Process CSV file and extract key frames for all videos.
    
    Args:
        csv_path: Path to input CSV file
        output_csv_path: Path to output CSV file (if None, overwrites input)
        photos_dir: Directory to save frames (if None, auto-detects from CSV path)
    """
    print("🎬 Starting key frame extraction process for Twitter videos")
    print("=" * 60)
    
    # Read CSV
    print(f"\n📖 Reading CSV file: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(df)} rows")
    except Exception as e:
        print(f"❌ Failed to read CSV: {e}")
        return
    
    # Check if video_key_frames column already exists
    key_frames_column = "video_key_frames"
    if key_frames_column in df.columns:
        print(f"⚠️  Column '{key_frames_column}' already exists. Will update empty values.")
    else:
        df[key_frames_column] = ""
    
    # Check if all_images column already exists (unified column for all images)
    all_images_column = "all_images"
    if all_images_column in df.columns:
        print(f"⚠️  Column '{all_images_column}' already exists. Will update values.")
    else:
        df[all_images_column] = ""
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    
    # Determine photos directory
    if photos_dir is None:
        # Auto-detect from CSV path (e.g., twitter/assam_flood/csvs/... -> twitter/assam_flood/media_cleaned/photos)
        csv_parent = Path(csv_path).parent.parent
        photos_dir = csv_parent / "media_cleaned" / "photos"
    else:
        photos_dir = Path(photos_dir)
    
    photos_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Key frames will be saved to: {photos_dir}")
    
    # Process each row
    total_rows = len(df)
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        row_num = idx + 1
        
        # Skip if already has key frames (but still update all_images column if needed)
        has_existing_key_frames = pd.notna(row.get(key_frames_column)) and str(row[key_frames_column]).strip()
        
        # Get all video paths for this tweet
        video_paths = []
        for i in range(1, 6):  # video1 to video5
            video_col = f"video{i}_local_path"
            if video_col in row and pd.notna(row[video_col]) and str(row[video_col]).strip():
                video_path = str(row[video_col]).strip()
                
                # Convert to cleaned media path if needed
                # Original path: twitter/assam_flood/media/videos/xxx.mp4
                # Cleaned path: twitter/assam_flood/media_cleaned/videos/xxx.mp4
                if "/media/videos/" in video_path:
                    video_path = video_path.replace("/media/videos/", "/media_cleaned/videos/")
                elif "media\\videos\\" in video_path:
                    video_path = video_path.replace("media\\videos\\", "media_cleaned\\videos\\")
                
                # Convert to absolute path if relative
                if not os.path.isabs(video_path):
                    video_path = project_root / video_path
                    video_path = str(video_path)
                
                # Check if file exists
                if os.path.exists(video_path):
                    video_paths.append(video_path)
                else:
                    print(f"   ⚠️  Video file not found: {video_path}")
        
        if has_existing_key_frames:
            # Still update all_images column if it's empty or needs updating
            if not pd.notna(row.get(all_images_column)) or not str(row[all_images_column]).strip():
                # Collect all image paths
                all_image_paths = collect_photo_paths_from_row(row, project_root, csv_path)
                
                # Get existing video key frames
                try:
                    existing_frames = json.loads(row[key_frames_column])
                    if existing_frames:
                        all_image_paths.extend(existing_frames)
                except:
                    pass
                
                if all_image_paths:
                    all_images_json = json.dumps(all_image_paths)
                    df.at[idx, all_images_column] = all_images_json
            
            skipped_count += 1
            if skipped_count % 10 == 0:
                print(f"⏭️  Skipped {skipped_count} rows with existing key frames...")
            continue
        
        # Get all video paths for this tweet
        video_paths = []
        # Auto-detect dataset name from CSV path
        csv_parent = Path(csv_path).parent.parent
        dataset_name = csv_parent.name
        
        for i in range(1, 6):  # video1 to video5
            video_col = f"video{i}_local_path"
            if video_col in row and pd.notna(row[video_col]) and str(row[video_col]).strip():
                video_path = str(row[video_col]).strip()
                
                # Convert to cleaned media path if needed
                # Handle multiple formats:
                # 1. twitter/assam_flood/media/videos/xxx.mp4 -> twitter/assam_flood/media_cleaned/videos/xxx.mp4
                # 2. media/videos/xxx.mp4 -> twitter/{dataset}/media_cleaned/videos/xxx.mp4
                if "/media/videos/" in video_path:
                    video_path = video_path.replace("/media/videos/", "/media_cleaned/videos/")
                elif "media\\videos\\" in video_path:
                    video_path = video_path.replace("media\\videos\\", "media_cleaned\\videos\\")
                elif video_path.startswith("media/videos/"):
                    # Path without dataset prefix, need to add it
                    video_path = f"twitter/{dataset_name}/media_cleaned/videos/{os.path.basename(video_path)}"
                
                # Convert to absolute path if relative
                if not os.path.isabs(video_path):
                    video_path = project_root / video_path
                    video_path = str(video_path)
                
                # Check if file exists
                if os.path.exists(video_path):
                    video_paths.append(video_path)
                else:
                    print(f"   ⚠️  Video file not found: {video_path}")
        
        # Check if there were video paths in CSV but files don't exist
        csv_has_videos = any(
            pd.notna(row.get(f"video{i}_local_path")) and str(row.get(f"video{i}_local_path", "")).strip()
            for i in range(1, 6)
        )
        
        if not video_paths:
            # No videos found (either no paths in CSV or files don't exist)
            all_image_paths = collect_photo_paths_from_row(row, project_root, csv_path)
            
            # If CSV says there are videos but files don't exist, mark it
            if csv_has_videos:
                # Video files are missing - use special marker to distinguish from truly empty
                df.at[idx, key_frames_column] = "FILE_MISSING"  # Special marker for missing files
                print(f"   ⚠️  Video files missing (CSV has video paths but files don't exist)")
            
            # Save all images (only photos, no video frames)
            if all_image_paths:
                all_images_json = json.dumps(all_image_paths)
                df.at[idx, all_images_column] = all_images_json
                print(f"   📸 No videos, but found {len(all_image_paths)} photo(s)")
            elif not csv_has_videos:
                # No videos and no photos - mark all_images as empty
                df.at[idx, all_images_column] = ""
            
            skipped_count += 1
            continue
        
        # Extract key frames from all videos
        all_frame_paths = []
        tweet_id = row.get("tweet_id", f"row_{row_num}")
        
        print(f"\n📹 [{row_num}/{total_rows}] Processing tweet {tweet_id} ({len(video_paths)} video(s))")
        
        for video_idx, video_path in enumerate(video_paths):
            video_name = os.path.basename(video_path)
            print(f"   🎥 Video {video_idx+1}/{len(video_paths)}: {video_name}")
            
            try:
                frame_paths = extract_key_frames(
                    video_path, 
                    num_frames=5, 
                    output_dir=str(photos_dir.resolve())
                )
                
                if frame_paths:
                    all_frame_paths.extend(frame_paths)
                    print(f"   ✅ Extracted {len(frame_paths)} key frames")
                else:
                    print(f"   ⚠️  Failed to extract key frames")
            except Exception as e:
                print(f"   ❌ Error extracting frames: {str(e)[:100]}")
        
        # Collect all image paths for this tweet (original photos + video key frames)
        all_image_paths = collect_photo_paths_from_row(row, project_root, csv_path)
        
        # Add video key frames
        if all_frame_paths:
            all_image_paths.extend(all_frame_paths)
        
        # Save frame paths to CSV
        if all_frame_paths:
            # Save as JSON string in CSV
            frame_paths_json = json.dumps(all_frame_paths)
            df.at[idx, key_frames_column] = frame_paths_json
            processed_count += 1
            print(f"   ✅ Total: {len(all_frame_paths)} key frames extracted")
        else:
            error_count += 1
            df.at[idx, key_frames_column] = ""
            print(f"   ❌ No key frames extracted")
        
        # Save all images (original photos + video key frames) to unified column
        if all_image_paths:
            all_images_json = json.dumps(all_image_paths)
            df.at[idx, all_images_column] = all_images_json
            print(f"   📸 Total images (photos + key frames): {len(all_image_paths)}")
        else:
            df.at[idx, all_images_column] = ""
        
        # Save progress periodically (every 10 rows)
        if row_num % 10 == 0:
            output_path = output_csv_path or csv_path
            df.to_csv(output_path, index=False, na_rep='')
            print(f"\n💾 Progress saved: {row_num}/{total_rows} rows processed")
            print(f"   ✅ Processed: {processed_count} | ⏭️  Skipped: {skipped_count} | ❌ Errors: {error_count}")
    
    # Save final results
    output_path = output_csv_path or csv_path
    print(f"\n💾 Saving results to: {output_path}")
    # Use na_rep='' to preserve empty strings, but FILE_MISSING will be preserved as-is
    df.to_csv(output_path, index=False, na_rep='')
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"   Total rows: {total_rows}")
    print(f"   ✅ Processed (with videos): {processed_count}")
    print(f"   ⏭️  Skipped (no videos or already had key frames): {skipped_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   Output saved to: {output_path}")
    print("=" * 60)


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python extract_video_key_frames.py <csv_path> [output_csv_path] [photos_dir]")
        print("\nExample:")
        print("  python extract_video_key_frames.py twitter/assam_flood/csvs/filtered_assam_flood_tweets_20240501_20240801_with_local_paths_20250721_172531.csv")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    output_csv_path = sys.argv[2] if len(sys.argv) > 2 else None
    photos_dir = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        sys.exit(1)
    
    # Check if opencv-python is available
    try:
        import cv2
    except ImportError:
        print("❌ opencv-python is required. Install it with:")
        print("   pip install opencv-python")
        sys.exit(1)
    
    process_csv(csv_path, output_csv_path, photos_dir)
    print("\n🎉 Process completed!")


if __name__ == "__main__":
    main()

