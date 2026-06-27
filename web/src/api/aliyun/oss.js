// src/api/aliyun/oss.js
import request from '@/utils/request'

// 获取 OSS Bucket 列表
export function listOSSBuckets(params) {
  return request({
    url: '/oss/',
    method: 'get',
    params
  })
}

// 获取单个 Bucket 详情（通过 bucket name）
export function getOSSBucketDetail(name) {
  return request({
    url: `/oss/buckets/${name}/`,
    method: 'get'
  })
}

// 同步 OSS 数据（后端目前是 POST，保持不变）
export function syncOSSBuckets() {
  return request({
    url: '/oss/sync/',
    method: 'post'
  })
}

// 导出 OSS 数据为 Excel
export function exportOSSBuckets(params) {
  return request({
    url: '/oss/export/',
    method: 'get',
    params,
    responseType: 'blob'
  })
}

