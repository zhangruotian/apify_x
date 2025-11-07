#!/usr/bin/env python3
"""
清理多余的TikTok视频文件
删除videos目录中不在CSV文件中列出的视频，只保留CSV中对应的视频
"""

import os
import pandas as pd
from pathlib import Path

# 定义所有数据集配置（从tiktok_viewer.py中提取）
DATASETS = {
    "Bangladesh Flood": {
        "csv_path": "tiktok/bangladesh_flood/csvs/tiktok_posts_20240801_to_20241031_with_local_paths.csv",
        "video_dir": "tiktok/bangladesh_flood/videos",
    },
    "Assam Flood": {
        "csv_path": "tiktok/assam_flood/csvs/filtered_assam_flood_posts_20240501_20241120_with_local_paths.csv",
        "video_dir": "tiktok/assam_flood/videos",
    },
    "Kerala Flood": {
        "csv_path": "tiktok/kerala_flood/csvs/filtered_kerala_flood_posts_20240715_20241101_with_local_paths.csv",
        "video_dir": "tiktok/kerala_flood/videos",
    },
    "Pakistan Flood": {
        "csv_path": "tiktok/pakistan_flood/csvs/filtered_pakistan_flood_posts_20220601_20230101_with_local_paths.csv",
        "video_dir": "tiktok/pakistan_flood/videos",
    },
    "South Asia Flood": {
        "csv_path": "tiktok/south_asia_flood/csvs/filtered_south_asia_flood_posts_with_local_paths.csv",
        "video_dir": "tiktok/south_asia_flood/videos",
    },
}


def get_video_filenames_from_csv(csv_path, video_dir):
    """
    从CSV文件中提取应该保留的视频文件名
    
    Args:
        csv_path: CSV文件路径
        video_dir: 视频目录路径
        
    Returns:
        set: 应该保留的视频文件名集合（只包含文件名，不包含路径）
    """
    if not os.path.exists(csv_path):
        print(f"  ⚠️  CSV文件不存在: {csv_path}")
        return set()
    
    try:
        df = pd.read_csv(csv_path, dtype={"id": str})
        video_filenames = set()
        
        # 方法1: 如果CSV中有video_local_path列，从该列提取文件名
        if "video_local_path" in df.columns:
            for path in df["video_local_path"]:
                if pd.notna(path) and isinstance(path, str) and path.strip():
                    # 提取文件名
                    filename = os.path.basename(path.strip())
                    if filename:
                        video_filenames.add(filename)
        
        # 方法2: 如果没有video_local_path列，从id列构建文件名
        if not video_filenames and "id" in df.columns:
            for post_id in df["id"]:
                if pd.notna(post_id):
                    filename = f"tiktok_{post_id}.mp4"
                    video_filenames.add(filename)
        
        # 方法1和2都尝试：如果video_local_path存在但有些为空，用id补充
        if "video_local_path" in df.columns and "id" in df.columns:
            for idx, row in df.iterrows():
                video_local_path = row.get("video_local_path")
                post_id = row.get("id")
                
                # 如果video_local_path为空但id存在，使用id构建文件名
                if (pd.isna(video_local_path) or not str(video_local_path).strip()) and pd.notna(post_id):
                    filename = f"tiktok_{post_id}.mp4"
                    video_filenames.add(filename)
        
        return video_filenames
    
    except Exception as e:
        print(f"  ❌ 读取CSV文件时出错: {e}")
        return set()


