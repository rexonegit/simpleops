import request from '@/utils/request'

export function listProjectAliyunDomain(params) {
  return request({
    url: '/projectaliyundomain/',
    method: 'get',
    timeout: 20000,
    params
  })
}

export function createProjectAliyunDomain(data) {
  return request({
    url: '/projectaliyundomain/',
    method: 'post',
    timeout: 20000,
    data
  })
}

export function updateProjectAliyunDomain(id, data) {
  return request({
    url: `/projectaliyundomain/${id}/`,
    method: 'put',
    timeout: 20000,
    data
  })
}

export function deleteProjectAliyunDomain(id) {
  return request({
    url: `/projectaliyundomain/${id}/`,
    method: 'delete',
    timeout: 20000
  })
}

