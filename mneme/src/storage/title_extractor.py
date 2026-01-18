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

    # 匹配第一行 # 开头的内容
    lines = markdown.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("# "):
            # 清理标题，移除特殊字符
            title = line[2:].strip()
            # 替换不合法字符为空格
            title = re.sub(r'[<>:"/\\|?]', " ", title)
            # 多个空格合并为一个
            title = re.sub(r"\s+", " ", title).strip()
            return title

    return default.replace("-", " ").title()
