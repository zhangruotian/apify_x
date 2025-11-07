#!/usr/bin/env python3
"""
使用 Ollama Qwen VLM 模型对 TikTok 数据进行洪水相关性标注
"""

import json
import os
import re
import base64
import requests
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import time
import asyncio
import aiohttp
from io import BytesIO
from PIL import Image


class OllamaVLMClassifier:
    """使用 Ollama VLM 进行洪水相关性分类"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "qwen3-vl:30b-a3b-instruct-q4_K_M"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self._session = None  # 用于异步请求的 session
        self._image_cache = {}  # LRU 缓存：路径 -> base64
        self._cache_max_size = 1000  # 缓存最大条目数
        
    def _compress_image(self, image_path: Path, max_short_side: int = 768, quality: int = 85) -> bytes:
        """压缩图片：短边≤768，JPEG quality=85，optimize=True"""
        try:
            with Image.open(image_path) as img:
                # 转换为 RGB（如果是 RGBA 或其他格式）
                if img.mode in ('RGBA', 'LA', 'P'):
                    # 创建白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 计算缩放比例（短边≤768）
                width, height = img.size
                if min(width, height) > max_short_side:
                    ratio = max_short_side / min(width, height)
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # JPEG 压缩
                output = BytesIO()
                img.save(output, format='JPEG', quality=quality, optimize=True)
                return output.getvalue()
        except Exception as e:
            # 如果压缩失败，返回原图
            print(f"⚠️  Image compression failed for {image_path}: {e}, using original")
            with open(image_path, "rb") as f:
                return f.read()
    
    def encode_image(self, image_path: str, use_cache: bool = True) -> str:
        """将图像文件编码为 base64（带压缩和缓存）"""
        image_path_str = str(image_path)
        image_path = Path(image_path)
        
        # 检查缓存
        if use_cache and image_path_str in self._image_cache:
            return self._image_cache[image_path_str]
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # 压缩图片
        image_data = self._compress_image(image_path)
        
        # 编码为 base64
        encoded = base64.b64encode(image_data).decode('utf-8')
        
        # 更新缓存（LRU 策略）
        if use_cache:
            if len(self._image_cache) >= self._cache_max_size:
                # 删除最旧的条目（简单策略：删除第一个）
                oldest_key = next(iter(self._image_cache))
                del self._image_cache[oldest_key]
            self._image_cache[image_path_str] = encoded
        
        return encoded
    
    def classify_flood_relevance(
        self,
        title: str,
        transcription: str,
        hashtags: str,
        image_paths: List[str],
        project_root: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        使用 VLM 判断帖子是否与洪水相关
        
        Returns:
            Dict with keys: is_flood_related (bool), confidence (str), reason (str)
        """
        # 构建文本信息，按优先级组织
        # 优先级：Title > Hashtags > Transcription (transcription可能不准确)
        reliable_text_parts = []
        if title and str(title).strip() and str(title).strip().lower() != 'nan':
            reliable_text_parts.append(f"Title: {title}")
        if hashtags and str(hashtags).strip() and str(hashtags).strip().lower() != 'nan':
            reliable_text_parts.append(f"Hashtags: {hashtags}")
        
        reliable_text = "\n".join(reliable_text_parts) if reliable_text_parts else None
        
        # Transcription 单独处理，标记为可能不可靠
        has_transcription = False
        transcription_text = None
        if transcription and str(transcription).strip() and str(transcription).strip().lower() != 'nan':
            has_transcription = True
            transcription_text = str(transcription).strip()
        
        # 限制图片数量（最多使用3张关键帧，以减少 IO 并发）
        total_frames = len(image_paths)
        max_images = 3
        image_paths_limited = image_paths[:max_images] if total_frames > max_images else image_paths
        
        # 加载图像
        images_base64 = []
        for img_path in image_paths_limited:
            try:
                if project_root:
                    full_path = project_root / img_path
                else:
                    full_path = Path(img_path)
                
                if full_path.exists():
                    img_b64 = self.encode_image(str(full_path))
                    images_base64.append(img_b64)
            except Exception as e:
                print(f"⚠️  Warning: Failed to load image {img_path}: {e}")
                continue
        
        if not images_base64:
            print("⚠️  Warning: No images available for this post")
            return {
                "is_flood_related": False,
                "confidence": "low",
                "reason": "No images available"
            }
        
        # 构建 prompt（精简版）
        prompt_parts = [
            "Analyze if this TikTok post is flood-related. Consider ALL sources (title, hashtags, transcription, images) and make a COMPREHENSIVE judgment.",
            "",
            "Return TRUE if floods/flooding is the PRIMARY content:",
            "- Visual: flooded areas, water damage, rescue operations",
            "- Text: discussions of floods, impacts, events",
            "- News/reporting about flooding",
            "- Political/social commentary where flooding is MAIN topic",
            "",
            "Return FALSE if:",
            "- Only passing mention (not main topic)",
            "- Unrelated content using water words",
            "- Visual contradicts text claims",
            "",
            "Analysis: (1) Examine each source, (2) Check consistency, (3) Determine if flooding is PRIMARY subject",
            "",
            "Strong indicators (TRUE): Multiple sources mention floods consistently, flood hashtags (#flood, #bangladeshfloods), detailed flood discussion, visual flood evidence.",
            "",
            "Weak indicators (consider context): Brief mention, generic water imagery, metaphorical flood terms.",
            ""
        ]
        
        # 添加文本信息
        if reliable_text:
            prompt_parts.append(f"Title/Hashtags: {reliable_text}")
            prompt_parts.append("")
        
        # 添加transcription
        if has_transcription and transcription_text:
            prompt_parts.append(f"Audio/Speech: {transcription_text}")
            prompt_parts.append("")
        
        if total_frames > len(images_base64):
            visual_info = f"Visual: {len(images_base64)} key frame(s) attached (selected from {total_frames} total frames)."
        else:
            visual_info = f"Visual: {len(images_base64)} key frame(s) attached."
        
        prompt_parts.extend([
            visual_info,
            "",
            "Respond ONLY with JSON:",
            '{"is_flood_related": true/false, "confidence": "high/medium/low", "reason": "brief explanation"}'
        ])
        
        prompt = "\n".join(prompt_parts)
        
        # 构建消息
        message = {
            "role": "user",
            "content": prompt,
            "images": images_base64
        }
        
        # 发送请求
        payload = {
            "model": self.model,
            "messages": [message],
            "stream": False
        }
        
        # 同步请求也添加重试机制
        max_retries = 3
        last_error = None
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=600  # 10分钟超时
                )
                response.raise_for_status()
                result = response.json()
                
                # 提取响应内容
                content = result.get("message", {}).get("content", "")
                
                # 解析 JSON 响应
                return self._parse_response(content)
                
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, BrokenPipeError, OSError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"⚠️  Connection error (attempt {attempt + 1}/{max_retries}): {type(e).__name__}. Retrying in {wait_time}s...")
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Max retries reached. Error: {type(e).__name__}")
                    return {
                        "is_flood_related": False,
                        "confidence": "low",
                        "reason": "API connection failed after retries"
                    }
            except Exception as e:
                print(f"❌ Unexpected error: {type(e).__name__}: {str(e)[:100]}")
                return {
                    "is_flood_related": False,
                    "confidence": "low",
                    "reason": "Processing error"
                }
        
        return {
            "is_flood_related": False,
            "confidence": "low",
            "reason": "API request failed"
        }
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """解析模型响应，提取 JSON"""
        # 尝试提取 JSON 对象
        # 方法1: 直接查找 JSON 对象
        json_match = re.search(r'\{[^{}]*"is_flood_related"[^{}]*\}', content, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)
                return {
                    "is_flood_related": bool(parsed.get("is_flood_related", False)),
                    "confidence": str(parsed.get("confidence", "low")).lower(),
                    "reason": str(parsed.get("reason", ""))
                }
            except json.JSONDecodeError:
                pass
        
        # 方法2: 查找所有可能的 JSON
        json_patterns = [
            r'\{[^}]*"is_flood_related"[^}]*\}',
            r'is_flood_related["\s]*:\s*(true|false)',
            r'"is_flood_related"["\s]*:\s*(true|false)',
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                if 'true' in match.group(0).lower():
                    return {
                        "is_flood_related": True,
                        "confidence": "medium",
                        "reason": "Parsed from response"
                    }
                elif 'false' in match.group(0).lower():
                    return {
                        "is_flood_related": False,
                        "confidence": "medium",
                        "reason": "Parsed from response"
                    }
        
        # 方法3: 基于关键词的启发式判断
        content_lower = content.lower()
        if any(keyword in content_lower for keyword in ["related", "flood", "yes", "true"]):
            if any(keyword in content_lower for keyword in ["not", "unrelated", "false", "no"]):
                is_related = False
            else:
                is_related = True
        else:
            is_related = False
        
        return {
            "is_flood_related": is_related,
            "confidence": "low",
            "reason": f"Fallback parsing: {content[:200]}"
        }
    
    def _build_prompt(
        self,
        title: str,
        transcription: str,
        hashtags: str,
        image_paths: List[str],
        project_root: Optional[Path] = None,
        total_frames: Optional[int] = None
    ) -> Tuple[str, List[str]]:
        """
        构建 prompt 和加载图像（内部方法，供同步和异步版本共用）
        
        Returns:
            (prompt, images_base64)
        """
        # 构建文本信息
        reliable_text_parts = []
        if title and str(title).strip() and str(title).strip().lower() != 'nan':
            reliable_text_parts.append(f"Title: {title}")
        if hashtags and str(hashtags).strip() and str(hashtags).strip().lower() != 'nan':
            reliable_text_parts.append(f"Hashtags: {hashtags}")
        
        reliable_text = "\n".join(reliable_text_parts) if reliable_text_parts else None
        
        has_transcription = False
        transcription_text = None
        if transcription and str(transcription).strip() and str(transcription).strip().lower() != 'nan':
            has_transcription = True
            transcription_text = str(transcription).strip()
        
        # 加载图像（使用全部关键帧）
        images_base64 = []
        for img_path in image_paths:
            try:
                if project_root:
                    full_path = project_root / img_path
                else:
                    full_path = Path(img_path)
                
                if full_path.exists():
                    img_b64 = self.encode_image(str(full_path))
                    images_base64.append(img_b64)
            except Exception as e:
                continue
        
        if not images_base64:
            raise ValueError("No images available")
        
        # 构建 prompt（精简版）
        prompt_parts = [
            "Analyze if this TikTok post is flood-related. Consider ALL sources (title, hashtags, transcription, images) and make a COMPREHENSIVE judgment.",
            "",
            "Return TRUE if floods/flooding is the PRIMARY content:",
            "- Visual: flooded areas, water damage, rescue operations",
            "- Text: discussions of floods, impacts, events",
            "- News/reporting about flooding",
            "- Political/social commentary where flooding is MAIN topic",
            "",
            "Return FALSE if:",
            "- Only passing mention (not main topic)",
            "- Unrelated content using water words",
            "- Visual contradicts text claims",
            "",
            "Analysis: (1) Examine each source, (2) Check consistency, (3) Determine if flooding is PRIMARY subject",
            "",
            "Strong indicators (TRUE): Multiple sources mention floods consistently, flood hashtags (#flood, #bangladeshfloods), detailed flood discussion, visual flood evidence.",
            "",
            "Weak indicators (consider context): Brief mention, generic water imagery, metaphorical flood terms.",
            ""
        ]
        
        if reliable_text:
            prompt_parts.append(f"Title/Hashtags: {reliable_text}")
            prompt_parts.append("")
        
        if has_transcription and transcription_text:
            prompt_parts.append(f"Audio/Speech: {transcription_text}")
            prompt_parts.append("")
        
        # 显示图片数量信息
        if total_frames and total_frames > len(images_base64):
            visual_info = f"Visual: {len(images_base64)} key frame(s) attached (selected from {total_frames} total frames)."
        else:
            visual_info = f"Visual: {len(images_base64)} key frame(s) attached."
        
        prompt_parts.extend([
            visual_info,
            "",
            "Respond ONLY with JSON:",
            '{"is_flood_related": true/false, "confidence": "high/medium/low", "reason": "brief explanation"}'
        ])
        
        prompt = "\n".join(prompt_parts)
        return prompt, images_base64
    
    async def _send_classification_request(
        self,
        prompt: str,
        images_base64: List[str],
        session: Optional[aiohttp.ClientSession] = None,
        max_retries: int = 5
    ) -> Dict[str, Any]:
        """
        发送分类请求（内部方法，带重试机制）
        """
        # 构建消息
        message = {
            "role": "user",
            "content": prompt,
            "images": images_base64
        }
        
        # 发送异步请求（带 keep_alive 和优化选项）
        payload = {
            "model": self.model,
            "messages": [message],
            "stream": False,
            "options": {
                "num_gpu": 999,  # 使用所有可用GPU
                "num_ctx": 1536,  # 上下文窗口
                "num_batch": 1024,  # 批处理大小
                "kv_cache_type": "q8_0",  # KV缓存类型
                "use_mmap": True  # 本机NVMe使用mmap，网络盘设为False
            },
            "keep_alive": "2h"  # 保持模型加载2小时
        }
        
        last_error = None
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
                        
            except (aiohttp.ClientError, ConnectionError, BrokenPipeError, OSError, aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3  # 3s, 6s, 9s, 12s, 15s
                    await asyncio.sleep(wait_time)
                    # 不打印重试信息，避免日志过多
                    continue
                else:
                    # 所有重试都失败，抛出异常让上层处理
                    raise Exception(f"API connection failed after {max_retries} retries: {type(e).__name__}")
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Processing error after {max_retries} retries: {type(e).__name__}: {str(e)[:100]}")
        
        # 不应该到达这里，但以防万一
        raise Exception("API request failed after all retries")


async def process_csv_async(
    csv_path: str,
    output_csv_path: Optional[str] = None,
    model: str = "qwen3-vl:30b-a3b-instruct-q4_K_M",
    base_url: str = "http://127.0.0.1:11434",
    start_idx: int = 0,
    max_rows: Optional[int] = None,
    resume: bool = True,
    max_concurrent: int = 2
):
    """
    异步处理 CSV 文件，添加洪水相关性标注（支持并发批量处理）
    
    Args:
        csv_path: 输入 CSV 文件路径
        output_csv_path: 输出 CSV 文件路径（如果为 None，则覆盖原文件）
        model: Ollama 模型名称
        base_url: Ollama API 基础 URL
        start_idx: 开始处理的索引（用于断点续传）
        max_rows: 最大处理行数（None 表示处理所有）
        resume: 是否跳过已有标注的行
        max_concurrent: 最大并发数（默认2，避免连接错误）
    """
    print("🌊 Starting flood relevance classification (Async Mode)")
    print(f"⚡ Max concurrent requests: {max_concurrent}")
    print("=" * 70)
    
    # 读取 CSV
    print(f"\n📖 Reading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df)} rows")
    
    # 确定输出路径
    if output_csv_path is None:
        output_csv_path = csv_path
    
    # 获取项目根目录
    csv_path_obj = Path(csv_path).resolve()
    if csv_path_obj.parts[-3] == "csvs":
        project_root = csv_path_obj.parent.parent.parent.parent
    else:
        project_root = Path(csv_path).resolve()
        while project_root.parent != project_root:
            if any(p in ["tiktok", "twitter"] for p in project_root.parts):
                if project_root.name in ["tiktok", "twitter"]:
                    project_root = project_root.parent
                break
            project_root = project_root.parent
        if project_root == Path(csv_path).resolve():
            project_root = Path.cwd()
    
    # 添加新列（如果不存在）
    classification_column = "is_flood_related"
    confidence_column = "flood_classification_confidence"
    reason_column = "flood_classification_reason"
    
    if classification_column not in df.columns:
        df[classification_column] = None
    if confidence_column not in df.columns:
        df[confidence_column] = None
    if reason_column not in df.columns:
        df[reason_column] = None
    
    # 初始化分类器
    classifier = OllamaVLMClassifier(base_url=base_url, model=model)
    
    # 创建全局 aiohttp.ClientSession（复用连接）
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
        task_indices = []
        
        for idx, row in rows_to_process.iterrows():
            # 检查是否已经处理过
            if resume and pd.notna(row.get(classification_column)):
                reason_val = row.get(reason_column)
                # 如果之前记录的是错误信息，则视为未处理，需重新尝试
                if isinstance(reason_val, str) and "error" in reason_val.lower():
                    df.at[idx, classification_column] = None
                    df.at[idx, confidence_column] = None
                    df.at[idx, reason_column] = None
                else:
                    continue
            
            # 提取数据
            title = row.get("title", "")
            transcription = row.get("transcription_english", "")
            hashtags = row.get("hashtags", "")
            
            # 解析 key_frames
            key_frames_str = row.get("key_frames", "")
            image_paths = []
            
            if pd.notna(key_frames_str) and str(key_frames_str).strip():
                try:
                    if isinstance(key_frames_str, str):
                        image_paths = json.loads(key_frames_str)
                    elif isinstance(key_frames_str, list):
                        image_paths = key_frames_str
                except Exception:
                    pass
            
            if not image_paths:
                # 标记为无图像
                df.at[idx, classification_column] = False
                df.at[idx, confidence_column] = "low"
                df.at[idx, reason_column] = "No key frames available"
                continue
            
            # 限制图片数量：只使用前1-2张关键帧（E. 限制图像并发）
            max_images = 3
            image_paths_limited = image_paths[:max_images]
            
            # 创建任务
            tasks.append((idx, title, transcription, hashtags, image_paths_limited, image_paths))
            task_indices.append(idx)
    
        if not tasks:
            print("✅ All rows already processed or no tasks to process")
            return
        
        print(f"🚀 Processing {len(tasks)} tasks with {max_concurrent} concurrent requests...")
        print("=" * 70)
        
        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)
        processed_count = asyncio.Lock()
        processed_num = [0]
        error_count = [0]
        session_lock = asyncio.Lock()
        
        async def process_single_task(task_data):
            """处理单个任务"""
            nonlocal global_session
            idx, title, transcription, hashtags, image_paths_limited, image_paths_all = task_data
            row_num = idx + 1
            
            async with semaphore:
                try:
                    # 构建 prompt（使用限制后的图片）
                    prompt, images_base64 = classifier._build_prompt(
                        title=title,
                        transcription=transcription,
                        hashtags=hashtags,
                        image_paths=image_paths_limited,  # 只使用1-3张
                        project_root=project_root,
                        total_frames=len(image_paths_all)  # 传递总数用于提示
                    )
                    
                    # 使用全局 session（复用连接），如遇连接错误尝试重建 session 一次
                    attempt_result = None
                    for session_attempt in range(2):
                        try:
                            attempt_result = await classifier._send_classification_request(
                                prompt=prompt,
                                images_base64=images_base64,
                                session=global_session
                            )
                            break
                        except Exception as request_error:
                            error_message = str(request_error)
                            if session_attempt == 0 and "API connection failed" in error_message:
                                # 重新创建 session
                                async with session_lock:
                                    await global_session.close()
                                    connector = aiohttp.TCPConnector(limit=max_concurrent * 2, limit_per_host=max_concurrent)
                                    timeout = aiohttp.ClientTimeout(total=600, connect=30)
                                    global_session = aiohttp.ClientSession(connector=connector, timeout=timeout)
                                await asyncio.sleep(1)
                                continue
                            raise
                    if attempt_result is None:
                        raise Exception("Failed to obtain classification result")
                    result = attempt_result
                    
                    # 更新 DataFrame
                    df.at[idx, classification_column] = result["is_flood_related"]
                    df.at[idx, confidence_column] = result["confidence"]
                    df.at[idx, reason_column] = result["reason"]
                    
                    # 线程安全地更新计数
                    async with processed_count:
                        processed_num[0] += 1
                        current_count = processed_num[0]
                    
                    # 只打印结果和进度
                    status = "✅ RELATED" if result["is_flood_related"] else "❌ NOT RELATED"
                    print(f"[{current_count}/{len(tasks)}] Row {row_num}: {status} (confidence: {result['confidence'].upper()})")
                    
                    # 每处理5个任务保存一次
                    if current_count % 5 == 0:
                        df.to_csv(output_csv_path, index=False)
                        print(f"💾 Progress saved: {current_count}/{len(tasks)} processed")
                    
                except Exception as e:
                    async with processed_count:
                        error_count[0] += 1
                        processed_num[0] += 1
                        current_count = processed_num[0]
                    
                    # 不写入错误信息到 CSV，保留为空，让用户可以稍后重试
                    # 这样 resume 模式会自动重试这些失败的行
                    error_msg = str(e)[:100]
                    print(f"❌ [{current_count}/{len(tasks)}] Row {row_num}: Failed after retries - {error_msg}")
                    # 保留为 None，不写入 CSV，这样 resume 时会自动重试
        
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
        print(f"   ❌ Failed (will retry on resume): {error_count[0]}")
        
        if classification_column in df.columns:
            related_count = df[classification_column].sum() if df[classification_column].dtype == bool else df[classification_column].eq(True).sum()
            print(f"   🌊 Flood-related posts: {related_count}")
        
        if error_count[0] > 0:
            print(f"\n   💡 Tip: Re-run the script to retry {error_count[0]} failed rows")
        
        print(f"   Output saved to: {output_csv_path}")
        print("=" * 70)
    
    finally:
        # 关闭全局 session
        await global_session.close()


def process_csv(
    csv_path: str,
    output_csv_path: Optional[str] = None,
    model: str = "qwen3-vl:30b-a3b-instruct-q4_K_M",
    base_url: str = "http://127.0.0.1:11434",
    start_idx: int = 0,
    max_rows: Optional[int] = None,
    resume: bool = True,
    max_concurrent: int = 3
):
    """
    同步包装函数，调用异步版本
    """
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
        description="使用 Ollama VLM 对 TikTok 数据进行洪水相关性标注",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 处理整个 CSV 文件
  python classify_flood_relevance.py tiktok/assam_flood/csvs/filtered_assam_flood_posts_20240501_20241120_with_local_paths.csv
  
  # 指定输出文件
  python classify_flood_relevance.py input.csv -o output.csv
  
  # 从第10行开始处理，最多处理20行
  python classify_flood_relevance.py input.csv --start-idx 10 --max-rows 20
  
  # 不使用断点续传（重新处理所有行）
  python classify_flood_relevance.py input.csv --no-resume
  
  # 自定义并发数（加速处理）
  python classify_flood_relevance.py input.csv --max-concurrent 5
        """
    )
    
    parser.add_argument(
        "csv_path",
        help="CSV 文件路径"
    )
    parser.add_argument(
        "-o", "--output",
        help="输出 CSV 文件路径（默认覆盖原文件）"
    )
    parser.add_argument(
        "--model",
        default="qwen3-vl:30b-a3b-instruct-q4_K_M",
        help="Ollama 模型名称"
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:11434",
        help="Ollama API 基础 URL"
    )
    parser.add_argument(
        "--start-idx",
        type=int,
        default=0,
        help="开始处理的索引（默认: 0）"
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        help="最大处理行数（默认: 处理所有行）"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="不使用断点续传（重新处理所有行）"
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="最大并发请求数（默认: 3，可根据服务器性能调整）"
    )
    
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
    
    print("\n🎉 Classification completed!")


if __name__ == "__main__":
    main()

