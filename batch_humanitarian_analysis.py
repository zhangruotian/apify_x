#!/usr/bin/env python3
"""
批量人道主义影响分析脚本
Batch processing script for humanitarian impact analysis
"""

import os
import sys
import subprocess
from pathlib import Path
from glob import glob


def main():
    """批量处理所有 TikTok 和 Twitter CSV 文件"""
    # 配置
    MAX_CONCURRENT = 2
    BASE_URL = "http://127.0.0.1:11434"
    MODEL = "qwen3-vl:32b-instruct"
    
    # 获取脚本目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🌊 Batch Humanitarian Impact Analysis")
    print("=" * 70)
    print(f"📁 Working directory: {script_dir}")
    print(f"⚡ Max concurrent: {MAX_CONCURRENT}")
    print(f"🤖 Model: {MODEL}")
    print()
    
    # 处理 TikTok 文件
    print("=" * 70)
    print("🎵 Processing TikTok Files (5 folders)")
    print("=" * 70)
    print()
    
    tiktok_files = sorted(glob("tiktok/*/csvs/*.csv"))
    tiktok_count = 0
    
    for csv_file in tiktok_files:
        if os.path.isfile(csv_file):
            tiktok_count += 1
            print(f"[{tiktok_count}/{len(tiktok_files)}] Processing: {csv_file}")
            
            try:
                subprocess.run([
                    sys.executable,
                    "humanitarian_impact_analysis.py",
                    csv_file,
                    "--platform", "tiktok",
                    "--model", MODEL,
                    "--base-url", BASE_URL,
                    "--max-concurrent", str(MAX_CONCURRENT)
                ], check=True)
                
                print(f"✅ Completed: {csv_file}")
                print()
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed: {csv_file}")
                print(f"   Error: {e}")
                print()
                # 继续处理下一个文件
                continue
    
    print(f"✨ TikTok processing complete: {tiktok_count} files")
    print()
    
    # 处理 Twitter 文件
    print("=" * 70)
    print("🐦 Processing Twitter Files (4 folders)")
    print("=" * 70)
    print()
    
    twitter_files = sorted(glob("twitter/*/csvs/*.csv"))
    twitter_count = 0
    
    for csv_file in twitter_files:
        if os.path.isfile(csv_file):
            twitter_count += 1
            print(f"[{twitter_count}/{len(twitter_files)}] Processing: {csv_file}")
            
            try:
                subprocess.run([
                    sys.executable,
                    "humanitarian_impact_analysis.py",
                    csv_file,
                    "--platform", "twitter",
                    "--model", MODEL,
                    "--base-url", BASE_URL,
                    "--max-concurrent", str(MAX_CONCURRENT)
                ], check=True)
                
                print(f"✅ Completed: {csv_file}")
                print()
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed: {csv_file}")
                print(f"   Error: {e}")
                print()
                # 继续处理下一个文件
                continue
    
    print(f"✨ Twitter processing complete: {twitter_count} files")
    print()
    
    # 统计信息
    print("=" * 70)
    print("🎉 All Processing Complete!")
    print("=" * 70)
    print(f"TikTok files processed: {tiktok_count}")
    print(f"Twitter files processed: {twitter_count}")
    print(f"Total files processed: {tiktok_count + twitter_count}")
    print()
    print("📊 Results have been appended to the original CSV files.")
    print("You can now analyze the statistics using pandas or other tools.")


if __name__ == "__main__":
    main()

