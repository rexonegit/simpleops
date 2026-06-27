from rest_framework.response import Response
from rest_framework import status


class ApiResponse:
    def __init__(self, code=200, msg="成功", data=None):
        self.code = code
        self.msg = msg
        self.data = data

    def json(self):
        return {
            "code": self.code,
            "msg": self.msg,
            "data": self.data or {}
        }

    @staticmethod
    def success(data=None, msg="操作成功"):
        return Response(ApiResponse(200, msg, data).json(), status=status.HTTP_200_OK)

    @staticmethod
    def error(msg="操作失败", code=500):
        return Response(ApiResponse(code, msg).json(), status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def unauthorized(msg="请先登录"):
        return Response(ApiResponse(402, msg).json(), status=status.HTTP_401_UNAUTHORIZED)

    @staticmethod
    def login_error(msg="用户名或密码错误"):
        return Response(ApiResponse(401, msg).json(), status=status.HTTP_401_UNAUTHORIZED)