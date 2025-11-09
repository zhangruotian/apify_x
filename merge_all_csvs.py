#!/usr/bin/env python3
"""
合并所有TikTok和Twitter的CSV文件到一个总CSV文件
- 对齐所有字段，不遗漏信息
- 添加source字段（tiktok/twitter）
- 添加region字段（assam, bangladesh, kerala, pakistan, south_asia）
- 确保从is_flood_related开始的字段顺序连续且不变
"""

import pandas as pd
import os
from pathlib import Path
from collections import OrderedDict

# 定义所有CSV文件路径和对应的source、region信息
CSV_FILES = [
    {
        'path': 'tiktok/assam_flood/csvs/filtered_assam_flood_posts_20240501_20241120_with_local_paths.csv',
        'source': 'tiktok',
        'region': 'assam'
    },
    {
        'path': 'tiktok/bangladesh_flood/csvs/tiktok_posts_20240801_to_20241031_with_local_paths.csv',
        'source': 'tiktok',
        'region': 'bangladesh'
    },
    {
        'path': 'tiktok/kerala_flood/csvs/filtered_kerala_flood_posts_20240715_20241101_with_local_paths.csv',
        'source': 'tiktok',
        'region': 'kerala'
    },
    {
        'path': 'tiktok/pakistan_flood/csvs/filtered_pakistan_flood_posts_20220601_20230101_with_local_paths.csv',
        'source': 'tiktok',
        'region': 'pakistan'
    },
    {
        'path': 'tiktok/south_asia_flood/csvs/filtered_south_asia_flood_posts_with_local_paths.csv',
        'source': 'tiktok',
        'region': 'south_asia'
    },
    {
        'path': 'twitter/assam_flood/csvs/filtered_assam_flood_tweets_20240501_20240801_with_local_paths_20250721_172531.csv',
        'source': 'twitter',
        'region': 'assam'
    },
    {
        'path': 'twitter/bangladesh_flood/csvs/filtered_tweets_aug_to_oct_2024_with_local_paths_20250604_133037.csv',
        'source': 'twitter',
        'region': 'bangladesh'
    },
    {
        'path': 'twitter/kerala_flood/csvs/filtered_kerala_flood_tweets_20240715_20240901_with_local_paths_20250721_181731.csv',
        'source': 'twitter',
        'region': 'kerala'
    },
    {
        'path': 'twitter/pakistan_flood/csvs/filtered_pakistan_flood_tweets_20220601_20221101_with_local_paths_20250721_175020.csv',
        'source': 'twitter',
        'region': 'pakistan'
    },
]

def get_analysis_fields_order():
    """
    确定从is_flood_related开始的所有字段的统一顺序
    按照字段在所有CSV中首次出现的顺序排列
    """
    analysis_fields_order = OrderedDict()
    
    for file_info in CSV_FILES:
        file_path = file_info['path']
        try:
            df = pd.read_csv(file_path, nrows=0)
            cols = list(df.columns)
            if 'is_flood_related' in cols:
                idx = cols.index('is_flood_related')
                analysis_fields = cols[idx:]
                # 记录每个字段出现的顺序（使用第一个出现的顺序）
                for field in analysis_fields:
                    if field not in analysis_fields_order:
                        analysis_fields_order[field] = len(analysis_fields_order)
        except Exception as e:
            print(f"  Warning: Could not read {file_path} to determine field order: {e}")
    
    return list(analysis_fields_order.keys())

def load_and_prepare_csv(file_info, analysis_fields_order):
    """加载CSV文件并添加source和region字段"""
    file_path = file_info['path']
    source = file_info['source']
    region = file_info['region']
    
    print(f"Loading {file_path}...")
    
    # 读取CSV文件
    try:
        df = pd.read_csv(file_path, low_memory=False)
        print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")
    except Exception as e:
        print(f"  Error loading {file_path}: {e}")
        return None
    
    # 添加或更新source和region字段（放在最前面）
    # 如果字段已存在，先删除再添加（确保值正确）
    if 'source' in df.columns:
        df = df.drop(columns=['source'])
    if 'region' in df.columns:
        df = df.drop(columns=['region'])
    
    df.insert(0, 'region', region)
    df.insert(0, 'source', source)
    
    return df

