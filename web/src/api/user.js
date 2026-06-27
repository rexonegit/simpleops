import request from "@/utils/request";
import { tokenName } from "@/config";

export async function login(data) {
  return request({
    url: "/auth/login/",
    method: "post",
    data,
  });
}

export function getUserInfo(accessToken) {
  return request({
    url: "/auth/userInfo/",
    method: "get",
    data: {
      // [tokenName]: accessToken,
    },
  });
}

export function logout() {
  return request({
    url: "/auth/logout/",
    method: "post",
  });
}

export function updateUserInfo(data) {
  return request({
    url: "/auth/update/info/",
    method: "post",
    data,
  });
}

export function updateUserPassword(data) {
  return request({
    url: "/auth/update/password/",
    method: "post",
    data,
  });
}

export function uploadAvatar(data) {
  return request({
    url: "/auth/upload/avatar/",
    method: "post",
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
}
