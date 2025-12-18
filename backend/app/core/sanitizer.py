"""
输入清理（Sanitization）工具模块。

本模块提供各种输入清理函数，用于防止安全漏洞：
1. XSS（跨站脚本攻击）防护
2. 注入攻击防护
3. 路径遍历攻击防护
4. 恶意数据过滤

安全原则：
- 永远不要信任用户输入
- 在存储前清理数据
- 在显示前转义数据
- 使用白名单而非黑名单

XSS 攻击示例：
用户输入: <script>alert('XSS')</script>
清理后: &lt;script&gt;alert('XSS')&lt;/script&gt;

路径遍历攻击示例：
用户输入: ../../../etc/passwd
清理后: etc/passwd（移除路径分隔符）

使用建议：
- 所有用户输入都应该经过清理
- 不同类型的数据使用对应的清理函数
- 清理函数应该在数据进入系统时立即调用
"""

import html
import re
from typing import Optional


# ============================================================================
# 基础清理函数
# ============================================================================

def sanitize_html(text: str) -> str:
    """
    对 HTML 内容进行转义处理，防止 XSS 攻击。
    
    将 HTML 特殊字符转换为安全的 HTML 实体：
    - < → &lt;
    - > → &gt;
    - & → &amp;
    - " → &quot;
    - ' → &#x27;
    
    这样即使用户输入包含 HTML/JavaScript 代码，
    在浏览器中也只会显示为纯文本，不会被执行。
    
    Args:
        text: 需要清理的输入文本
        
    Returns:
        str: 转义后的安全文本
        
    Example:
        sanitize_html("<script>alert('XSS')</script>")
        # 返回: "&lt;script&gt;alert('XSS')&lt;/script&gt;"
    """
    return html.escape(text)


def sanitize_for_db(text: str) -> str:
    """
    清理文本以便安全存储到数据库。
    
    移除可能导致问题的控制字符，但保留：
    - 换行符 (\\n, 0x0a)
    - 回车符 (\\r, 0x0d)
    - 制表符 (\\t, 0x09)
    
    控制字符可能导致：
    - 日志注入攻击
    - 终端控制序列执行
    - 数据库查询问题
    
    Args:
        text: 需要清理的输入文本
        
    Returns:
        str: 清理后的安全文本
        
    正则表达式说明：
    - \\x00-\\x08: 移除 NUL 到 BS（退格前的控制符）
    - \\x0b: 移除垂直制表符
    - \\x0c: 移除换页符
    - \\x0e-\\x1f: 移除 SO 到 US（其他控制符）
    - \\x7f: 移除 DEL 控制符
    """
    # 使用正则表达式移除危险的控制字符
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return sanitized


# ============================================================================
# 特定类型数据清理函数
# ============================================================================

def sanitize_filename(filename: str) -> str:
    """
    清理文件名，防止路径遍历攻击和文件系统问题。
    
    路径遍历攻击示例：
    - "../../../etc/passwd" - 访问系统文件
    - "C:\\Windows\\System32" - 访问系统目录
    
    清理策略：
    1. 移除路径分隔符（/ 和 \\）
    2. 移除危险字符（<>:"|?*）
    3. 移除控制字符
    4. 移除首尾的点和空格
    5. 限制文件名长度
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的安全文件名
        
    Example:
        sanitize_filename("../../../etc/passwd")
        # 返回: "etcpasswd"
        
        sanitize_filename("report.pdf")
        # 返回: "report.pdf"（无变化）
    """
    # 移除路径分隔符和危险字符
    # 这些字符在 Windows 或 Unix 系统中有特殊含义
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
    
    # 移除首尾的点和空格
    # 以点开头的文件在 Unix 中是隐藏文件
    # 首尾空格可能导致意外行为
    sanitized = sanitized.strip('. ')
    
    # 限制文件名长度（大多数文件系统限制为 255 字符）
    if len(sanitized) > 255:
        # 尝试保留文件扩展名
        if '.' in sanitized:
            name, ext = sanitized.rsplit('.', 1)
            max_name_len = 255 - len(ext) - 1
            sanitized = f"{name[:max_name_len]}.{ext}"
        else:
            sanitized = sanitized[:255]
    
    # 如果清理后为空，返回默认名称
    return sanitized or 'unnamed'


