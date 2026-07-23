#!/usr/bin/env python3
"""
金价分析报告保存工具
自动处理文件名冲突，避免覆盖已有文件
"""

import os
import sys
from pathlib import Path


def get_unique_filename(directory: str, base_name: str, extension: str = ".md") -> str:
    """
    生成唯一的文件名，避免覆盖已有文件

    Args:
        directory: 目标目录路径
        base_name: 基础文件名（不含扩展名）
        extension: 文件扩展名（默认 .md）

    Returns:
        唯一的完整文件路径

    Examples:
        如果 monitor-gold-risk-analysis-2026-01-28.md 已存在:
        - 第一次: monitor-gold-risk-analysis-2026-01-28(1).md
        - 第二次: monitor-gold-risk-analysis-2026-01-28(2).md
        - 以此类推...
    """
    # 确保目录存在
    Path(directory).mkdir(parents=True, exist_ok=True)

    # 构建初始文件路径
    file_path = os.path.join(directory, f"{base_name}{extension}")

    # 如果文件不存在，直接返回
    if not os.path.exists(file_path):
        return file_path

    # 如果文件存在，寻找可用的数字后缀
    counter = 1
    while True:
        new_file_path = os.path.join(directory, f"{base_name}({counter}){extension}")
        if not os.path.exists(new_file_path):
            return new_file_path
        counter += 1


def save_report(content: str, directory: str, base_name: str, extension: str = ".md") -> str:
    """
    保存报告内容到文件，自动处理文件名冲突

    Args:
        content: 报告内容
        directory: 目标目录路径
        base_name: 基础文件名（不含扩展名）
        extension: 文件扩展名（默认 .md）

    Returns:
        实际保存的文件路径
    """
    file_path = get_unique_filename(directory, base_name, extension)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return file_path


def main():
    """命令行接口"""
    if len(sys.argv) < 4:
        print("Usage: python save_report.py <directory> <base_name> <content_file>")
        print("Example: python save_report.py ./output/monitor-gold monitor-gold-risk-2026-01-28 report.txt")
        sys.exit(1)

    directory = sys.argv[1]
    base_name = sys.argv[2]
    content_file = sys.argv[3]

    # 读取内容
    with open(content_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 保存报告
    file_path = save_report(content, directory, base_name)
    print(f"Report saved to: {file_path}")


if __name__ == "__main__":
    main()
