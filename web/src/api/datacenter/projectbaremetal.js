import request from '@/utils/request'

export function listProjectBareMetal(params) {
  return request({
    url: '/projectbaremetal/',
    method: 'get',
    timeout: 20000,
    params
  })
}

export function getProjectBareMetal(id) {
  return request({
    url: `/projectbaremetal/${id}/`,
    method: 'get',
    timeout: 20000
  })
}

export function createProjectBareMetal(data) {
  return request({
    url: '/projectbaremetal/',
    method: 'post',
    timeout: 20000,
    data
  })
}

export function updateProjectBareMetal(id, data) {
  return request({
    url: `/projectbaremetal/${id}/`,
    method: 'put',
    timeout: 20000,
    data
  })
}

export function deleteProjectBareMetal(id) {
  return request({
    url: `/projectbaremetal/${id}/`,
    method: 'delete',
    timeout: 20000
  })
}
