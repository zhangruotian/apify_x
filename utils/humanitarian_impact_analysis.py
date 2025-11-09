#!/usr/bin/env python3
"""
使用 Ollama Qwen VLM 模型对 TikTok/Twitter 数据进行人道主义影响分析
Humanitarian Impact Analysis for Flood-Related Social Media Posts
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
import random


class HumanitarianImpactAnalyzer:
    """使用 Ollama VLM 进行人道主义影响分析"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "qwen3-vl:32b-instruct"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self._image_cache = {}
        self._cache_max_size = 1000
        
        # 系统提示词
        self.system_prompt = """You are a conservative, evidence-driven humanitarian VLM for analyzing flood-related social media posts.

STRICT RULES
- Use TITLE TEXT and IMAGES (key frames).
- A label that requires visual cues may be TRUE only if the images clearly show those cues. Do NOT guess from common sense.
- HARD EVIDENCE POLICY (visual cues required unless noted):
  * infrastructure_access/damage_signs: flooded roads/bridges/houses, blocked vehicles, closed school/clinic signs, etc. Text alone is insufficient.
  * water_food_insecurity: do NOT infer from common sense; only mark loss_types.water_food_insecurity=true if images show distribution/containers/queues OR explicit on-image text that proves shortage. Plain caption is insufficient.
  * education_disruption: school building + closure cues (signs, closed gate, students turned away). Text alone insufficient.
  * displacement: shelters, group sleeping on floors, evacuation boats with belongings. Text alone insufficient.
  * caregiving_burden: visible caregiving actions (carrying child/elderly, wheelchair assistance). Text alone insufficient.
  * psychosocial_distress: do NOT infer from faces; set false unless text explicitly states psychological suffering AND images support the context.
  * urgency_score_0_5 > 0 only when visual danger cues exist (deep water around people/houses, blocked roads, structural damage, active rescue).
- PRIVACY: no identity inference. Demographics are visibility flags only (true only if clearly visible in images).

SCORING
- Precision over recall: false positives are worse than false negatives.
- If uncertain, set present=false (confidence<=0.4).

OUTPUT
- Return STRICT JSON ONLY, exactly matching the schema in the user message. No extra keys, no prose.
- Keep "evidence" concise (≤ 200 characters)."""
        
    def _compress_image(self, image_path: Path, max_short_side: int = 512, quality: int = 85) -> bytes:
        """压缩图片：短边≤512，JPEG quality=85，optimize=True"""
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
            print(f"⚠️  Image compression failed for {image_path}: {e}, using original")
            with open(image_path, "rb") as f:
                return f.read()
    
    def encode_image(self, image_path: str, use_cache: bool = True) -> str:
        """将图像文件编码为 base64（带压缩和缓存）"""
        image_path_str = str(image_path)
        image_path = Path(image_path)
        
        if use_cache and image_path_str in self._image_cache:
            return self._image_cache[image_path_str]
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        image_data = self._compress_image(image_path)
        # 返回纯 base64（Ollama 0.12.x 期望 raw base64，而不是 data URI）
        encoded = base64.b64encode(image_data).decode('utf-8')
        
        if use_cache:
            if len(self._image_cache) >= self._cache_max_size:
                oldest_key = next(iter(self._image_cache))
                del self._image_cache[oldest_key]
            self._image_cache[image_path_str] = encoded
        
        return encoded
    
    def _build_prompt_tiktok(
        self,
        title: str,
        hashtags: str,
        transcription: str,
        image_paths: List[str],
        project_root: Optional[Path] = None
    ) -> Tuple[str, List[str]]:
        """构建 TikTok 数据的 prompt"""
        # 准备文本内容
        title_text = ""
        if title and str(title).strip() and str(title).strip().lower() != 'nan':
            title_text = str(title).strip()
        
        # 合并 hashtags 到文本中
        post_text_concat = title_text
        if hashtags and str(hashtags).strip() and str(hashtags).strip().lower() != 'nan':
            hashtags_text = str(hashtags).strip()
            if post_text_concat:
                post_text_concat += f" #{hashtags_text.replace(',', ' #')}"
            else:
                post_text_concat = f"#{hashtags_text.replace(',', ' #')}"
        
        # 加载图像（使用全部3张，如果可用）
        images_base64 = []
        for img_path in image_paths[:3]:  # 限制最多3张
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
        
        if not images_base64 and not post_text_concat:
            raise ValueError("No images or text available")
        
        # 构建用户提示词
        user_prompt = f"""Task: Visual-first extraction of NON-ECONOMIC flood impact signals for ONE post.

Apply the HARD EVIDENCE policy. Use ONLY TITLE/TEXT and the attached IMAGES (key frames). 

Demography flags must come from IMAGES ONLY. If the group is not clearly visible, set the flag to false.

POST CONTEXT

TITLE:
<<<{title_text if title_text else 'N/A'}>>>

TEXT (caption/hashtags/OCR merged):
<<<{post_text_concat if post_text_concat else 'N/A'}>>>

{len(images_base64)} image(s) attached via the API call.

Return EXACTLY this JSON (and nothing else):
{{
  "loss_types": {{
    "displacement":              {{"present": false, "confidence": 0.0}},
    "education_disruption":      {{"present": false, "confidence": 0.0}},
    "health_trauma":             {{"present": false, "confidence": 0.0}},
    "social_ties_loss":          {{"present": false, "confidence": 0.0}},
    "cultural_ritual_disruption":{{"present": false, "confidence": 0.0}},
    "caregiving_burden":         {{"present": false, "confidence": 0.0}},
    "water_food_insecurity":     {{"present": false, "confidence": 0.0}},
    "infrastructure_access":     {{"present": false, "confidence": 0.0}},
    "psychosocial_distress":     {{"present": false, "confidence": 0.0}}
  }},
  "urgency_score_0_5": 0,
  "visual_cues": {{
    "water_depth_bin": "unknown",
    "crowd_size_bin": "unknown",
    "relief_visible": false,
    "relief_actor_type": "none",
    "damage_signs": ["none"]
  }},
  "demography_presence": {{
    "children": false,
    "elderly": false,
    "pregnant": false,
    "disabled_aid": false,
    "male": false,
    "female": false
  }},
  "scene_type": {{
    "aerial": false,
    "ground_outdoor": false,
    "indoor": false
  }},
  "context_area": ["unknown"],
  "sentiment": [
    {{"label":"fear","present":false,"confidence":0.0}},
    {{"label":"hopelessness","present":false,"confidence":0.0}},
    {{"label":"grief","present":false,"confidence":0.0}},
    {{"label":"anger","present":false,"confidence":0.0}},
    {{"label":"resilience","present":false,"confidence":0.0}},
    {{"label":"neutral","present":false,"confidence":0.0}},
    {{"label":"mixed","present":false,"confidence":0.0}}
  ],
  "recovery": {{
    "recovery_signals": false,
    "evidence": ""
  }}
}}

FIELD DEFINITIONS:
- water_depth_bin: one of {{"none","ankle","knee","waist","vehicle_height","indoor_flood","unknown"}}
- crowd_size_bin: one of {{"1","2-5","6-20",">20","unknown"}}
- relief_actor_type: one of {{"ngo","government","community","unknown","none"}}
- damage_signs: choose any of {{"road_blocked","house_inundated","bridge_damage","school_closed_sign","clinic_closed_sign","power_outage_sign","other","none"}}
- context_area: choose any subset of {{"settlement","farmland","roadway","riverbank","school_or_health_facility","mixed","unknown"}}
- confidence values: 0.0 to 1.0
- urgency_score_0_5: integer from 0 to 5"""
        
        return user_prompt, images_base64
    
    def _build_prompt_twitter(
        self,
        text: str,
        image_paths: List[str],
        project_root: Optional[Path] = None
    ) -> Tuple[str, List[str]]:
        """构建 Twitter 数据的 prompt"""
        # 准备文本内容
        tweet_text = ""
        if text and str(text).strip() and str(text).strip().lower() != 'nan':
            tweet_text = str(text).strip()
        
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
        
        if not images_base64 and not tweet_text:
            raise ValueError("No images or text available")
        
        # 构建用户提示词（Twitter 版本：无 transcription）
        user_prompt = f"""Task: Visual-first extraction of NON-ECONOMIC flood impact signals for ONE post.

Apply the HARD EVIDENCE policy. Use ONLY TITLE/TEXT and the attached IMAGES (key frames).

Demography flags must come from IMAGES ONLY. If the group is not clearly visible, set the flag to false.

POST CONTEXT

TEXT (tweet content):
<<<{tweet_text if tweet_text else 'N/A'}>>>

{len(images_base64)} image(s) attached via the API call.

Return EXACTLY this JSON (and nothing else):
{{
  "loss_types": {{
    "displacement":              {{"present": false, "confidence": 0.0}},
    "education_disruption":      {{"present": false, "confidence": 0.0}},
    "health_trauma":             {{"present": false, "confidence": 0.0}},
    "social_ties_loss":          {{"present": false, "confidence": 0.0}},
    "cultural_ritual_disruption":{{"present": false, "confidence": 0.0}},
    "caregiving_burden":         {{"present": false, "confidence": 0.0}},
    "water_food_insecurity":     {{"present": false, "confidence": 0.0}},
    "infrastructure_access":     {{"present": false, "confidence": 0.0}},
    "psychosocial_distress":     {{"present": false, "confidence": 0.0}}
  }},
  "urgency_score_0_5": 0,
  "visual_cues": {{
    "water_depth_bin": "unknown",
    "crowd_size_bin": "unknown",
    "relief_visible": false,
    "relief_actor_type": "none",
    "damage_signs": ["none"]
  }},
  "demography_presence": {{
    "children": false,
    "elderly": false,
    "pregnant": false,
    "disabled_aid": false,
    "male": false,
    "female": false
  }},
  "scene_type": {{
    "aerial": false,
    "ground_outdoor": false,
    "indoor": false
  }},
  "context_area": ["unknown"],
  "sentiment": [
    {{"label":"fear","present":false,"confidence":0.0}},
    {{"label":"hopelessness","present":false,"confidence":0.0}},
    {{"label":"grief","present":false,"confidence":0.0}},
    {{"label":"anger","present":false,"confidence":0.0}},
    {{"label":"resilience","present":false,"confidence":0.0}},
    {{"label":"neutral","present":false,"confidence":0.0}},
    {{"label":"mixed","present":false,"confidence":0.0}}
  ],
  "recovery": {{
    "recovery_signals": false,
    "evidence": ""
  }}
}}

FIELD DEFINITIONS:
- water_depth_bin: one of {{"none","ankle","knee","waist","vehicle_height","indoor_flood","unknown"}}
- crowd_size_bin: one of {{"1","2-5","6-20",">20","unknown"}}
- relief_actor_type: one of {{"ngo","government","community","unknown","none"}}
- damage_signs: choose any of {{"road_blocked","house_inundated","bridge_damage","school_closed_sign","clinic_closed_sign","power_outage_sign","other","none"}}
- context_area: choose any subset of {{"settlement","farmland","roadway","riverbank","school_or_health_facility","mixed","unknown"}}
- confidence values: 0.0 to 1.0
- urgency_score_0_5: integer from 0 to 5"""
        
        return user_prompt, images_base64
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """解析模型响应，提取 JSON"""
        # 尝试提取 JSON 对象
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)
                # 验证必要的字段
                if "loss_types" in parsed and "urgency_score_0_5" in parsed:
                    return parsed
            except json.JSONDecodeError:
                pass
        
        # 如果解析失败，返回默认结构
        print(f"⚠️  Failed to parse response, using default values. Response: {content[:200]}")
        return self._get_default_response()
    
    def _get_default_response(self) -> Dict[str, Any]:
        """返回默认的空响应结构"""
        return {
            "loss_types": {
                "displacement": {"present": False, "confidence": 0.0},
                "education_disruption": {"present": False, "confidence": 0.0},
                "health_trauma": {"present": False, "confidence": 0.0},
                "social_ties_loss": {"present": False, "confidence": 0.0},
                "cultural_ritual_disruption": {"present": False, "confidence": 0.0},
                "caregiving_burden": {"present": False, "confidence": 0.0},
                "water_food_insecurity": {"present": False, "confidence": 0.0},
                "infrastructure_access": {"present": False, "confidence": 0.0},
                "psychosocial_distress": {"present": False, "confidence": 0.0}
            },
            "urgency_score_0_5": 0,
            "visual_cues": {
                "water_depth_bin": "unknown",
                "crowd_size_bin": "unknown",
                "relief_visible": False,
                "relief_actor_type": "none",
                "damage_signs": ["none"]
            },
            "demography_presence": {
                "children": False,
                "elderly": False,
                "pregnant": False,
                "disabled_aid": False,
                "male": False,
                "female": False
            },
            "scene_type": {
                "aerial": False,
                "ground_outdoor": False,
                "indoor": False
            },
            "context_area": ["unknown"],
            "sentiment": [
                {"label": "fear", "present": False, "confidence": 0.0},
                {"label": "hopelessness", "present": False, "confidence": 0.0},
                {"label": "grief", "present": False, "confidence": 0.0},
                {"label": "anger", "present": False, "confidence": 0.0},
                {"label": "resilience", "present": False, "confidence": 0.0},
                {"label": "neutral", "present": False, "confidence": 0.0},
                {"label": "mixed", "present": False, "confidence": 0.0}
            ],
            "recovery": {
                "recovery_signals": False,
                "evidence": ""
            }
        }

    def _make_payload(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建 Ollama 请求 payload（复用配置避免重复代码）"""
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
        """预热模型，降低首个请求的启动延迟"""
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
    
    async def _send_analysis_request(
        self,
        user_prompt: str,
        images_base64: List[str],
        session: Optional[aiohttp.ClientSession] = None,
        max_retries: int = 5
    ) -> Dict[str, Any]:
        """发送分析请求（带重试机制）"""
        # 构建消息
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
                        
            except (aiohttp.ClientError, ConnectionError, BrokenPipeError, OSError, 
                    aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError) as e:
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


def flatten_analysis_results(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """将嵌套的分析结果展平为 DataFrame 列"""
    flat = {}
    
    # Loss types
    for loss_type, data in analysis["loss_types"].items():
        flat[f"loss_{loss_type}_present"] = data["present"]
        flat[f"loss_{loss_type}_confidence"] = data["confidence"]
    
    # Urgency score
    flat["urgency_score"] = analysis["urgency_score_0_5"]
    
    # Visual cues
    flat["water_depth_bin"] = analysis["visual_cues"]["water_depth_bin"]
    flat["crowd_size_bin"] = analysis["visual_cues"]["crowd_size_bin"]
    flat["relief_visible"] = analysis["visual_cues"]["relief_visible"]
    flat["relief_actor_type"] = analysis["visual_cues"]["relief_actor_type"]
    flat["damage_signs"] = json.dumps(analysis["visual_cues"]["damage_signs"])
    
    # Demography
    for demo, present in analysis["demography_presence"].items():
        flat[f"demo_{demo}"] = present
    
    # Scene type
    for scene_key, present in analysis["scene_type"].items():
        flat[f"scene_{scene_key}"] = present
    
    # Context area (store as JSON string)
    flat["context_area"] = json.dumps(analysis["context_area"])
    
    # Sentiment
    for sent_item in analysis["sentiment"]:
        label = sent_item["label"]
        flat[f"sentiment_{label}_present"] = sent_item["present"]
        flat[f"sentiment_{label}_confidence"] = sent_item["confidence"]
    
    # Recovery
    flat["recovery_signals"] = analysis["recovery"]["recovery_signals"]
    flat["recovery_evidence"] = analysis["recovery"]["evidence"]
    
    return flat


async def process_csv_async(
    csv_path: str,
    output_csv_path: Optional[str] = None,
    platform: str = "tiktok",  # "tiktok" or "twitter"
    model: str = "qwen3-vl:32b-instruct",
    base_url: str = "http://127.0.0.1:11434",
    start_idx: int = 0,
    max_rows: Optional[int] = None,
    resume: bool = True,
    max_concurrent: int = 2
):
    """
    异步处理 CSV 文件，添加人道主义影响分析
    """
    print(f"🌊 Starting Humanitarian Impact Analysis ({platform.upper()} Mode)")
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
    
    # 初始化分类器
    analyzer = HumanitarianImpactAnalyzer(base_url=base_url, model=model)
    
    # 获取所有需要添加的列名（使用默认响应结构）
    default_response = analyzer._get_default_response()
    flat_columns = flatten_analysis_results(default_response)
    
    # 添加新列（如果不存在）
    for col_name in flat_columns.keys():
        if col_name not in df.columns:
            df[col_name] = None
    
    # 添加标记列，表示该行是否已完成分析
    analysis_status_col = "humanitarian_analysis_complete"
    if analysis_status_col not in df.columns:
        df[analysis_status_col] = False
    
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
            if resume and pd.notna(row.get(analysis_status_col)) and row.get(analysis_status_col):
                continue
            
            # 根据平台提取数据
            if platform == "tiktok":
                title = row.get("title", "")
                hashtags = row.get("hashtags", "")
                transcription = row.get("transcription_english", "")
                
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
                
                if not image_paths and not title:
                    continue
                
                tasks.append((idx, "tiktok", title, hashtags, transcription, image_paths[:3]))
                
            elif platform == "twitter":
                text = row.get("text", "")
                
                # 解析 all_images
                all_images_str = row.get("all_images", "")
                image_paths = []
                
                if pd.notna(all_images_str) and str(all_images_str).strip():
                    try:
                        if isinstance(all_images_str, str):
                            image_paths = json.loads(all_images_str)
                        elif isinstance(all_images_str, list):
                            image_paths = all_images_str
                    except Exception:
                        pass
                
                if not image_paths and not text:
                    continue
                
                # 限制图片数量：最多3张
                if len(image_paths) > 3:
                    image_paths_limited = random.sample(image_paths, 3)
                else:
                    image_paths_limited = image_paths
                
                tasks.append((idx, "twitter", text, image_paths_limited))
        
        if not tasks:
            print("✅ All rows already processed or no tasks to process")
            return
        
        print(f"🚀 Processing {len(tasks)} tasks with {max_concurrent} concurrent requests...")
        print("=" * 70)
        
        # 预热模型，减少首次调用延迟
        try:
            print("🔥 Warming up model (one-time request)...")
            await analyzer.warm_up(global_session)
        except Exception as warm_err:
            print(f"⚠️  Warm-up skipped due to error: {warm_err}")
        
        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)
        processed_count = asyncio.Lock()
        processed_num = [0]
        error_count = [0]
        session_lock = asyncio.Lock()
        
        async def process_single_task(task_data):
            """处理单个任务"""
            nonlocal global_session
            
            if task_data[1] == "tiktok":
                idx, _, title, hashtags, transcription, image_paths = task_data
            else:  # twitter
                idx, _, text, image_paths = task_data
            
            row_num = idx + 1
            
            async with semaphore:
                try:
                    # 构建 prompt
                    if task_data[1] == "tiktok":
                        user_prompt, images_base64 = analyzer._build_prompt_tiktok(
                            title=title,
                            hashtags=hashtags,
                            transcription=transcription,
                            image_paths=image_paths,
                            project_root=project_root
                        )
                    else:  # twitter
                        user_prompt, images_base64 = analyzer._build_prompt_twitter(
                            text=text,
                            image_paths=image_paths,
                            project_root=project_root
                        )
                    
                    # 发送请求（带 session 重建机制）
                    attempt_result = None
                    for session_attempt in range(2):
                        try:
                            attempt_result = await analyzer._send_analysis_request(
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
                        raise Exception("Failed to obtain analysis result")
                    
                    # 展平结果并更新 DataFrame
                    flat_result = flatten_analysis_results(attempt_result)
                    for col_name, value in flat_result.items():
                        df.at[idx, col_name] = value
                    df.at[idx, analysis_status_col] = True
                    
                    # 更新计数
                    async with processed_count:
                        processed_num[0] += 1
                        current_count = processed_num[0]
                    
                    # 打印进度
                    urgency = flat_result.get("urgency_score", 0)
                    print(f"[{current_count}/{len(tasks)}] Row {row_num}: ✅ Analyzed (urgency: {urgency}/5)")
                    
                    # 每处理5个任务保存一次
                    if current_count % 5 == 0:
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
    platform: str = "tiktok",
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
        platform=platform,
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
        description="人道主义影响分析 - TikTok/Twitter 洪水相关帖子",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # TikTok 数据
  python humanitarian_impact_analysis.py tiktok/assam_flood/csvs/filtered_assam_flood_posts_20240501_20241120_with_local_paths.csv --platform tiktok
  
  # Twitter 数据
  python humanitarian_impact_analysis.py twitter/assam_flood/csvs/filtered_assam_flood_tweets_20240501_20240801_with_local_paths_20250721_172531.csv --platform twitter
  
  # 批量处理（使用 shell 脚本）
  for file in tiktok/*/csvs/*.csv; do
    python humanitarian_impact_analysis.py "$file" --platform tiktok
  done
        """
    )
    
    parser.add_argument("csv_path", help="CSV 文件路径")
    parser.add_argument("-o", "--output", help="输出 CSV 文件路径（默认覆盖原文件）")
    parser.add_argument("--platform", choices=["tiktok", "twitter"], required=True, help="平台类型")
    parser.add_argument("--model", default="qwen3-vl:32b", help="Ollama 模型名称")
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
        platform=args.platform,
        model=args.model,
        base_url=args.base_url,
        start_idx=args.start_idx,
        max_rows=args.max_rows,
        resume=not args.no_resume,
        max_concurrent=args.max_concurrent
    )
    
    print("\n🎉 Analysis completed!")


if __name__ == "__main__":
    main()

