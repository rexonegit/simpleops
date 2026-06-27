import request from '@/utils/request'

export function ecslist(params) {
  return request({
    url: '/ecs/',
    method: 'get',
    params
  })
}

// 同步 ECS 数据（后端目前是 POST，保持不变）
export function syncecs() {
  return request({
    url: '/ecs/sync/',
    method: 'post'
  })
}


export function listProjectAliyunecs(params) {
  return request({
    url: '/projectaliyunecs/',
    method: 'get',
    timeout: 20000,
    params
  })
}

export function createProjectAliyunecs(data) {
  return request({
    url: '/projectaliyunecs/',
    method: 'post',
    timeout: 20000,
    data
  })
}

export function updateProjectAliyunecs(id, data) {
  return request({
    url: `/projectaliyunecs/${id}/`, // 修正API路径
    method: 'put',
    timeout: 20000,
    data
  })
}

export function deleteProjectAliyunecs(id) {
  return request({
    url: `/projectaliyunecs/${id}/`, // 修正API路径
    method: 'delete',
    timeout: 20000
  })
}




