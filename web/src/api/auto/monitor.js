import request from '@/utils/request'

export function getHistoryAlerts(params) {
  return request({
    url: '/monitor/alerts/history/',
    method: 'get',
    params
  })
}

export function getRealTimeAlerts(params) {
  return request({
    url: '/monitor/alerts/realtime/',
    method: 'get',
    params
  })
}

export function syncAlerts(params) {
  return request({
    url: '/monitor/alerts/sync/',
    method: 'post',
    data: params,
    timeout: 60000
  })
}

export function updateAlertStatus(id, data) {
  return request({
    url: `/monitor/alerts/${id}/status/`,
    method: 'put',
    data
  })
}

export function getDashboardStats() {
  return request({
    url: '/monitor/dashboard/stats/',
    method: 'get'
  })
}

export function getAlertTypeDistribution() {
  return request({
    url: '/monitor/dashboard/alert-type-distribution/',
    method: 'get'
  })
}

export function getAlertLevelDistribution() {
  return request({
    url: '/monitor/dashboard/alert-level-distribution/',
    method: 'get'
  })
}

export function getAlertTrend(params) {
  return request({
    url: '/monitor/dashboard/alert-trend/',
    method: 'get',
    params
  })
}

export function getRecentAlerts() {
  return request({
    url: '/monitor/dashboard/recent-alerts/',
    method: 'get'
  })
}

// Application Group API
export function listGroups(params) {
  return request({
    url: '/monitor/groups/',
    method: 'get',
    params
  })
}

export function getUngroupedHosts() {
  return request({
    url: '/monitor/hosts/ungrouped/',
    method: 'get'
  })
}

export function getGroupHosts(groupId) {
  return request({
    url: `/monitor/groups/${groupId}/hosts/`,
    method: 'get'
  })
}

export function assignHostToGroup(data) {
  return request({
    url: '/monitor/groups/assign/',
    method: 'post',
    data
  })
}

export function removeHostFromGroup(data) {
  return request({
    url: '/monitor/groups/remove/',
    method: 'post',
    data
  })
}

export function syncGroups() {
  return request({
    url: '/monitor/groups/sync/',
    method: 'post',
    timeout: 60000
  })
}
