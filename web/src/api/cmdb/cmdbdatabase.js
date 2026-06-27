import request from '@/utils/request'

export function listcmdbdatabase(params) {
  return request({
    url: '/cmdbdatabase/',
    method: 'get',
    timeout: 20000,
    params
  })
}

export function createcmdbdatabase(data) {
  return request({
    url: '/cmdbdatabase/',
    method: 'post',
    timeout: 20000,
    data
  })
}

export function updatecmdbdatabase(id, data) {
  return request({
    url: `/cmdbdatabase/${id}/`,
    method: 'put',
    timeout: 20000,
    data
  })
}

export function deletecmdbdatabase(id) {
  return request({
    url: `/cmdbdatabase/${id}/`,
    method: 'delete',
    timeout: 20000
  })
}
