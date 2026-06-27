"""
aliyun/aliyun_common.py
所有阿里云相关公共逻辑
"""
import os
import re
import logging
import configparser
from pathlib import Path
from alibabacloud_tea_openapi.models import Config as TeaConfig
from Tea.exceptions import TeaException
from alibabacloud_tea_openapi.exceptions import ClientException as OpenApiClientException
from datetime import datetime
import pytz
import time
from datetime import datetime, timezone, timedelta
from django.utils import timezone as django_timezone
import configparser
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)


# -------------------- 账号解析 --------------------
def get_aliyun_accounts():
    """
    全局统一的阿里云账号解析器
    从 app/conf/aliyun.cnf 文件读取配置
    """
    accounts = []

    try:
        # 构建配置文件路径
        # 根据您的 settings.py，BASE_DIR 是项目根目录
        # 假设 aliyun app 在项目根目录下
        config_path = Path(settings.BASE_DIR) / 'aliyun' / 'conf' / 'aliyun.cnf'

        logger.info(f"尝试读取配置文件: {config_path}")
        logger.info(f"配置文件是否存在: {config_path.exists()}")

        if not config_path.exists():
            logger.error(f"配置文件不存在: {config_path}")
            # 尝试其他可能路径
            alternative_paths = [
                Path(settings.BASE_DIR) / 'conf' / 'aliyun.cnf',
                Path(settings.BASE_DIR) / 'backend' / 'conf' / 'aliyun.cnf',
                Path('conf/aliyun.cnf'),
                Path('./conf/aliyun.cnf'),
            ]
            for alt_path in alternative_paths:
                if alt_path.exists():
                    config_path = alt_path
                    logger.info(f"使用备用配置文件路径: {config_path}")
                    break
            else:
                logger.error("未找到任何配置文件")
                return accounts

        # 读取配置文件
        config = configparser.ConfigParser()
        # 保留原始大小写
        config.optionxform = lambda option: option

        files_read = config.read(config_path, encoding='utf-8')
        logger.info(f"成功读取配置文件，sections: {config.sections()}")

        # 遍历所有 section
        for section in config.sections():
            logger.info(f"处理配置段: {section}")

            # 检查是否是阿里云账号配置
            if section.lower().startswith('aliyun'):
                try:
                    access_key = config.get(section, 'access_key', fallback='').strip()
                    access_secret = config.get(section, 'access_secret', fallback='').strip()
                    regions_str = config.get(section, 'regions', fallback='').strip()

                    logger.info(f"{section} - access_key: {'*' * 8}{access_key[-4:] if access_key else 'None'}")
                    logger.info(f"{section} - regions: {regions_str}")

                    # 处理 regions
                    regions = []
                    if regions_str:
                        regions = [r.strip().strip('"').strip("'") for r in regions_str.split(',') if r.strip()]

                    # 验证配置完整性
                    if not access_key:
                        logger.warning(f"{section} access_key 为空，跳过")
                        continue
                    if not access_secret:
                        logger.warning(f"{section} access_secret 为空，跳过")
                        continue
                    if not regions:
                        logger.warning(f"{section} regions 为空，跳过")
                        continue

                    account_info = {
                        'name': section,
                        'access_key': access_key,
                        'access_secret': access_secret,
                        'regions': regions
                    }

                    accounts.append(account_info)
                    logger.info(f"成功添加账号: {section}, regions: {regions}")

                except configparser.NoOptionError as e:
                    logger.error(f"配置段 {section} 缺少必要选项: {e}")
                    continue
                except Exception as e:
                    logger.error(f"解析 {section} 配置失败: {e}")
                    continue
            else:
                logger.info(f"跳过非阿里云配置段: {section}")

        logger.info(f"共解析到 {len(accounts)} 个阿里云账号配置")

    except Exception as e:
        logger.error(f"读取阿里云配置文件失败: {e}", exc_info=True)

    return accounts


