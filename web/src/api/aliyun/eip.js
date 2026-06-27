import request from '@/utils/request'

export function fetchEIPList(params) {
  return request({
    url: '/eip/',
    method: 'get',
    params
  })
}

export function fetchEIPDetail(allocationId) {
  return request({
    url: `/eip/${allocationId}/`,
    method: 'get'
  })
}

export function syncEIPs() {
  return request({
    url: '/eip/sync/',
    method: 'post',
    timeout: 60000
  })
}
