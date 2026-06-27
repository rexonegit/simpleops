// src/api/securityGroup.js
import request from '@/utils/request'

// 获取安全组列表
export function fetchSecurityGroups(params) {
  return request({
    url: '/security-groups/',
    method: 'get',
    params
  })
}

// 获取安全组详情
export function fetchSecurityGroupDetail(groupId) {
  return request({
    url: `/security-groups/${groupId}/`,
    method: 'get'
  })
}

// 获取安全组规则
export function fetchSecurityGroupRules(params) {
  return request({
    url: '/security-group-rules/',
    method: 'get',
    params
  })
}

// 添加安全组规则
export function addSecurityGroupRule(data) {
  return request({
    url: '/api/security-group-rules/',
    method: 'post',
    data
  })
}

// 删除安全组规则
export function deleteSecurityGroupRule(ruleId) {
  return request({
    url: `/security-group-rules/${ruleId}/`,
    method: 'delete'
  })
}

// 获取安全组关联实例
export function fetchSecurityGroupInstances(groupId) {
  return request({
    url: `/security-groups/${groupId}/instances/`,
    method: 'get'
  })
}

// 同步安全组
export function syncSecurityGroups() {
  return request({
    url: '/security-groups/sync/',
    method: 'post'
  })
}
