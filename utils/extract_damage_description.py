#!/usr/bin/env python3
"""
提取洪水损害类别和图片描述
Extract flood damage categories and image descriptions
"""

import json
import os
import re
import base64
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import aiohttp
from io import BytesIO
from PIL import Image


class DamageDescriptionExtractor:
    """使用 Ollama VLM 提取损害类别和图片描述"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "qwen3-vl:32b-instruct"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self._image_cache = {}
        self._cache_max_size = 1000
        
        # 系统提示词
        self.system_prompt = """You are a precise visual analysis model for flood damage assessment.

TASK: Analyze flood-related images and extract:
1. Damage categories: Identify which types of damage are CLEARLY VISIBLE in the images
2. Image description: Provide a brief, factual description of what the images show

STRICT RULES:
- Only mark a damage category as true if it is CLEARLY VISIBLE in the images
- Do NOT infer damage from text alone - visual evidence required
- Be conservative: when uncertain, mark as false
- Keep description concise (2-3 sentences max)
- Focus on observable facts, not assumptions

OUTPUT: Return STRICT JSON ONLY, matching the schema exactly. No extra text."""
        
    def _compress_image(self, image_path: Path, max_short_side: int = 512, quality: int = 85) -> bytes:
        """压缩图片"""
        try:
            with Image.open(image_path) as img:
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                width, height = img.size
                if min(width, height) > max_short_side:
                    ratio = max_short_side / min(width, height)
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                output = BytesIO()
                img.save(output, format='JPEG', quality=quality, optimize=True)
                return output.getvalue()
        except Exception as e:
            print(f"⚠️  Image compression failed for {image_path}: {e}")
            with open(image_path, "rb") as f:
                return f.read()
    
    def encode_image(self, image_path: str, use_cache: bool = True) -> str:
        """将图像文件编码为 base64"""
        image_path_str = str(image_path)
        image_path = Path(image_path)
        
        if use_cache and image_path_str in self._image_cache:
            return self._image_cache[image_path_str]
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        image_data = self._compress_image(image_path)
        encoded = base64.b64encode(image_data).decode('utf-8')
        
        if use_cache:
            if len(self._image_cache) >= self._cache_max_size:
                oldest_key = next(iter(self._image_cache))
                del self._image_cache[oldest_key]
            self._image_cache[image_path_str] = encoded
        
        return encoded
    
    def _build_prompt(
        self,
        image_paths: List[str],
        project_root: Optional[Path] = None
    ) -> Tuple[str, List[str]]:
        """构建 prompt"""
        # 加载图像（最多3张）
        images_base64 = []
        for img_path in image_paths[:3]:
            try:
                if project_root:
                    full_path = project_root / img_path
                else:
                    full_path = Path(img_path)
                
                if full_path.exists():
                    img_b64 = self.encode_image(str(full_path))
                    images_base64.append(img_b64)
            except Exception:
                continue
        
        if not images_base64:
            raise ValueError("No images available")
        
        user_prompt = f"""Analyze the {len(images_base64)} attached flood-related image(s).

Extract VISIBLE damage categories and provide a brief description.

Return EXACTLY this JSON (and nothing else):
{{
  "damage_categories": {{
    "car": false,
    "house": false,
    "crops": false,
    "road": false,
    "bridge": false
  }},
  "image_description": ""
}}

FIELD DEFINITIONS:
- car: true if damaged/submerged vehicles (cars, motorcycles, trucks) are CLEARLY VISIBLE
- house: true if damaged/flooded buildings or residential structures are CLEARLY VISIBLE
- crops: true if damaged/flooded agricultural fields or crops are CLEARLY VISIBLE
- road: true if damaged/flooded roads or streets are CLEARLY VISIBLE
- bridge: true if damaged/flooded bridges are CLEARLY VISIBLE
- image_description: 2-3 sentence factual description of what the images show (scene, people, activities, damage level)

