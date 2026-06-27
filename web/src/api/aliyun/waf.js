import request from '@/utils/request'

export function fetchWAFList(params) {
  return request({
    url: '/waf/',
    method: 'get',
    params
  })
}

export function fetchWAFDetail(instanceId) {
  return request({
    url: `/waf/${instanceId}/`,
    method: 'get'
  })
}

export function syncWAF() {
  return request({
    url: '/waf/sync/',
    method: 'post',
    timeout: 60000
  })
}
