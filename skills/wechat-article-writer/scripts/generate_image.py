#!/usr/bin/env python3
"""
图片生成API调用脚本

支持多种图片生成API:
- Gemini Imagen API (Google)
- DALL-E API (OpenAI)

使用方法:
    python generate_image.py --prompt "图片描述" --api gemini --output output.png
    python generate_image.py --prompt "图片描述" --api dalle --output output.png
"""

import os
import sys
import argparse
import base64
import requests
from pathlib import Path
from typing import Optional, Dict, Any


class ImageGenerator:
    """图片生成器基类"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._get_api_key()

    def _get_api_key(self) -> str:
        """从环境变量获取API密钥"""
        raise NotImplementedError

    def _get_proxies(self, proxy: Optional[str] = None) -> Optional[Dict[str, str]]:
        """获取代理配置"""
        if proxy:
            return {
                'http': proxy,
                'https': proxy
            }

        http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')

        if http_proxy or https_proxy:
            return {
                'http': http_proxy or https_proxy,
                'https': https_proxy or http_proxy
            }

        return None

    def generate(self, prompt: str, output_path: str, **kwargs) -> str:
        """生成图片并保存"""
        raise NotImplementedError


class GeminiImageGenerator(ImageGenerator):
    """Gemini Imagen API图片生成器"""

    def _get_api_key(self) -> str:
        api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("请设置环境变量 GEMINI_API_KEY 或 GOOGLE_API_KEY")
        return api_key

    def generate(self, prompt: str, output_path: str, **kwargs) -> str:
        try:
            from google import genai
        except ImportError:
            raise ImportError("请先安装 google-genai SDK: pip install google-genai")

        try:
            client = genai.Client(api_key=self.api_key)
            model = kwargs.get("model", "gemini-3-pro-image-preview")

            response = client.models.generate_content(
                model=model,
                contents=[prompt],
            )

            for part in response.parts:
                if part.inline_data is not None:
                    image = part.as_image()
                    image.save(output_path)
                    return output_path

            raise ValueError("API 响应中未找到图片数据")

        except Exception as e:
            raise RuntimeError(f"Gemini API调用失败: {str(e)}")


class DALLEImageGenerator(ImageGenerator):
    """DALL-E API图片生成器 (OpenAI)"""

    def _get_api_key(self) -> str:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("请设置环境变量 OPENAI_API_KEY")
        return api_key

    def generate(self, prompt: str, output_path: str, **kwargs) -> str:
        url = "https://api.openai.com/v1/images/generations"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": kwargs.get("model", "dall-e-3"),
            "prompt": prompt,
            "n": 1,
            "size": kwargs.get("size", "1792x1024"),
            "quality": kwargs.get("quality", "standard"),
            "response_format": "b64_json"
        }

        proxies = self._get_proxies(kwargs.get("proxy"))

        try:
            response = requests.post(url, json=data, headers=headers, proxies=proxies, timeout=120)
            response.raise_for_status()

            result = response.json()

            if "data" in result and len(result["data"]) > 0:
                image_data = result["data"][0].get("b64_json")
                if image_data:
                    image_bytes = base64.b64decode(image_data)
                    with open(output_path, 'wb') as f:
                        f.write(image_bytes)
                    return output_path

            raise ValueError(f"API返回数据格式异常: {result}")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"DALL-E API调用失败: {str(e)}")


API_GENERATORS = {
    "gemini": GeminiImageGenerator,
    "imagen": GeminiImageGenerator,
    "dalle": DALLEImageGenerator,
    "openai": DALLEImageGenerator,
}


def main():
    parser = argparse.ArgumentParser(
        description="调用生图API生成图片",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--prompt", required=True, help="图片生成提示词")
    parser.add_argument("--api", choices=list(API_GENERATORS.keys()), default="gemini", help="使用的API (默认: gemini)")
    parser.add_argument("--output", required=True, help="输出图片路径")
    parser.add_argument("--aspect-ratio", default="16:9", help="图片宽高比 (默认: 16:9)")
    parser.add_argument("--size", help="图片尺寸 (DALL-E专用, 如: 1792x1024)")
    parser.add_argument("--quality", choices=["standard", "hd"], default="standard", help="图片质量 (DALL-E专用)")
    parser.add_argument("--proxy", help="代理地址 (如: http://127.0.0.1:7890)")

    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generator_class = API_GENERATORS[args.api]

    try:
        generator = generator_class()

        kwargs = {"aspect_ratio": args.aspect_ratio}

        if args.proxy:
            kwargs["proxy"] = args.proxy

        if args.api in ["dalle", "openai"]:
            if args.size:
                kwargs["size"] = args.size
            kwargs["quality"] = args.quality

        print(f"🎨 使用 {args.api.upper()} API生成图片...")
        print(f"📝 提示词: {args.prompt}")

        result_path = generator.generate(
            prompt=args.prompt,
            output_path=str(output_path),
            **kwargs
        )

        print(f"✅ 图片已生成: {result_path}")
        return 0

    except Exception as e:
        print(f"❌ 生成失败: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
