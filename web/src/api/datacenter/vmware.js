import request from '@/utils/request'

export function getVMwareList(params) {
  return request({
    url: '/vmware/',
    method: 'get',
    timeout: 20000,
    params
  })
}

export function syncVMware() {
  return request({
    url: '/vmware/sync/',
    method: 'post',
    timeout: 120000  // 同步可能需要较长时间
  })
}
