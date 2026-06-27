// src/api/menu.js
import request from '@/utils/request'

// 获取导航菜单（动态路由）- POST 方法
export function getRouterList() {
  return request({
    url: '/menu/navigate/',
    method: 'post'
  })
}


export function getMenuTree() {
  return request({
    url: '/menu/tree/',
    method: 'get'
  })
}

export function createMenu(data) {
  return request({
    url: '/menu/create/',
    method: 'post',
    data
  })
}

export function updateMenu(data) {
  return request({
    url: `/menu/update/${data.id}/`,
    method: 'put',
    data
  })
}

export function deleteMenu(id) {
  return request({
    url: `/menu/delete/${id}/`,
    method: 'delete'
  })
}