def merge_all_csvs():
    """合并所有CSV文件"""
    print("=" * 80)
    print("Starting CSV merge process...")
    print("=" * 80)
    
    # 首先确定从is_flood_related开始的字段顺序
    print("\nDetermining analysis fields order (from is_flood_related)...")
    analysis_fields_order = get_analysis_fields_order()
    print(f"  Found {len(analysis_fields_order)} analysis fields")
    
    # 加载所有CSV文件
    dataframes = []
    all_columns = set()
    
    for file_info in CSV_FILES:
        df = load_and_prepare_csv(file_info, analysis_fields_order)
        if df is not None:
            dataframes.append(df)
            all_columns.update(df.columns)
    
    if not dataframes:
        print("No dataframes loaded. Exiting.")
        return
    
    print(f"\nTotal unique columns across all files: {len(all_columns)}")
    
    # 构建统一的列顺序
    print("\nBuilding unified column order...")
    
    # 1. source和region在最前面
    priority_columns = ['source', 'region']
    
    # 2. 找出所有非分析字段（在is_flood_related之前的字段）
    non_analysis_fields = []
    for df in dataframes:
        cols = list(df.columns)
        if 'is_flood_related' in cols:
            idx = cols.index('is_flood_related')
            non_analysis = [c for c in cols[:idx] if c not in priority_columns]
            non_analysis_fields.extend(non_analysis)
    
    # 去重但保持顺序
    seen = set()
    ordered_non_analysis = []
    for col in non_analysis_fields:
        if col not in seen:
            seen.add(col)
            ordered_non_analysis.append(col)
    
    # 3. 从is_flood_related开始的分析字段（保持顺序）
    # 确保is_flood_related在分析字段列表的最前面
    if 'is_flood_related' in analysis_fields_order:
        analysis_fields_order.remove('is_flood_related')
    analysis_fields = ['is_flood_related'] + analysis_fields_order
    
    # 4. 构建最终列顺序
    ordered_columns = priority_columns + ordered_non_analysis + analysis_fields
    
    print(f"  Priority columns: {len(priority_columns)}")
    print(f"  Non-analysis columns: {len(ordered_non_analysis)}")
    print(f"  Analysis columns (from is_flood_related): {len(analysis_fields)}")
    print(f"  Total columns: {len(ordered_columns)}")
    
    # 对齐所有DataFrame的列
    print("\nAligning columns...")
    aligned_dfs = []
    for i, df in enumerate(dataframes):
        # 重新排序列 - 使用更高效的方法
        missing_cols = [col for col in ordered_columns if col not in df.columns]
        if missing_cols:
            # 一次性添加所有缺失的列
            df = pd.concat([df, pd.DataFrame(None, index=df.index, columns=missing_cols)], axis=1)
        df = df[ordered_columns].copy()  # 使用copy()避免fragmentation警告
        aligned_dfs.append(df)
        print(f"  Aligned DataFrame {i+1}: {len(df)} rows, {len(df.columns)} columns")
    
    # 合并所有DataFrame
    print("\nMerging all dataframes...")
    merged_df = pd.concat(aligned_dfs, ignore_index=True, sort=False)
    
    print(f"\nMerged DataFrame: {len(merged_df)} rows, {len(merged_df.columns)} columns")
    
    # 验证is_flood_related之后的字段顺序
    merged_cols = list(merged_df.columns)
    if 'is_flood_related' in merged_cols:
        idx = merged_cols.index('is_flood_related')
        merged_analysis_fields = merged_cols[idx:]
        print(f"\nVerifying analysis fields order...")
        print(f"  Expected first 5: {analysis_fields[:5]}")
        print(f"  Actual first 5: {merged_analysis_fields[:5]}")
        if merged_analysis_fields[:len(analysis_fields)] == analysis_fields:
            print("  ✓ Analysis fields order is correct!")
        else:
            print("  ⚠️  Warning: Analysis fields order may differ")
    
    # 统计信息
    print("\n" + "=" * 80)
    print("Summary Statistics:")
    print("=" * 80)
    print(f"Total records: {len(merged_df)}")
    print(f"\nBy source:")
    print(merged_df['source'].value_counts().to_string())
    print(f"\nBy region:")
    print(merged_df['region'].value_counts().to_string())
    print(f"\nBy source and region:")
    print(merged_df.groupby(['source', 'region']).size().to_string())
    
    # 保存合并后的CSV
    output_file = 'merged_all_flood_data.csv'
    print(f"\nSaving merged data to {output_file}...")
    merged_df.to_csv(output_file, index=False)
    print(f"✓ Saved {len(merged_df)} rows to {output_file}")
    
    # 保存列信息到文件（便于后续分析）
    columns_info_file = 'merged_csv_columns_info.txt'
    with open(columns_info_file, 'w') as f:
        f.write("Columns in merged CSV:\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total columns: {len(merged_df.columns)}\n")
        f.write(f"\nPriority columns (first 2):\n")
        for i, col in enumerate(merged_df.columns[:2], 1):
            non_null_count = merged_df[col].notna().sum()
            f.write(f"  {i}. {col:<50} (non-null: {non_null_count}/{len(merged_df)})\n")
        
        if 'is_flood_related' in merged_df.columns:
            idx = list(merged_df.columns).index('is_flood_related')
            f.write(f"\nAnalysis columns (from is_flood_related, column {idx+1} onwards):\n")
            analysis_cols = list(merged_df.columns)[idx:]
            for i, col in enumerate(analysis_cols, 1):
                non_null_count = merged_df[col].notna().sum()
                f.write(f"  {i}. {col:<50} (non-null: {non_null_count}/{len(merged_df)})\n")
        else:
            f.write("\nAll columns:\n")
            for i, col in enumerate(merged_df.columns, 1):
                non_null_count = merged_df[col].notna().sum()
                f.write(f"{i:3d}. {col:<50} (non-null: {non_null_count}/{len(merged_df)})\n")
    
    print(f"✓ Saved column information to {columns_info_file}")
    
    return merged_df

if __name__ == '__main__':
    merged_df = merge_all_csvs()
    print("\n" + "=" * 80)
    print("Merge completed successfully!")
    print("=" * 80)

