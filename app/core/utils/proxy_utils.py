"""代理配置工具模块

统一管理应用的网络代理设置，通过环境变量控制所有网络请求。
"""

import os
from typing import Optional
from ..utils.logger import setup_logger

logger = setup_logger("proxy_utils")


def get_proxy_url() -> Optional[str]:
    """获取代理URL
    
    Returns:
        代理URL字符串，如果未启用代理则返回 None
    """
    # 延迟导入以避免循环依赖
    from app.common.config import cfg
    
    if not cfg.proxy_enabled.value:
        return None
    
    proxy_host = cfg.proxy_host.value.strip()
    if not proxy_host:
        return None
    
    proxy_type = cfg.proxy_type.value.lower()
    # 端口现在是字符串类型，需要转换为整数
    try:
        proxy_port = int(cfg.proxy_port.value)
    except (ValueError, TypeError):
        proxy_port = 7890  # 默认端口
    
    proxy_username = cfg.proxy_username.value.strip()
    proxy_password = cfg.proxy_password.value.strip()
    
    # 构建代理URL
    if proxy_username and proxy_password:
        proxy_url = f"{proxy_type}://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"
    else:
        proxy_url = f"{proxy_type}://{proxy_host}:{proxy_port}"
    
    return proxy_url


def apply_proxy_to_env():
    """将代理配置应用到环境变量
    
    这是推荐的方式，会影响所有使用标准网络库的代码：
    - requests
    - urllib
    - httpx (如果没有显式设置proxies参数)
    - openai库
    - 其他基于这些库的第三方库
    """
    proxy_url = get_proxy_url()
    
    if proxy_url:
        # 设置标准代理环境变量
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["http_proxy"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url
        os.environ["https_proxy"] = proxy_url
        logger.info(f"代理已设置到环境变量: {proxy_url}")
    else:
        # 清除代理环境变量
        for key in ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"]:
            if key in os.environ:
                del os.environ[key]
        logger.info("代理环境变量已清除")


def init_proxy():
    """初始化代理设置
    
    应该在应用启动时调用一次，之后所有网络请求都会自动使用代理
    """
    apply_proxy_to_env()


def update_proxy():
    """更新代理设置
    
    当用户在设置界面修改代理配置后调用
    """
    apply_proxy_to_env()
    # 重置LLM客户端以使用新的代理设置
    from ..llm.client import reset_llm_client
    reset_llm_client()
