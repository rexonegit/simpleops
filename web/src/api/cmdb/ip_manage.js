import request from '@/utils/request'


// 获取网段统计信息（新接口）
export function getIPSegments(params) {
  return request({
    url: '/ip-addresses/segments/',
    method: 'get',
    params
  })
}


export function getNetworkSegmentList(params) {
  return request({
    url: '/network-segment/',
    method: 'get',
    params
  })
}

export function createNetworkSegment(data) {
  return request({
    url: '/network-segment/',
    method: 'post',
    data
  })
}

export function updateNetworkSegment(id, data) {
  return request({
    url: `/network-segment/${id}/`,
    method: 'put',
    data
  })
}

export function deleteNetworkSegment(id) {
  return request({
    url: `/network-segment/${id}/`,
    method: 'delete'
  })
}

// 获取IP地址列表（支持网段筛选）
export function getIPAddressList(params) {
  return request({
    url: '/ip-addresses/',
    method: 'get',
    params
  })
}

export function createIPAddress(data) {
  return request({
    url: '/ip-addresses/',
    method: 'post',
    data
  })
}

// 更新IP
export function updateIPAddress(id, data) {
  return request({
    url: `/ip-addresses/${id}/`,
    method: 'patch',
    data
  })
}

// 删除IP
export function deleteIPAddress(id) {
  return request({
    url: `/ip-addresses/${id}/`,
    method: 'delete'
  })
}

// 同步IP数据
export function syncIPAddress() {
  return request({
    url: '/ip-addresses/sync/',
    method: 'post',
    timeout: 60000 // 同步可能需要较长时间
  })
}