# -------------------- SDK v2 通用 client 构建 --------------------
def make_tea_config(account: dict, region: str, product: str) -> TeaConfig:
    """
    生成 TeaConfig（SDK v2）
    product: ecs / slb / rds / vpc / oss / nas / waf-openapi ...
    """
    endpoint_map = {
        'ecs': f'ecs.{region}.aliyuncs.com',
        'slb': f'slb.{region}.aliyuncs.com',
        'rds': 'rds.aliyuncs.com',
        'vpc': f'vpc.{region}.aliyuncs.com',
        'oss': f'oss-{region}.aliyuncs.com',
        'nas': f'nas.{region}.aliyuncs.com',
        'waf-openapi': 'wafopenapi.cn-hangzhou.aliyuncs.com',
        'domain': 'domain.aliyuncs.com',
        'alidns': 'alidns.aliyuncs.com',
        'ram': 'ram.aliyuncs.com',
        'ims': 'ims.aliyuncs.com',
        'sls': f'{region}.log.aliyuncs.com',
    }


    endpoint = endpoint_map.get(product)
    if not endpoint:
        raise ValueError(f"未找到产品 {product} 的 endpoint 映射")

    logger.info(f"创建 TeaConfig: product={product}, region={region}, endpoint={endpoint}")

    return TeaConfig(
        access_key_id=account['access_key'],
        access_key_secret=account['access_secret'],
        endpoint=endpoint_map[product],
        region_id=region
    )


def safe_api_call(call_func, default=None, max_retries=3):
    """
    超级稳健的阿里云 API 调用封装
    - 自动重试（网络、超时、限流）
    - 自动跳过 401/403 权限不足
    - 自动跳过 404 资源不存在
    - 自动记录详细日志
    """
    for attempt in range(max_retries + 1):
        try:
            resp = call_func()

            # 新增：调试日志
            if resp and hasattr(resp, 'body'):
                logger.debug(f"API响应Body类型: {type(resp.body)}")
                # 可以打印关键字段检查
                if hasattr(resp.body, 'security_groups'):
                    sg_sample = resp.body.security_groups.security_group[0]
                    logger.debug(f"安全组样本字段: {vars(sg_sample)}")

            # ✅ Tea SDK 响应检查
            if resp and hasattr(resp, 'body') and resp.body is not None:
                return resp
            else:
                logger.debug("API 返回 body 为空，视为失败")
                return default

        except TeaException as e:
            error_code = getattr(e, 'code', '')
            error_msg = str(e).lower()
            request_id = getattr(e, 'request_id', 'N/A')

            # 401 认证失败：立即返回，不重试
            if '401' in error_msg or 'unauthorized' in error_msg:
                logger.error(f"❌ 认证失败 (401) [RequestId: {request_id}]，请检查 RAM 权限: {e}")
                logger.error("  需要权限: log:ListProject, log:ListLogStores, log:GetLogStore")
                return default

            # 403 权限不足：跳过
            if '403' in error_msg or error_code == 'NoPermission':
                logger.info(f"➡️ 权限不足 (403) [RequestId: {request_id}]，已跳过: {e}")
                return default

            # 404 资源不存在：跳过
            if '404' in error_msg or 'notfound' in error_msg:
                logger.debug(f"🔍 资源不存在 (404) [RequestId: {request_id}]，已跳过: {e}")
                return default

            # 429 限流：需要重试
            if '429' in error_msg or 'throttling' in error_msg:
                wait = min(2 ** attempt, 30)  # 最多等待30秒
                logger.warning(f"⚠️ 请求被限流 (429) [RequestId: {request_id}]，{wait}秒后第 {attempt + 1} 次重试")
                time.sleep(wait)
                continue

            # 其他可重试错误（网络超时、500等）
            if attempt < max_retries:
                wait = 2 ** attempt
                logger.warning(f"⚠️ API 调用失败 [RequestId: {request_id}]，{wait}秒后第 {attempt + 1} 次重试: {e}")
                time.sleep(wait)
                continue
            else:
                logger.error(f"❌ API 调用最终失败（已重试 {max_retries} 次）: {e}")
                return default

        except Exception as e:
            # 非 TeaException 异常
            if attempt < max_retries:
                wait = 2 ** attempt
                logger.warning(f"⚠️ 未知异常，{wait}秒后第 {attempt + 1} 次重试: {e}")
                time.sleep(wait)
                continue
            else:
                logger.error(f"💥 严重异常: {e}", exc_info=True)
                return default

    logger.warning(f"⚠️ 达到最大重试次数 {max_retries}，返回默认值")
    return default


