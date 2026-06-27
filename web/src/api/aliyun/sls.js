// src/api/aliyun/sls.js
import request from '@/utils/request'

// ==================== SLS Project 列表 ====================
/**
 * 获取 SLS Project 列表（分页）
 * GET /api/sls/
 */
export function fetchSLSList(params) {
  return request({
    url: '/sls/',
    method: 'get',
    params
  })
}

/**
 * 获取单个 SLS Project 详情（用于详情页）
 * GET /api/sls/{project_name}/
 */
export function fetchSLSDetail(projectName) {
  return request({
    url: `/sls/${projectName}/`,
    method: 'get'
  })
}

/**
 * 同步 SLS 数据
 * POST /api/sls/sync/
 */
export function syncSLSapi() {
  return request({
    url: '/sls/sync/',
    method: 'post'
  })
}

/**
 * 可选：导出 SLS Project 数据（如果需要导出功能）
 */
export function exportSLS(params = {}) {
  return request({
    url: '/sls/export/',
    method: 'get',
    params,
    responseType: 'blob',
    timeout: 300000 // 导出可能较慢
  })
}

// ==================== ProjectAliyunSLS (项目归属管理) ====================

export function listProjectAliyunSLS(params) {
  return request({
    url: '/projectaliyunsls/',
    method: 'get',
    params
  })
}

export function createProjectAliyunSLS(data) {
  return request({
    url: '/projectaliyunsls/',
    method: 'post',
    data
  })
}

export function updateProjectAliyunSLS(id, data) {
  return request({
    url: `/projectaliyunsls/${id}/`,
    method: 'put',
    data
  })
}

export function deleteProjectAliyunSLS(id) {
  return request({
    url: `/projectaliyunsls/${id}/`,
    method: 'delete'
  })
}
