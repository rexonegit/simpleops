# apps/utils/formatdatetime.py
import pytz
import json
from datetime import datetime, date
from django.core.serializers.json import DjangoJSONEncoder

SHANGHAI_TZ = pytz.timezone('Asia/Shanghai')



def formatdatetime(datatimes):
    """
    格式化日期时间为指定格式
    :param datatimes: 数据库中存储的datetime日期时间,也可以是字符串形式(2021-09-23 11:22:03.1232000)
    :return: 格式化后的日期时间如：2021-09-23 11:22:03
    """
    if datatimes:
        try:
            if isinstance(datatimes, str):
                if "." in datatimes:
                    arrays = datatimes.split(".", maxsplit=1)
                    if arrays:
                        return arrays[0]
            return datatimes.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            return datatimes
    return datatimes


def format_size(size_bytes):
    if not size_bytes:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024:
            return f"{size:.2f} {unit}".strip()
        size /= 1024
    return f"{size:.2f} {units[-1]}"


# 关键：自定义 JSON Encoder 支持 datetime
class ExtendedJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        return super().default(obj)