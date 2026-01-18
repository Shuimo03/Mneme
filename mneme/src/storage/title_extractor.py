"""Title extraction utilities."""

import re


def extract_title(markdown: str, default: str) -> str:
    """从 markdown 中提取标题，或使用默认 slug。

    Args:
        markdown: markdown 内容
        default: 默认标题（通常是 URL slug）

    Returns:
        提取或生成的标题
    """
    if not markdown:
        return default.replace("-", " ").title()

    # 跳过图片链接、空白行等非标题行
    lines = markdown.strip().split("\n")
    for i, line in enumerate(lines):
        line = line.strip()
        # 只处理 # 开头的标题行
        if line.startswith("# "):
            title_content = line[2:].strip()
            # 跳过以 [ 开头的内容（通常是网站品牌 Logo 链接）
            if title_content.startswith("["):
                continue
            # 清理标题，移除特殊字符
            title = re.sub(r"[<>:\"/\\|?']", " ", title_content)
            # 多个空格合并为一个
            title = re.sub(r"\s+", " ", title).strip()
            return title

    # 如果没有找到合适的 # 标题，返回 slug 转换后的标题
    return default.replace("-", " ").title()
