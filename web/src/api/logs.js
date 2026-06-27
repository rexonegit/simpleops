// src/api/logs.js
import request from '@/utils/request'

export function getLoginLogList(params) {
  return request({
    url: '/logs/login-log/list/',  // 必须带 list/
    method: 'get',
    params
  })
}

export function getOperationLogList(params) {
  return request({
    url: '/logs/operation-log/list/',  // 必须带 list/
    method: 'get',
    params
  })
}
