import request from '@/utils/request'

export function listProjectVMware(params) {
  return request({
    url: '/projectvmware/',
    method: 'get',
    timeout: 20000,
    params
  })
}

export function createProjectVMware(data) {
  return request({
    url: '/projectvmware/',
    method: 'post',
    timeout: 20000,
    data
  })
}

export function updateProjectVMware(id, data) {
  return request({
    url: `/projectvmware/${id}/`,
    method: 'put',
    timeout: 20000,
    data
  })
}

export function deleteProjectVMware(id) {
  return request({
    url: `/projectvmware/${id}/`,
    method: 'delete',
    timeout: 20000
  })
}
