#!/usr/bin/env python3
"""
删除 Twitter CSV 中 is_flood_related=False 的记录及其对应的媒体文件
"""

import pandas as pd
import json
import os
from pathlib import Path
from typing import List, Tuple, Set


def get_all_media_paths_from_row(row: pd.Series, project_root: Path) -> Set[Path]:
    """
    从CSV行中提取所有媒体文件路径（照片、视频、关键帧）
    
    Returns:
        Set of absolute paths to media files
    """
    media_paths = set()
    
    # 获取照片路径 (photo1_local_path 到 photo9_local_path)
    for i in range(1, 10):
        photo_col = f"photo{i}_local_path"
        if photo_col in row and pd.notna(row[photo_col]) and str(row[photo_col]).strip():
            photo_path = str(row[photo_col]).strip()
            # 转换为 cleaned 路径
            if "/media/photos/" in photo_path:
                photo_path = photo_path.replace("/media/photos/", "/media_cleaned/photos/")
            elif "media\\photos\\" in photo_path:
                photo_path = photo_path.replace("media\\photos\\", "media_cleaned\\photos\\")
            
            abs_path = project_root / photo_path
            if abs_path.exists():
                media_paths.add(abs_path)
    
    # 获取视频路径 (video1_local_path 到 video5_local_path)
    for i in range(1, 6):
        video_col = f"video{i}_local_path"
        if video_col in row and pd.notna(row[video_col]) and str(row[video_col]).strip():
            video_path = str(row[video_col]).strip()
            # 转换为 cleaned 路径
            if "/media/videos/" in video_path:
                video_path = video_path.replace("/media/videos/", "/media_cleaned/videos/")
            elif "media\\videos\\" in video_path:
                video_path = video_path.replace("media\\videos\\", "media_cleaned\\videos\\")
            
            abs_path = project_root / video_path
            if abs_path.exists():
                media_paths.add(abs_path)
    
    # 获取视频关键帧 (video_key_frames)
    if pd.notna(row.get("video_key_frames")) and isinstance(row["video_key_frames"], str):
        video_frames_val = row["video_key_frames"]
        if video_frames_val.strip() and video_frames_val != "FILE_MISSING":
            try:
                key_frames = json.loads(video_frames_val)
                for frame_path in key_frames:
                    abs_path = project_root / frame_path
                    if abs_path.exists():
                        media_paths.add(abs_path)
            except:
                pass
    
    # 获取 all_images 中的所有图片
    if pd.notna(row.get("all_images")) and isinstance(row["all_images"], str):
        all_images_val = row["all_images"]
        if all_images_val.strip():
            try:
                all_images = json.loads(all_images_val)
                for img_path in all_images:
                    abs_path = project_root / img_path
                    if abs_path.exists():
                        media_paths.add(abs_path)
            except:
                pass
    
    return media_paths


def delete_media_files(media_paths: Set[Path]) -> Tuple[int, int]:
    """
    删除媒体文件
    
    Returns:
        (deleted_count, failed_count)
    """
    deleted_count = 0
    failed_count = 0
    
    for media_path in media_paths:
        try:
            if media_path.exists():
                media_path.unlink()
                deleted_count += 1
        except Exception as e:
            print(f"  ⚠️  Failed to delete {media_path}: {e}")
            failed_count += 1
    
    return deleted_count, failed_count


def process_csv(csv_path: str, project_root: Path) -> dict:
    """
    处理单个CSV文件，删除 is_flood_related=False 的记录及其媒体文件
    
    Returns:
        dict with statistics
    """
    print(f"\n{'='*70}")
    print(f"📄 Processing: {csv_path}")
    print(f"{'='*70}")
    
    # 读取CSV
    df = pd.read_csv(csv_path)
    original_count = len(df)
    print(f"📊 Original records: {original_count}")
    
    # 检查是否有 is_flood_related 列
    if "is_flood_related" not in df.columns:
        print("⚠️  No 'is_flood_related' column found, skipping...")
        return {
            "csv_path": csv_path,
            "original_count": original_count,
            "deleted_count": 0,
            "remaining_count": original_count,
            "media_deleted": 0,
            "media_failed": 0
        }
    
    # 找出 is_flood_related=False 的记录
    false_mask = df["is_flood_related"] == False
    false_count = false_mask.sum()
    print(f"🔍 Records with is_flood_related=False: {false_count}")
    
    if false_count == 0:
        print("✅ No records to delete")
        return {
            "csv_path": csv_path,
            "original_count": original_count,
            "deleted_count": 0,
            "remaining_count": original_count,
            "media_deleted": 0,
            "media_failed": 0
        }
    
    # 收集所有要删除的媒体文件路径
    print(f"\n📦 Collecting media files from {false_count} records...")
    all_media_paths = set()
    false_rows = df[false_mask]
    
    for idx, row in false_rows.iterrows():
        media_paths = get_all_media_paths_from_row(row, project_root)
        all_media_paths.update(media_paths)
    
    print(f"📁 Found {len(all_media_paths)} media files to delete")
    
    # 删除媒体文件
    if all_media_paths:
        print(f"\n🗑️  Deleting {len(all_media_paths)} media files...")
        media_deleted, media_failed = delete_media_files(all_media_paths)
        print(f"   ✅ Deleted: {media_deleted}")
        if media_failed > 0:
            print(f"   ❌ Failed: {media_failed}")
    else:
        media_deleted = 0
        media_failed = 0
    
    # 删除CSV中的False记录
    df_filtered = df[~false_mask].copy()
    remaining_count = len(df_filtered)
    
    # 保存更新后的CSV
    df_filtered.to_csv(csv_path, index=False)
    print(f"\n💾 Saved filtered CSV: {remaining_count} records remaining")
    
    return {
        "csv_path": csv_path,
        "original_count": original_count,
        "deleted_count": false_count,
        "remaining_count": remaining_count,
        "media_deleted": media_deleted,
        "media_failed": media_failed
    }


