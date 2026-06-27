// src/api/auto/inventory.js
import request from '@/utils/request'

export function getComputerInventory(params) {
  return request({
    url: '/computer-inventory/',
    method: 'get',
    params
  })
}

export function getComputerInventoryStats() {
  return request({
    url: '/computer-inventory-stats/',
    method: 'get'
  })
}

export function getTotalByModel(type, assetType = 'all') {
  return request({
    url: '/total-by-model/',
    method: 'get',
    params: { type, asset_type: assetType }
  })
}

/**
 * 获取统一库存视图（所有型号汇总）
 */
export function getUnifiedInventory() {
  return request({
    url: '/inventory/unified/',
    method: 'get'
  })
}
