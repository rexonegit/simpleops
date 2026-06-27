import request from '@/utils/request'

export function getDNSRecordList(params) {
  return request({
    url: '/dnsrecord/',
    method: 'get',
    timeout: 20000,
    params
  })
}