Only mark as true what you can CLEARLY SEE in the images."""
        
        return user_prompt, images_base64
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """解析模型响应，提取 JSON"""
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)
                if "damage_categories" in parsed and "image_description" in parsed:
                    return parsed
            except json.JSONDecodeError:
                pass
        
        print(f"⚠️  Failed to parse response, using default values. Response: {content[:200]}")
        return self._get_default_response()
    
    def _get_default_response(self) -> Dict[str, Any]:
        """返回默认的空响应结构"""
        return {
            "damage_categories": {
                "car": False,
                "house": False,
                "crops": False,
                "road": False,
                "bridge": False
            },
            "image_description": ""
        }

    def _make_payload(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建 Ollama 请求 payload"""
        return {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_gpu": 999,
                "num_ctx": 2048,
                "num_batch": 128,
                "format": "json",
                "temperature": 0.1, 
                "use_mmap": False
            },
            "keep_alive": "4h"
        }

    async def warm_up(self, session: Optional[aiohttp.ClientSession] = None) -> None:
        """预热模型"""
        warm_messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": "Warm up and respond with OK."}
        ]
        payload = self._make_payload(warm_messages)
        try:
            if session is None:
                async with aiohttp.ClientSession() as temp_session:
                    async with temp_session.post(
                        f"{self.base_url}/api/chat",
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=aiohttp.ClientTimeout(total=120, connect=30)
                    ) as response:
                        response.raise_for_status()
            else:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=120, connect=30)
                ) as response:
                    response.raise_for_status()
        except Exception as warm_err:
            print(f"⚠️  Warm-up request failed (ignored): {warm_err}")
    
    async def _send_request(
        self,
        user_prompt: str,
        images_base64: List[str],
        session: Optional[aiohttp.ClientSession] = None,
        max_retries: int = 5
    ) -> Dict[str, Any]:
        """发送分析请求（带重试机制）"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt, "images": images_base64}
        ]
        
        payload = self._make_payload(messages)
        
        for attempt in range(max_retries):
            try:
                if session is None:
                    async with aiohttp.ClientSession() as temp_session:
                        async with temp_session.post(
                            f"{self.base_url}/api/chat",
                            json=payload,
                            headers={"Content-Type": "application/json"},
                            timeout=aiohttp.ClientTimeout(total=600, connect=30)
                        ) as response:
                            response.raise_for_status()
                            result = await response.json()
                            content = result.get("message", {}).get("content", "")
                            return self._parse_response(content)
                else:
                    async with session.post(
                        f"{self.base_url}/api/chat",
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=aiohttp.ClientTimeout(total=600, connect=30)
                    ) as response:
                        response.raise_for_status()
                        result = await response.json()
                        content = result.get("message", {}).get("content", "")
                        return self._parse_response(content)
                        
            except (aiohttp.ClientError, ConnectionError, BrokenPipeError, OSError) as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"API connection failed after {max_retries} retries: {type(e).__name__}")
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Processing error after {max_retries} retries: {type(e).__name__}: {str(e)[:100]}")
        
        raise Exception("API request failed after all retries")


def flatten_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """将结果展平为 DataFrame 列"""
    flat = {}
    for damage_type, present in result["damage_categories"].items():
        flat[f"damage_{damage_type}"] = present
    flat["image_description"] = result["image_description"]
    return flat


async def process_csv_async(
    csv_path: str,
    output_csv_path: Optional[str] = None,
    model: str = "qwen3-vl:32b-instruct",
    base_url: str = "http://127.0.0.1:11434",
    start_idx: int = 0,
    max_rows: Optional[int] = None,
    resume: bool = True,
    max_concurrent: int = 2
):
    """异步处理 CSV 文件"""
    print(f"🌊 Extracting Damage Categories and Image Descriptions")
    print(f"⚡ Max concurrent requests: {max_concurrent}")
    print("=" * 70)
    
    # 读取 CSV
    print(f"\n📖 Reading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df)} rows")
    
    # 确定输出路径
    if output_csv_path is None:
        output_csv_path = csv_path
    
    # 获取项目根目录 (apify_scraper)
    csv_path_obj = Path(csv_path).resolve()
    # analysis/merged_all_flood_data.csv -> parent.parent = apify_scraper
    project_root = csv_path_obj.parent.parent
    
    # 初始化提取器
    extractor = DamageDescriptionExtractor(base_url=base_url, model=model)
    
    # 获取所有需要添加的列名
    default_response = extractor._get_default_response()
    flat_columns = flatten_result(default_response)
    
    # 添加新列（如果不存在）
    for col_name in flat_columns.keys():
        if col_name not in df.columns:
            df[col_name] = None
    
    # 添加标记列
    status_col = "damage_extraction_complete"
    if status_col not in df.columns:
        df[status_col] = False
    
    # 创建全局 aiohttp.ClientSession
    connector = aiohttp.TCPConnector(limit=max_concurrent * 2, limit_per_host=max_concurrent)
    timeout = aiohttp.ClientTimeout(total=600, connect=30)
    global_session = aiohttp.ClientSession(connector=connector, timeout=timeout)
    
    try:
        # 确定处理范围
        end_idx = len(df) if max_rows is None else min(start_idx + max_rows, len(df))
        rows_to_process = df.iloc[start_idx:end_idx]
        
        print(f"\n📊 Processing rows {start_idx} to {end_idx-1} (total: {len(rows_to_process)} rows)")
        print("-" * 70)
        
        # 准备任务列表
        tasks = []
        
        for idx, row in rows_to_process.iterrows():
            # 检查是否已经处理过
            if resume and pd.notna(row.get(status_col)) and row.get(status_col):
                continue
            
            # 根据 source 获取图片路径
            source = row.get("source", "")
            image_paths = []
            
            if source == "tiktok":
                # TikTok 使用 key_frames
                key_frames_str = row.get("key_frames", "")
                if pd.notna(key_frames_str) and str(key_frames_str).strip():
                    try:
                        if isinstance(key_frames_str, str):
                            image_paths = json.loads(key_frames_str)
                        elif isinstance(key_frames_str, list):
                            image_paths = key_frames_str
                    except Exception:
                        pass
            else:
                # Twitter 使用 all_images
                all_images_str = row.get("all_images", "")
                if pd.notna(all_images_str) and str(all_images_str).strip():
                    try:
                        if isinstance(all_images_str, str):
                            image_paths = json.loads(all_images_str)
                        elif isinstance(all_images_str, list):
                            image_paths = all_images_str
                    except Exception:
                        pass
            
            if not image_paths:
                continue
            
            tasks.append((idx, image_paths[:3]))
        
        if not tasks:
            print("✅ All rows already processed or no tasks to process")
            return
        
        print(f"🚀 Processing {len(tasks)} tasks with {max_concurrent} concurrent requests...")
        print("=" * 70)
        
        # 预热模型
        try:
            print("🔥 Warming up model...")
            await extractor.warm_up(global_session)
        except Exception as warm_err:
            print(f"⚠️  Warm-up skipped: {warm_err}")
        
        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)
        processed_count = asyncio.Lock()
        processed_num = [0]
        error_count = [0]
        session_lock = asyncio.Lock()
        
        async def process_single_task(task_data):
            """处理单个任务"""
            nonlocal global_session
            
            idx, image_paths = task_data
            row_num = idx + 1
            
            async with semaphore:
                try:
                    # 构建 prompt
                    user_prompt, images_base64 = extractor._build_prompt(
                        image_paths=image_paths,
                        project_root=project_root
                    )
                    
                    # 发送请求
                    attempt_result = None
                    for session_attempt in range(2):
                        try:
                            attempt_result = await extractor._send_request(
                                user_prompt=user_prompt,
                                images_base64=images_base64,
                                session=global_session
                            )
                            break
                        except Exception as request_error:
                            error_message = str(request_error)
                            if session_attempt == 0 and "API connection failed" in error_message:
                                async with session_lock:
                                    await global_session.close()
                                    connector = aiohttp.TCPConnector(limit=max_concurrent * 2, limit_per_host=max_concurrent)
                                    timeout = aiohttp.ClientTimeout(total=600, connect=30)
                                    global_session = aiohttp.ClientSession(connector=connector, timeout=timeout)
                                await asyncio.sleep(1)
                                continue
                            raise
                    
                    if attempt_result is None:
                        raise Exception("Failed to obtain result")
                    
                    # 展平结果并更新 DataFrame
                    flat_result = flatten_result(attempt_result)
                    for col_name, value in flat_result.items():
                        df.at[idx, col_name] = value
                    df.at[idx, status_col] = True
                    
                    # 更新计数
                    async with processed_count:
                        processed_num[0] += 1
                        current_count = processed_num[0]
                    
                    # 打印进度
                    damages = [k.replace("damage_", "") for k, v in flat_result.items() if k.startswith("damage_") and v]
                    damage_str = ", ".join(damages) if damages else "none"
                    print(f"[{current_count}/{len(tasks)}] Row {row_num}: ✅ Damages: [{damage_str}]")
                    
                    # 每处理10个任务保存一次
                    if current_count % 10 == 0:
                        df.to_csv(output_csv_path, index=False)
                        print(f"💾 Progress saved: {current_count}/{len(tasks)} processed")
                    
                except Exception as e:
                    async with processed_count:
                        error_count[0] += 1
                        processed_num[0] += 1
                        current_count = processed_num[0]
                    
                    error_msg = str(e)[:100]
                    print(f"❌ [{current_count}/{len(tasks)}] Row {row_num}: Failed - {error_msg}")
        
        # 并发执行所有任务
        await asyncio.gather(*[process_single_task(task) for task in tasks])
        
        # 保存最终结果
        print(f"\n💾 Saving final results to: {output_csv_path}")
        df.to_csv(output_csv_path, index=False)
        
        # 打印统计信息
        print("\n" + "=" * 70)
        print("📊 Summary:")
        print(f"   Total rows: {len(df)}")
        successful_count = processed_num[0] - error_count[0]
        print(f"   ✅ Successfully processed: {successful_count}")
        print(f"   ⏭️  Skipped (already processed): {len(rows_to_process) - len(tasks)}")
        print(f"   ❌ Failed: {error_count[0]}")
        
        if error_count[0] > 0:
            print(f"\n   💡 Tip: Re-run the script to retry {error_count[0]} failed rows")
        
        print(f"   Output saved to: {output_csv_path}")
        print("=" * 70)
    
    finally:
        await global_session.close()


def process_csv(
    csv_path: str,
    output_csv_path: Optional[str] = None,
    model: str = "qwen3-vl:32b-instruct",
    base_url: str = "http://127.0.0.1:11434",
    start_idx: int = 0,
    max_rows: Optional[int] = None,
    resume: bool = True,
    max_concurrent: int = 2
):
    """同步包装函数"""
    asyncio.run(process_csv_async(
        csv_path=csv_path,
        output_csv_path=output_csv_path,
        model=model,
        base_url=base_url,
        start_idx=start_idx,
        max_rows=max_rows,
        resume=resume,
        max_concurrent=max_concurrent
    ))


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="提取洪水损害类别和图片描述",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python extract_damage_description.py ../analysis/merged_all_flood_data.csv
  
  # 指定输出文件
  python extract_damage_description.py ../analysis/merged_all_flood_data.csv -o ../analysis/output.csv
  
  # 调整并发数
  python extract_damage_description.py ../analysis/merged_all_flood_data.csv --max-concurrent 4
        """
    )
    
    parser.add_argument("csv_path", help="CSV 文件路径")
    parser.add_argument("-o", "--output", help="输出 CSV 文件路径（默认覆盖原文件）")
    parser.add_argument("--model", default="qwen3-vl:32b-instruct", help="Ollama 模型名称")
    parser.add_argument("--base-url", default="http://127.0.0.1:11434", help="Ollama API URL")
    parser.add_argument("--start-idx", type=int, default=0, help="开始索引")
    parser.add_argument("--max-rows", type=int, help="最大处理行数")
    parser.add_argument("--no-resume", action="store_true", help="不使用断点续传")
    parser.add_argument("--max-concurrent", type=int, default=2, help="最大并发数")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_path):
        print(f"❌ CSV file not found: {args.csv_path}")
        return
    
    process_csv(
        csv_path=args.csv_path,
        output_csv_path=args.output,
        model=args.model,
        base_url=args.base_url,
        start_idx=args.start_idx,
        max_rows=args.max_rows,
        resume=not args.no_resume,
        max_concurrent=args.max_concurrent
    )
    
    print("\n🎉 Extraction completed!")


if __name__ == "__main__":
    main()

