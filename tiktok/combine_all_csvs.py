#!/usr/bin/env python3
"""
合并所有TikTok数据集的CSV文件并去重
"""

import os

import pandas as pd

# 定义所有数据集
DATASETS = {
    "Bangladesh Flood": {
        "csv_path": "tiktok/bangladesh_flood/csvs/tiktok_posts_20240801_to_20241031.csv",
        "video_dir": "tiktok/bangladesh_flood/videos",
        "event": "Bangladesh Flood",
    },
    "Assam Flood": {
        "csv_path": "tiktok/assam_flood/csvs/filtered_assam_flood_posts_20240501_20241120_with_local_paths.csv",
        "video_dir": "tiktok/assam_flood/videos",
        "event": "Assam Flood",
    },
    "Kerala Flood": {
        "csv_path": "tiktok/kerala_flood/csvs/filtered_kerala_flood_posts_20240715_20241101_with_local_paths.csv",
        "video_dir": "tiktok/kerala_flood/videos",
        "event": "Kerala Flood",
    },
    "Pakistan Flood": {
        "csv_path": "tiktok/pakistan_flood/csvs/filtered_pakistan_flood_posts_20220601_20230101_with_local_paths.csv",
        "video_dir": "tiktok/pakistan_flood/videos",
        "event": "Pakistan Flood",
    },
    "South Asia Flood": {
        "csv_path": "tiktok/south_asia_flood/csvs/filtered_south_asia_flood_posts_with_local_paths.csv",
        "video_dir": "tiktok/south_asia_flood/videos",
        "event": "South Asia Flood",
    },
}


def load_and_standardize_csv(csv_path, event_name, video_dir):
    """加载CSV文件并标准化列"""
    print(f"加载 {event_name}: {csv_path}")

    if not os.path.exists(csv_path):
        print(f"⚠️  文件不存在: {csv_path}")
        return None

    try:
        # 读取CSV时将id列作为字符串处理
        df = pd.read_csv(csv_path, dtype={"id": str})

        # 添加事件标识和本地视频路径
        df["event"] = event_name
        df["video_local_path"] = df["id"].apply(lambda x: f"{video_dir}/tiktok_{x}.mp4")

        print(f"✓ 成功加载 {len(df)} 条记录")
        return df

    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return None


def combine_csvs():
    """合并所有CSV文件"""
    print("🚀 开始合并TikTok数据集...\n")

    all_dataframes = []
    stats = {}

    # 加载所有数据集
    for dataset_name, dataset_info in DATASETS.items():
        df = load_and_standardize_csv(
            dataset_info["csv_path"], dataset_info["event"], dataset_info["video_dir"]
        )

        if df is not None:
            all_dataframes.append(df)
            stats[dataset_name] = len(df)
        else:
            stats[dataset_name] = 0

        print()

    if not all_dataframes:
        print("❌ 没有成功加载任何数据集")
        return

    # 合并所有数据
    print("🔄 合并数据...")
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    print(f"✓ 合并完成，总计 {len(combined_df)} 条记录")

    # 去重（基于id列）
    print("🔄 去除重复记录...")
    original_count = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset=["id"], keep="first")
    deduplicated_count = len(combined_df)
    removed_duplicates = original_count - deduplicated_count

    print(f"✓ 去重完成，移除了 {removed_duplicates} 条重复记录")
    print(f"✓ 最终数据集包含 {deduplicated_count} 条唯一记录")

    # 按上传时间排序
    if "uploaded_at" in combined_df.columns:
        print("🔄 按上传时间排序...")
        combined_df = combined_df.sort_values("uploaded_at", ascending=False)
        print("✓ 排序完成")

    # 保存合并后的CSV
    output_path = "tiktok/combined_all_floods.csv"
    print(f"💾 保存到 {output_path}...")
    combined_df.to_csv(output_path, index=False)
    print("✓ 保存完成")

    # 打印统计信息
    print("\n" + "=" * 60)
    print("📊 数据集统计")
    print("=" * 60)

    for dataset_name, count in stats.items():
        print(f"{dataset_name:20s}: {count:4d} 条记录")

    print(f"{'':20s}   ----")
    print(f"{'原始总计':20s}: {original_count:4d} 条记录")
    print(f"{'去重后总计':20s}: {deduplicated_count:4d} 条记录")
    print(f"{'重复记录':20s}: {removed_duplicates:4d} 条记录")

    # 按事件统计去重后的数据
    print("\n📈 去重后按事件统计:")
    event_stats = combined_df["event"].value_counts().sort_index()
    for event, count in event_stats.items():
        print(f"{event:20s}: {count:4d} 条记录")

    print(f"\n✨ 合并完成！输出文件: {output_path}")

    return output_path, stats, combined_df


if __name__ == "__main__":
    combine_csvs()
