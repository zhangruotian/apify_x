#!/usr/bin/env python3
"""
Extract key frames from TikTok videos.
Extracts up to 5 key frames per video, ensuring they span the entire video duration.
Uses visual difference detection to select the most representative frames.
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
        output_dir: Directory to save frames (if None, creates frames/ directory)
        
    Returns:
        List of frame file paths, or empty list if failed
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
    
    # Create output directory
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    if output_dir is None:
        frames_dir = os.path.join(os.path.dirname(video_path), "..", "frames")
    else:
        frames_dir = output_dir
    
    frames_dir = os.path.join(frames_dir, video_name)
    os.makedirs(frames_dir, exist_ok=True)
    
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
    for idx, (frame_time, frame) in enumerate(selected_frames):
        frame_filename = f"frame_{idx+1:02d}_{frame_time:.2f}s.jpg"
        frame_path = os.path.join(frames_dir, frame_filename)
        
        # Save frame
        cv2.imwrite(frame_path, frame)
        if os.path.exists(frame_path):
            # Use relative path from project root
            rel_path = os.path.relpath(frame_path, Path(__file__).parent.parent)
            frame_paths.append(rel_path)
    
    return frame_paths


def process_csv(csv_path, output_csv_path=None, frames_base_dir=None):
    """
    Process CSV file and extract key frames for all videos.
    
    Args:
        csv_path: Path to input CSV file
        output_csv_path: Path to output CSV file (if None, overwrites input)
        frames_base_dir: Base directory for frames (if None, auto-detects from CSV path)
    """
    print("🎬 Starting key frame extraction process")
    print("=" * 60)
    
    # Read CSV
    print(f"\n📖 Reading CSV file: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(df)} rows")
    except Exception as e:
        print(f"❌ Failed to read CSV: {e}")
        return
    
    # Check if key_frames column already exists
    key_frames_column = "key_frames"
    if key_frames_column in df.columns:
        print(f"⚠️  Column '{key_frames_column}' already exists. Will update empty values.")
    else:
        df[key_frames_column] = ""
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    
    # Determine frames directory
    if frames_base_dir is None:
        # Auto-detect from CSV path (e.g., tiktok/assam_flood/csvs/... -> tiktok/assam_flood/frames)
        csv_parent = Path(csv_path).parent.parent
        dataset_name = csv_parent.name
        frames_base_dir = csv_parent / "frames"
    else:
        frames_base_dir = Path(frames_base_dir)
    
    frames_base_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Frames will be saved to: {frames_base_dir}")
    
    # Process each row
    total_rows = len(df)
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        row_num = idx + 1
        
        # Skip if already has key frames
        if pd.notna(row.get(key_frames_column)) and str(row[key_frames_column]).strip():
            skipped_count += 1
            if skipped_count % 10 == 0:
                print(f"⏭️  Skipped {skipped_count} rows with existing key frames...")
            continue
        
        # Get video path
        video_path = row.get("video_local_path", "")
        if not video_path or pd.isna(video_path):
            print(f"⚠️  [{row_num}/{total_rows}] No video_local_path found")
            skipped_count += 1
            continue
        
        # Convert to absolute path if relative
        if not os.path.isabs(video_path):
            video_path = project_root / video_path
            video_path = str(video_path)
        
        # Extract key frames
        print(f"\n📹 [{row_num}/{total_rows}] Processing: {os.path.basename(video_path)}")
        try:
            frame_paths = extract_key_frames(video_path, num_frames=5, output_dir=str(frames_base_dir.resolve()))
            
            if frame_paths:
                # Save as JSON string in CSV
                frame_paths_json = json.dumps(frame_paths)
                df.at[idx, key_frames_column] = frame_paths_json
                processed_count += 1
                print(f"✅ Extracted {len(frame_paths)} key frames")
            else:
                error_count += 1
                df.at[idx, key_frames_column] = ""
                print(f"❌ Failed to extract key frames")
        except Exception as e:
            error_count += 1
            df.at[idx, key_frames_column] = ""
            print(f"❌ Error: {str(e)[:100]}")
        
        # Save progress periodically (every 10 rows)
        if row_num % 10 == 0:
            output_path = output_csv_path or csv_path
            df.to_csv(output_path, index=False)
            print(f"\n💾 Progress saved: {row_num}/{total_rows} rows processed")
            print(f"   ✅ Processed: {processed_count} | ⏭️  Skipped: {skipped_count} | ❌ Errors: {error_count}")
    
    # Save final results
    output_path = output_csv_path or csv_path
    print(f"\n💾 Saving results to: {output_path}")
    df.to_csv(output_path, index=False)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"   Total rows: {total_rows}")
    print(f"   ✅ Processed: {processed_count}")
    print(f"   ⏭️  Skipped (already had key frames): {skipped_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   Output saved to: {output_path}")
    print("=" * 60)


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python extract_key_frames.py <csv_path> [output_csv_path]")
        print("\nExample:")
        print("  python extract_key_frames.py tiktok/assam_flood/csvs/filtered_assam_flood_posts_20240501_20241120_with_local_paths.csv")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    output_csv_path = sys.argv[2] if len(sys.argv) > 2 else None
    
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
    
    process_csv(csv_path, output_csv_path)
    print("\n🎉 Process completed!")


if __name__ == "__main__":
    main()

