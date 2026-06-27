import request from '@/utils/request'

export function fetchNASList(params) {
  return request({
    url: '/nas/',
    method: 'get',
    params
  })
}

export function fetchNASDetail(fileSystemId) {
  return request({
    url: `/nas/${fileSystemId}/`,
    method: 'get'
  })
}

export function syncNAS() {
  return request({
    url: '/nas/sync/',
    method: 'post',
    timeout: 60000
  })
}

// --------- ProjectAliyunNAS API ---------
export function listProjectAliyunNAS(params) {
  return request({
    url: '/projectaliyunnas/',
    method: 'get',
    timeout: 20000,
    params
  })
}

export function createProjectAliyunNAS(data) {
  return request({
    url: '/projectaliyunnas/',
    method: 'post',
    timeout: 20000,
    data
  })
}

export function updateProjectAliyunNAS(id, data) {
  return request({
    url: `/projectaliyunnas/${id}/`,
    method: 'put',
    timeout: 20000,
    data
  })
}

export function deleteProjectAliyunNAS(id) {
  return request({
    url: `/projectaliyunnas/${id}/`,
    method: 'delete',
    timeout: 20000
  })
}
