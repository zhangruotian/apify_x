#!/usr/bin/env python3
"""
TikTok视频清理脚本
根据清理过的CSV文件，将相关视频复制到新的事件特定文件夹中，避免直接删除原始文件
"""

import os
import shutil
from typing import Dict, Set

import pandas as pd

# 数据集定义（基于tiktok_viewer.py）
DATASETS = {
    "Bangladesh Flood": {
        "csv_path": "tiktok/bangladesh_flood/csvs/tiktok_posts_20240801_to_20241031.csv",
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


def get_video_ids_from_csv(csv_path: str) -> Set[str]:
    """从CSV文件中提取视频ID"""
    video_ids = set()
    try:
        # 读取CSV时将id列作为字符串处理，避免科学记数法转换
        df = pd.read_csv(csv_path, dtype={"id": str})
        if "id" in df.columns:
            # ID已经是字符串格式，直接使用
            for video_id in df["id"]:
                video_ids.add(video_id.strip())
        else:
            print(f"警告：CSV文件 {csv_path} 中没有找到'id'列")
    except Exception as e:
        print(f"错误：读取CSV文件 {csv_path} 时出错: {e}")

    return video_ids


def get_available_videos(video_dir: str) -> Dict[str, str]:
    """获取视频目录中可用的视频文件"""
    video_files = {}
    if not os.path.exists(video_dir):
        print(f"警告：视频目录不存在 {video_dir}")
        return video_files

    for filename in os.listdir(video_dir):
        if filename.startswith("tiktok_") and filename.endswith(".mp4"):
            # 提取视频ID
            video_id = filename[7:-4]  # 去掉'tiktok_'前缀和'.mp4'后缀
            video_files[video_id] = os.path.join(video_dir, filename)

    return video_files


def create_cleaned_directory(event_name: str, base_dir: str) -> str:
    """创建清理后的视频目录"""
    # 将事件名称转换为文件夹友好的名称
    folder_name = event_name.lower().replace(" ", "_") + "_cleaned_videos"
    cleaned_dir = os.path.join(base_dir, folder_name)

    os.makedirs(cleaned_dir, exist_ok=True)
    return cleaned_dir


def copy_videos(
    video_ids: Set[str],
    available_videos: Dict[str, str],
    cleaned_dir: str,
    event_name: str,
) -> Dict[str, any]:
    """将匹配的视频复制到清理目录"""
    results = {"copied": 0, "missing": 0, "copied_files": [], "missing_ids": []}

    for video_id in video_ids:
        if video_id in available_videos:
            source_path = available_videos[video_id]
            filename = os.path.basename(source_path)
            dest_path = os.path.join(cleaned_dir, filename)

            try:
                shutil.copy2(source_path, dest_path)
                results["copied"] += 1
                results["copied_files"].append(filename)
                print(f"✓ 复制: {filename}")
            except Exception as e:
                print(f"✗ 复制失败 {filename}: {e}")
        else:
            results["missing"] += 1
            results["missing_ids"].append(video_id)
            print(f"✗ 缺失视频: tiktok_{video_id}.mp4")

    return results


def clean_videos_for_dataset(
    event_name: str, dataset_info: Dict[str, str]
) -> Dict[str, any]:
    """为单个数据集清理视频"""
    print(f"\n🔧 处理数据集: {event_name}")
    print(f"   CSV路径: {dataset_info['csv_path']}")
    print(f"   视频目录: {dataset_info['video_dir']}")

    # 步骤1：从CSV中提取视频ID
    video_ids = get_video_ids_from_csv(dataset_info["csv_path"])
    print(f"   CSV中找到 {len(video_ids)} 个视频ID")

    # 步骤2：获取可用的视频文件
    available_videos = get_available_videos(dataset_info["video_dir"])
    print(f"   视频目录中找到 {len(available_videos)} 个视频文件")

    # 步骤3：创建清理目录
    base_dir = os.path.dirname(dataset_info["video_dir"])
    cleaned_dir = create_cleaned_directory(event_name, base_dir)
    print(f"   清理目录: {cleaned_dir}")

    # 步骤4：复制匹配的视频
    results = copy_videos(video_ids, available_videos, cleaned_dir, event_name)

    # 添加统计信息
    results["total_csv_ids"] = len(video_ids)
    results["total_available_videos"] = len(available_videos)
    results["cleaned_dir"] = cleaned_dir

    return results


def main():
    """主函数"""
    print("🚀 开始TikTok视频清理流程...\n")

    all_results = {}
    total_copied = 0
    total_missing = 0

    # 处理每个数据集
    for event_name, dataset_info in DATASETS.items():
        results = clean_videos_for_dataset(event_name, dataset_info)
        all_results[event_name] = results
        total_copied += results["copied"]
        total_missing += results["missing"]

    # 打印总结报告
    print("\n" + "=" * 80)
    print("📊 清理结果总结")
    print("=" * 80)

    for event_name, results in all_results.items():
        print(f"\n📁 {event_name}:")
        print(f"   CSV中的视频ID数量: {results['total_csv_ids']}")
        print(f"   可用的视频文件数量: {results['total_available_videos']}")
        print(f"   成功复制: {results['copied']}")
        print(f"   缺失文件: {results['missing']}")
        print(f"   清理目录: {results['cleaned_dir']}")

        if results["missing"] > 0:
            print(f"   ⚠️  缺失的视频ID示例: {results['missing_ids'][:5]}")

    print("\n🎯 总计:")
    print(f"   总共复制: {total_copied} 个视频")
    print(f"   总共缺失: {total_missing} 个视频")

    if total_missing == 0:
        print("\n✅ 所有视频都已成功复制！")
    else:
        print(f"\n⚠️  有 {total_missing} 个视频在原始目录中未找到")

    print("\n✨ 清理完成！")


if __name__ == "__main__":
    main()
