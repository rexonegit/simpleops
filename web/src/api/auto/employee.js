// @/api/employee.js
import request from '@/utils/request'

// 获取员工账号列表
export function listEmployeeAccounts(params) {
  return request({
    url: '/employeeaccounts/',
    method: 'get',
    params: params
  })
}

// 创建员工账号
export function createEmployeeAccount(data) {
  return request({
    url: '/employeeaccounts/',
    method: 'post',
    data: data
  })
}

// 删除员工账号
export function deleteEmployeeAccount(id) {
  return request({
    url: `/employeeaccounts/${id}/`,
    method: 'delete'
  })
}

// 导出员工账号为CSV
export function exportEmployeeAccounts(params) {
  return request({
    url: '/employeeaccounts/export/',
    method: 'get',
    params,
    responseType: 'blob' // 重要：处理二进制响应
  })
}

// 导入员工账号CSV
export function importEmployeeAccounts(data) {
  return request({
    url: '/employeeaccounts/import_csv/',
    method: 'post',
    data: data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export function updateEmployeeAccount(data) {
  return request({
    url: `/employeeaccounts/${data.id}/`,
    method: 'put',
    data
  })
}

// 新增：获取电脑需求统计数据
export function getComputerStats(params) {
  return request({
    url: '/employee/computer-stats/',
    method: 'get',
    params: params
  })
}

// 新增：离职办理
export function exitEmployeeAccount(id, data) {
  return request({
    url: `/employeeaccounts/${id}/exit/`,
    method: 'patch',
    data
  })
}

// 添加获取未归还资产的API函数
export function getUnreturnedAssets(params) {
  return request({
    url: '/unreturned-assets/',
    method: 'get',
    params
  })
}

