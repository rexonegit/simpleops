// src/utils/export.js
import { ElMessage } from 'element-plus'

/**
 * 统一导出文件处理（支持错误JSON提示 + 正常文件下载）
 * 为了兼容项目中所有地方的旧写法，函数名同时叫 handleFileError 和 handle
 */
function handleFileError(res, fileName) {
  // 1. 后端返回错误 JSON
  if (res && res.data && res.data.type === 'application/json') {
    const reader = new FileReader()
    reader.onload = function () {
      try {
        const result = JSON.parse(reader.result)
        ElMessage.error(result.msg || result.message || '导出失败')
      } catch (e) {
        ElMessage.error('导出失败：解析错误信息异常')
      }
    }
    if (res.data instanceof Blob) {
      reader.readAsText(res.data)
    } else {
      reader.readAsText(new Blob([res.data]))
    }
    return
  }

  // 2. 正常文件流
  let blob = res
  if (res && res.data) blob = res.data
  if (!(blob instanceof Blob)) blob = new Blob([blob])

  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.style.display = 'none'
  a.href = url
  a.download = fileName || 'download'
  document.body.appendChild(a)
  a.click()
  setTimeout(() => {
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }, 100)
}

// 关键：同时导出 handle，兼容所有老代码里直接写 .then(handle) 的情况
export { handleFileError }
export const handle = handleFileError   // ← 这一行解决你的报错！
export default handleFileError
