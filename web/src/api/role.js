// src/api/role.js
import request from '@/utils/request'

export function getRoleList() {
  return request({
    url: '/menu/role/list/',
    method: 'get'
  })
}

export function createRole(data) {
  return request({
    url: '/menu/role/create/',
    method: 'post',
    data
  })
}

export function updateRole(data) {
  return request({
    url: `/menu/role/update/${data.id}/`,
    method: 'put',
    data
  })
}

export function deleteRole(id) {
  return request({
    url: `/menu/role/delete/${id}/`,
    method: 'delete'
  })
}

export function getRolePermissions(id) {
  return request({
    url: `/menu/role/permissions/${id}/`,
    method: 'get'
  })
}

export function assignPermissions(data) {
  return request({
    url: '/menu/role/assign-permissions/',
    method: 'post',
    data
  })
}