def clean_videos_for_dataset(dataset_name, config):
    """
    清理单个数据集的视频文件
    
    Args:
        dataset_name: 数据集名称
        config: 数据集配置字典
    """
    print(f"\n{'='*60}")
    print(f"处理数据集: {dataset_name}")
    print(f"{'='*60}")
    
    csv_path = config["csv_path"]
    video_dir = config["video_dir"]
    
    # 转换为绝对路径
    project_root = Path(__file__).parent.parent
    csv_path_abs = project_root / csv_path
    video_dir_abs = project_root / video_dir
    
    print(f"CSV路径: {csv_path_abs}")
    print(f"视频目录: {video_dir_abs}")
    
    # 检查视频目录是否存在
    if not video_dir_abs.exists():
        print(f"  ⚠️  视频目录不存在: {video_dir_abs}")
        return
    
    # 从CSV中获取应该保留的视频文件名
    print(f"\n正在读取CSV文件以获取视频列表...")
    video_filenames_to_keep = get_video_filenames_from_csv(csv_path_abs, video_dir_abs)
    
    if not video_filenames_to_keep:
        print(f"  ⚠️  没有找到应该保留的视频文件")
        return
    
    print(f"  ✓ 找到 {len(video_filenames_to_keep)} 个应该在CSV中的视频文件")
    
    # 获取videos目录中的所有视频文件
    video_files_in_dir = []
    for file in video_dir_abs.iterdir():
        if file.is_file() and file.suffix.lower() == ".mp4":
            video_files_in_dir.append(file)
    
    print(f"  ✓ 视频目录中共有 {len(video_files_in_dir)} 个视频文件")
    
    # 找出需要删除的文件（在目录中但不在CSV中）
    files_to_delete = []
    files_to_keep = []
    
    for video_file in video_files_in_dir:
        filename = video_file.name
        if filename in video_filenames_to_keep:
            files_to_keep.append(filename)
        else:
            files_to_delete.append(video_file)
    
    print(f"\n统计结果:")
    print(f"  • 应该保留的视频: {len(files_to_keep)}")
    print(f"  • 应该删除的视频: {len(files_to_delete)}")
    
    # 验证：确保CSV中的所有视频都存在于目录中（至少被标记为保留）
    missing_videos = video_filenames_to_keep - set(files_to_keep)
    if missing_videos:
        print(f"\n  ⚠️  警告: CSV中列出的 {len(missing_videos)} 个视频在目录中不存在:")
        for filename in list(missing_videos)[:10]:  # 只显示前10个
            print(f"      - {filename}")
        if len(missing_videos) > 10:
            print(f"      ... 还有 {len(missing_videos) - 10} 个")
    
    # 删除多余的文件
    if not files_to_delete:
        print(f"\n  ✓ 没有需要删除的文件，所有视频都在CSV中")
        return
    
    print(f"\n准备删除 {len(files_to_delete)} 个多余视频文件...")
    
    # 显示前10个要删除的文件作为预览
    print(f"\n要删除的文件预览（前10个）:")
    for i, file_path in enumerate(files_to_delete[:10], 1):
        print(f"  {i}. {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.2f} MB)")
    
    if len(files_to_delete) > 10:
        print(f"  ... 还有 {len(files_to_delete) - 10} 个文件")
    
    # 确认删除
    print(f"\n⚠️  即将删除 {len(files_to_delete)} 个文件")
    response = input("确认删除？(yes/no): ").strip().lower()
    
    if response != "yes":
        print("  ❌ 取消删除操作")
        return
    
    # 执行删除
    deleted_count = 0
    failed_count = 0
    
    for file_path in files_to_delete:
        try:
            file_path.unlink()
            deleted_count += 1
        except Exception as e:
            print(f"  ❌ 删除失败 {file_path.name}: {e}")
            failed_count += 1
    
    print(f"\n✓ 删除完成:")
    print(f"  • 成功删除: {deleted_count} 个文件")
    if failed_count > 0:
        print(f"  • 删除失败: {failed_count} 个文件")
    
    # 计算释放的空间
    total_size = sum(f.stat().st_size for f in files_to_delete if f.exists())
    print(f"  • 释放空间: {total_size / 1024 / 1024:.2f} MB")


def main():
    """主函数：清理所有数据集的视频文件"""
    print("="*60)
    print("TikTok视频清理工具")
    print("="*60)
    print("\n此脚本将删除videos目录中不在CSV文件中列出的视频文件")
    print("只保留CSV中对应的视频文件\n")
    
    # 处理每个数据集
    for dataset_name, config in DATASETS.items():
        try:
            clean_videos_for_dataset(dataset_name, config)
        except Exception as e:
            print(f"\n❌ 处理数据集 {dataset_name} 时出错: {e}")
            continue
    
    print("\n" + "="*60)
    print("所有数据集处理完成！")
    print("="*60)


if __name__ == "__main__":
    main()

