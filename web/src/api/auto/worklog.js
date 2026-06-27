import request from '@/utils/request'

// 获取所有可选的技术员列表（用于下拉框）
export function getTechOptions() {
  // 可以复用 list 接口，或者单独写一个接口
  // 这里假设 list 接口的返回结构里包含了 techOptions
  return request({
    url: '/daily_work_log/',
    method: 'get',
    params: { pageSize: 1 } // 取一条数据顺便拿 options
  })
}

// 预览聚合数据
export function previewWorkLog(data) {
  return request({
    url: '/daily_work_log/preview/', // 注意：Django 默认必须加末尾斜杠 /
    method: 'post',
    data,
    // 关键点：显式指定 JSON，避开 request.js 中的 qs.stringify 逻辑
    // 这样后端 request.data 就能直接拿到干净的 list/dict 结构
    headers: {
      'Content-Type': 'application/json;charset=UTF-8'
    }
  })
}

// 导出 Excel (保持 GET)
// 注意：GET 请求参数放在 params 中，Axios 会自动序列化，
// 但后端 getlist 需要前端传递参数名为 name[] 或使用 paramsSerializer
export function exportWorkLog(params) {
  return request({
    url: '/daily_work_log/export/',
    method: 'get',
    params,
    responseType: 'blob'
  })
}

// 执行同步
export function syncGlpi(data) {
  return request({
    url: '/daily_work_log/sync/',
    method: 'post',
    data
  })
}
