import request from '@/utils/request'

// 列表请求（保持不变）
export const fetchRDSList = (params) => {
  return request({
    url: '/rds/',
    method: 'get',
    params
  })
}

// 详情请求（关键：加一个标识，跳过 code 判断）
export const fetchRDSDetail = (instanceId) => {
  return request({
    url: `/rds/${instanceId}/`,
    method: 'get',
  })
}

// 同步请求
export const syncRDSInstances = () => {
  return request({
    url: '/rds/sync/',
    method: 'post'
  })
}

// --------- ProjectAliyunRDS API ---------
export function listProjectAliyunRDS(params) {
  return request({
    url: '/projectaliyunrds/',
    method: 'get',
    timeout: 20000,
    params
  })
}

export function createProjectAliyunRDS(data) {
  return request({
    url: '/projectaliyunrds/',
    method: 'post',
    timeout: 20000,
    data
  })
}

export function updateProjectAliyunRDS(id, data) {
  return request({
    url: `/projectaliyunrds/${id}/`,
    method: 'put',
    timeout: 20000,
    data
  })
}

export function deleteProjectAliyunRDS(id) {
  return request({
    url: `/projectaliyunrds/${id}/`,
    method: 'delete',
    timeout: 20000
  })
}
