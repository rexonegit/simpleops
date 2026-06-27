// src/api/aliyun/ramuser.js
import request from '@/utils/request'

// 获取RAM用户列表
export function listRAMUsers(params) {
  return request({
    url: '/ram/',
    method: 'get',
    params
  })
}

// 获取RAM用户详情
export function getRAMUserDetail(userId) {
  return request({
    url: `/ram/${userId}/`,
    method: 'get'
  })
}

// 同步RAM用户数据
export function syncRAMUsers() {
  return request({
    url: '/ram/sync/',
    method: 'post'
  })
}

// 导出RAM用户数据
export function exportRAMUsers(params) {
  return request({
    url: '/ram/export/',
    method: 'get',
    params,
    responseType: 'blob'  // 重要：指定响应类型为 blob
  })
}