def verify_media_correspondence(csv_path: str, project_root: Path) -> dict:
    """
    验证剩余记录的媒体文件是否存在
    
    Returns:
        dict with verification statistics
    """
    df = pd.read_csv(csv_path)
    total_records = len(df)
    records_with_media = 0
    records_with_missing_media = 0
    total_expected_media = 0
    total_existing_media = 0
    
    for idx, row in df.iterrows():
        media_paths = get_all_media_paths_from_row(row, project_root)
        total_expected_media += len(media_paths)
        
        if len(media_paths) > 0:
            records_with_media += 1
            existing_count = sum(1 for p in media_paths if p.exists())
            total_existing_media += existing_count
            
            if existing_count < len(media_paths):
                records_with_missing_media += 1
    
    return {
        "total_records": total_records,
        "records_with_media": records_with_media,
        "records_with_missing_media": records_with_missing_media,
        "total_expected_media": total_expected_media,
        "total_existing_media": total_existing_media,
        "media_match_rate": total_existing_media / total_expected_media if total_expected_media > 0 else 1.0
    }


def main():
    """主函数"""
    project_root = Path(__file__).parent.resolve()
    
    # 定义要处理的CSV文件列表
    csv_files = [
        "twitter/bangladesh_flood/csvs/filtered_tweets_aug_to_oct_2024_with_local_paths_20250604_133037.csv",
        "twitter/assam_flood/csvs/filtered_assam_flood_tweets_20240501_20240801_with_local_paths_20250721_172531.csv",
        "twitter/kerala_flood/csvs/filtered_kerala_flood_tweets_20240715_20240901_with_local_paths_20250721_181731.csv",
        "twitter/pakistan_flood/csvs/filtered_pakistan_flood_tweets_20220601_20221101_with_local_paths_20250721_175020.csv",
    ]
    
    results = []
    
    # 处理每个CSV文件
    for csv_file in csv_files:
        csv_path = project_root / csv_file
        if not csv_path.exists():
            print(f"⚠️  File not found: {csv_path}")
            continue
        
        result = process_csv(str(csv_path), project_root)
        results.append(result)
    
    # 打印总结
    print(f"\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}")
    
    total_deleted_records = 0
    total_deleted_media = 0
    total_failed_media = 0
    
    for result in results:
        print(f"\n📄 {Path(result['csv_path']).name}")
        print(f"   Original records: {result['original_count']}")
        print(f"   Deleted records: {result['deleted_count']}")
        print(f"   Remaining records: {result['remaining_count']}")
        print(f"   Media files deleted: {result['media_deleted']}")
        if result['media_failed'] > 0:
            print(f"   Media files failed: {result['media_failed']}")
        
        total_deleted_records += result['deleted_count']
        total_deleted_media += result['media_deleted']
        total_failed_media += result['media_failed']
    
    print(f"\n{'='*70}")
    print("📈 TOTAL")
    print(f"{'='*70}")
    print(f"Total deleted records: {total_deleted_records}")
    print(f"Total deleted media files: {total_deleted_media}")
    if total_failed_media > 0:
        print(f"Total failed media deletions: {total_failed_media}")
    
    # 验证媒体文件对应关系
    print(f"\n{'='*70}")
    print("✅ VERIFICATION: Media File Correspondence")
    print(f"{'='*70}")
    
    for csv_file in csv_files:
        csv_path = project_root / csv_file
        if not csv_path.exists():
            continue
        
        print(f"\n📄 {Path(csv_file).name}")
        verification = verify_media_correspondence(str(csv_path), project_root)
        print(f"   Total records: {verification['total_records']}")
        print(f"   Records with media: {verification['records_with_media']}")
        print(f"   Records with missing media: {verification['records_with_missing_media']}")
        print(f"   Expected media files: {verification['total_expected_media']}")
        print(f"   Existing media files: {verification['total_existing_media']}")
        print(f"   Media match rate: {verification['media_match_rate']:.2%}")
        
        if verification['records_with_missing_media'] == 0:
            print(f"   ✅ All media files exist!")
        else:
            print(f"   ⚠️  Some media files are missing")


if __name__ == "__main__":
    main()

