import request from '@/utils/request'

export function listProjectProxmox(params) {
  return request({
    url: '/projectproxmox/',
    method: 'get',
    timeout: 20000,
    params
  })
}

export function createProjectProxmox(data) {
  return request({
    url: '/projectproxmox/',
    method: 'post',
    timeout: 20000,
    data
  })
}

export function updateProjectProxmox(id, data) {
  return request({
    url: `/projectproxmox/${id}/`,
    method: 'put',
    timeout: 20000,
    data
  })
}

export function deleteProjectProxmox(id) {
  return request({
    url: `/projectproxmox/${id}/`,
    method: 'delete',
    timeout: 20000
  })
}
