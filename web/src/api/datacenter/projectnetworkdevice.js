import request from '@/utils/request'

export function listProjectNetworkDevice(params) {
  return request({
    url: '/projectnetworkdevice/',
    method: 'get',
    timeout: 20000,
    params
  })
}

export function createProjectNetworkDevice(data) {
  return request({
    url: '/projectnetworkdevice/',
    method: 'post',
    timeout: 20000,
    data
  })
}

export function updateProjectNetworkDevice(id, data) {
  return request({
    url: `/projectnetworkdevice/${id}/`,
    method: 'put',
    timeout: 20000,
    data
  })
}

export function deleteProjectNetworkDevice(id) {
  return request({
    url: `/projectnetworkdevice/${id}/`,
    method: 'delete',
    timeout: 20000
  })
}
