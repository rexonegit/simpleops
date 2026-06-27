import request from '@/utils/request'

export function fetchSLBList(params) {
  return request({
    url: '/slb/',
    method: 'get',
    params
  })
}

export function fetchSLBDetail(id) {
  return request({
    url: `/slb/${id}/`,
    method: 'get'
  })
}

export function syncSLB() {
  return request({
    url: '/slb/sync/',
    method: 'post',
    timeout: 60000
  })
}

// --------- ProjectAliyunSLB API ---------
export function listProjectAliyunSLB(params) {
  return request({
    url: '/projectaliyunslb/',
    method: 'get',
    timeout: 20000,
    params
  })
}

export function createProjectAliyunSLB(data) {
  return request({
    url: '/projectaliyunslb/',
    method: 'post',
    timeout: 20000,
    data
  })
}

export function updateProjectAliyunSLB(id, data) {
  return request({
    url: `/projectaliyunslb/${id}/`,
    method: 'put',
    timeout: 20000,
    data
  })
}

export function deleteProjectAliyunSLB(id) {
  return request({
    url: `/projectaliyunslb/${id}/`,
    method: 'delete',
    timeout: 20000
  })
}