def sanitize_conversation_title(title: str) -> str:
    """
    清理对话标题。
    
    对话标题会显示在 UI 中，需要：
    1. 防止 XSS 攻击
    2. 移除控制字符
    3. 限制长度（避免 UI 溢出）
    
    Args:
        title: 对话标题
        
    Returns:
        str: 清理后的标题，如果为空则返回"新对话"
        
    长度限制说明：
    - 最大 200 字符
    - 超出时截断并添加省略号
    """
    # 首先进行 HTML 转义
    sanitized = sanitize_html(title)
    # 移除控制字符
    sanitized = sanitize_for_db(sanitized)
    
    # 限制长度
    if len(sanitized) > 200:
        sanitized = sanitized[:197] + '...'
    
    # 去除首尾空白，如果为空则返回默认值
    return sanitized.strip() or '新对话'


def sanitize_chat_content(content: str) -> str:
    """
    清理聊天消息内容。
    
    聊天内容需要特殊处理：
    - 保留 Markdown 格式（用户可能使用代码块、列表等）
    - 不转义 HTML（前端使用 react-markdown 安全渲染）
    - 只移除控制字符
    
    安全依赖：
    前端必须使用安全的 Markdown 渲染器（如 react-markdown）
    来防止 XSS 攻击。后端只做基本清理。
    
    Args:
        content: 聊天消息内容
        
    Returns:
        str: 清理后的内容
        
    Note:
        此函数有意不转义 HTML，因为：
        1. 用户可能需要在代码块中展示 HTML
        2. 前端使用 react-markdown 安全渲染
        3. Markdown 语法依赖某些特殊字符
    """
    # 只移除控制字符，保留 Markdown 格式
    sanitized = sanitize_for_db(content)
    return sanitized


def sanitize_email(email: str) -> Optional[str]:
    """
    验证并清理电子邮件地址。
    
    验证规则：
    - 必须包含 @ 符号
    - 本地部分只允许：字母、数字、._%+-
    - 域名部分只允许：字母、数字、.-
    - 顶级域名至少 2 个字符
    
    Args:
        email: 电子邮件地址
        
    Returns:
        Optional[str]: 清理后的小写邮箱地址，无效则返回 None
        
    Example:
        sanitize_email("User@Example.COM")
        # 返回: "user@example.com"
        
        sanitize_email("not-an-email")
        # 返回: None
        
    安全说明：
    - 统一转换为小写，避免大小写绕过
    - 使用正则表达式验证格式
    - 返回 None 而非抛出异常，便于调用者处理
    """
    # 去除首尾空白并转换为小写
    email = email.strip().lower()
    
    # 使用正则表达式验证邮箱格式
    # 这是一个简化的正则，覆盖大多数常见邮箱格式
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(email_pattern, email):
        return email
    return None


def sanitize_username(username: str) -> str:
    """
    清理用户名。
    
    用户名会显示在 UI 中的多个位置，需要：
    1. 防止 XSS 攻击
    2. 移除控制字符
    3. 限制长度
    
    Args:
        username: 用户名
        
    Returns:
        str: 清理后的用户名，如果为空则返回"User"
        
    长度限制说明：
    - 最大 50 字符
    - 超出时直接截断（不添加省略号）
    """
    # HTML 转义，防止 XSS
    sanitized = sanitize_html(username)
    # 移除控制字符
    sanitized = sanitize_for_db(sanitized)
    # 去除首尾空白
    sanitized = sanitized.strip()
    
    # 限制长度
    if len(sanitized) > 50:
        sanitized = sanitized[:50]
    
    # 如果为空则返回默认值
    return sanitized or 'User'