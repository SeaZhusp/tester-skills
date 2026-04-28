#!/usr/bin/env python3
"""
读取PDF需求文档，提取文本内容
"""

import json
import sys
import argparse
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF not installed. Run: pip install pymupdf")
    sys.exit(1)


def read_pdf(file_path: str) -> dict:
    """
    读取PDF文档

    Args:
        file_path: PDF文件路径

    Returns:
        包含文档内容的字典
    """
    doc = fitz.open(file_path)

    pages = []
    full_text = []

    for page_num, page in enumerate(doc):
        text = page.get_text()
        pages.append({
            'page': page_num + 1,
            'text': text.strip()
        })
        if text.strip():
            full_text.append(f"[Page {page_num + 1}]\n{text.strip()}")

    # 提取目录（如果有）
    toc = []
    try:
        toc = doc.get_toc()
    except:
        pass

    return {
        'page_count': len(doc),
        'pages': pages,
        'toc': toc,
        'full_text': '\n\n'.join(full_text)
    }


def main():
    parser = argparse.ArgumentParser(description='读取PDF需求文档')
    parser.add_argument('file_path', help='PDF文件路径')
    parser.add_argument('-o', '--output', help='输出JSON文件路径')
    parser.add_argument('--text-only', action='store_true', help='只输出纯文本')

    args = parser.parse_args()

    if not Path(args.file_path).exists():
        print(f"Error: File not found: {args.file_path}")
        sys.exit(1)

    result = read_pdf(args.file_path)

    if args.text_only:
        print(result['full_text'])
    elif args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Output written to: {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
