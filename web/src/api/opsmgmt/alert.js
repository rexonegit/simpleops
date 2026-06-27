import request from '@/utils/request'

// 获取告警列表
export function listAlerts(params) {
    return request({
        url: '/opsmgmt/alerts/',
        method: 'get',
        timeout: 20000,
        params
    })
}

// 获取告警统计
export function getAlertStats(params) {
    return request({
        url: '/opsmgmt/alerts/stats/',
        method: 'get',
        timeout: 20000,
        params
    })
}

// 创建告警记录
export function createAlert(data) {
    return request({
        url: '/opsmgmt/alerts/',
        method: 'post',
        timeout: 20000,
        data
    })
}

// 更新告警记录
export function updateAlert(id, data) {
    return request({
        url: `/opsmgmt/alerts/${id}/`,
        method: 'put',
        timeout: 20000,
        data
    })
}

// 删除告警记录
export function deleteAlert(id) {
    return request({
        url: `/opsmgmt/alerts/${id}/`,
        method: 'delete',
        timeout: 20000
    })
}
