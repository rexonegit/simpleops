import request from '@/utils/request'

export function getDNSRecordList(params) {
  return request({
    url: '/api/dns-records/',
    method: 'get',
    params
  })
}

export function syncDNSRecords() {
  return request({
    url: '/api/dns-records/sync/',
    method: 'post'
  })
}
