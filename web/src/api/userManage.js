// src/api/userManage.js
import request from '@/utils/request'

export function getUserList(params) {
  return request({
    url: '/menu/user/list/',
    method: 'get',
    params
  })
}

export function createUser(data) {
  return request({
    url: '/menu/user/create/',
    method: 'post',
    data
  })
}

export function updateUser(data) {
  return request({
    url: `/menu/user/update/${data.id}/`,
    method: 'put',
    data
  })
}

export function deleteUser(data) {
  return request({
    url: '/menu/user/delete/',
    method: 'delete',
    data
  })
}

export function resetPassword(data) {
  return request({
    url: '/menu/user/reset-password/',
    method: 'post',
    data
  })
}

export function getRoleSelect() {
  return request({
    url: '/menu/user/roles/',
    method: 'get'
  })
}
