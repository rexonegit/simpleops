// src/api/aliyun/snat.js
import request from '@/utils/request'

// 获取 SNAT 条目列表
export function listSNATEntries(params) {
  return request({
    url: '/snat/',
    method: 'get',
    params
  })
}

// 获取单个 SNAT 条目详情
export function getSNATEntryDetail(id) {
  return request({
    url: `/snat/${id}/`,
    method: 'get'
  })
}

// 同步 SNAT 数据
export function syncSNATEntries() {
  return request({
    url: '/snat/sync/',
    method: 'post'
  })
}

// 导出 SNAT 数据
export function exportSNATEntries(params) {
  return request({
    url: '/snat/export/',
    method: 'get',
    params,
    responseType: 'blob'
  })
}