def convert_utc_to_shanghai(utc_time_input):
    """
    统一时间转换函数，智能识别格式（完全保持你原来支持的所有格式）：
    - 毫秒时间戳: 1706249977000 → datetime
    - 秒时间戳: 1706249977 → datetime
    - ISO字符串: "2023-01-01T12:00:00Z" → datetime
    - 阿里云格式: "2023-01-01 12:00:00" → datetime
    """
    if not utc_time_input or str(utc_time_input).strip().upper() in ['N/A', 'NONE', '-', '']:
        return None

    time_str = str(utc_time_input).strip()

    try:
        # 1. 处理时间戳（毫秒或秒）—— 完全保留你原来的逻辑
        if time_str.isdigit():
            timestamp = float(time_str)
            if timestamp > 9999999999:  # 13位 = 毫秒
                timestamp /= 1000.0
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return dt.astimezone(pytz.timezone('Asia/Shanghai'))

        # 2. 处理字符串时间
        if isinstance(utc_time_input, str):
            # 情况A：阿里云常用格式 "2023-01-01 12:00:00"
            if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', time_str):
                dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                return pytz.timezone('Asia/Shanghai').localize(dt)

            # 情况B：标准 ISO 8601 格式 "2023-09-14T02:42:26Z" 或 "2025-12-21T16:00:00Z"
            # 这是你现在报错的主要来源，用纯原生方式解析
            if 'T' in time_str and time_str.endswith('Z'):
                # 去掉末尾的 Z，再按标准格式解析
                clean_time = time_str[:-1] if time_str.endswith('Z') else time_str
                # 支持带毫秒和不带毫秒两种
                for fmt in (
                    "%Y-%m-%dT%H:%M:%S.%f",  # 带毫秒：2023-09-14T02:42:26.123Z
                    "%Y-%m-%dT%H:%M:%S"      # 不带毫秒：2023-09-14T02:42:26Z
                ):
                    try:
                        dt = datetime.strptime(clean_time, fmt)
                        dt = dt.replace(tzinfo=timezone.utc)
                        return dt.astimezone(pytz.timezone('Asia/Shanghai'))
                    except ValueError:
                        continue

            # 情况C：其他带时区偏移的 ISO 格式，如 2023-09-14T02:42:26+08:00
            if '+' in time_str or ('-' in time_str and len(time_str) > 19):
                # 使用 pytz 直接处理时区偏移
                for sep in ['+', '-']:
                    if sep in time_str and time_str.count(':') >= 2:
                        try:
                            dt = datetime.fromisoformat(time_str.replace(sep, f' {sep}', 1))
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                            return dt.astimezone(pytz.timezone('Asia/Shanghai'))
                        except:
                            continue

        # 3. 已经是 datetime 对象
        if isinstance(utc_time_input, datetime):
            if utc_time_input.tzinfo is None:
                utc_time_input = utc_time_input.replace(tzinfo=timezone.utc)
            return utc_time_input.astimezone(pytz.timezone('Asia/Shanghai'))

    except Exception as e:
        logger.error(f"时间转换失败: {utc_time_input} | 类型: {type(utc_time_input)} | 错误: {e}")

    # 最终保底：如果所有方式都失败，尝试用最宽松的方式
    try:
        from dateutil import parser
        dt = parser.isoparse(str(utc_time_input))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(pytz.timezone('Asia/Shanghai'))
    except:
        pass

    return None


def format_size(size_bytes):
    """格式化字节大小为易读格式"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {size_names[i]}"