import request from '@/utils/request'

// 获取Proxmox虚拟机列表
export function getProxmoxList(params) {
  return request({
    url: '/proxmox/',
    method: 'get',
    timeout: 20000,
    params
  })
}

// 同步Proxmox虚拟机数据
export function syncProxmox() {
  return request({
    url: '/proxmox/sync/',
    method: 'post',
    timeout: 180000  // 同步可能需要较长时间（3分钟）
  })
}

// 获取统计数据
export function getProxmoxStats(params) {
  return request({
    url: '/proxmox/stats/',
    method: 'get',
    timeout: 20000,
    params
  })
}

// 更新Proxmox虚拟机
export function updateProxmoxVM(id, data) {
  return request({
    url: `/proxmox/${id}/`,
    method: 'patch',
    data
  })
}

// 删除Proxmox虚拟机
export function deleteProxmoxVM(id) {
  return request({
    url: `/proxmox/${id}/`,
    method: 'delete'
  })
}
