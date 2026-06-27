<template>
  <div>
    <div class="avatar-wrapper" @click="openFileDialog">
      <el-avatar :size="100" :src="avatarUrl" />
      <input
        ref="fileRef"
        type="file"
        accept="image/*"
        hidden
        @change="onFileChange"
      />
    </div>

    <el-dialog v-model="showPreview" title="更新头像" width="320px" align-center>
      <div class="preview-box">
        <el-avatar :size="200" :src="previewUrl" />
      </div>
      <template #footer>
        <el-button @click="showPreview = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleConfirm">确认更换</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadAvatar } from '@/api/user' // ✅ Import API function
import { baseURL } from '@/config'

const props = defineProps({
  user: {
    type: Object,
    default: () => ({}),
    required: true
  }
})

const emit = defineEmits(['update-success'])

const fileRef = ref(null)
const showPreview = ref(false)
const previewUrl = ref('')
const uploading = ref(false)
const selectedFile = ref(null)

// 当前头像URL
const avatarUrl = computed(() => {
  const name = props.user.avatar
  if (!name) return ''
  // 移除可能存在的 API 后缀，确保指向 media 目录
  const cleanBaseURL = baseURL.endsWith('/api') ? baseURL.slice(0, -4) : baseURL
  // 如果 baseURL 以 / 结尾，去掉
  const finalBaseURL = cleanBaseURL.endsWith('/') ? cleanBaseURL.slice(0, -1) : cleanBaseURL

  return `${finalBaseURL}/${name}`
})

function openFileDialog() {
  fileRef.value?.click()
}

function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.error('只能上传图片')
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('图片不能超过 2MB')
    return
  }

  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
  showPreview.value = true

  // 清空input，允许重复选择同一文件
  e.target.value = ''
}

const handleConfirm = async () => {
  if (!selectedFile.value) {
    ElMessage.error('请先选择图片')
    return
  }

  uploading.value = true
  try {
    // ✅ 修复：字段名改为 'file'，匹配后端
    const formData = new FormData()
    formData.append('file', selectedFile.value) // ✅ 关键：改为 'file'

    // ✅ 调用后端单个API完成上传和更新
    // ✅ 使用封装的 API
    const result = await uploadAvatar(formData)

    if (result.code === 200) {
      // ✅ 后端返回 { avatar: "filename.jpg" }
      const avatarName = result.data.avatar // ✅ 提取文件名

      ElMessage.success("头像更新成功！")

      // ✅ 通知父组件更新
      emit('update-success', { avatar: avatarName })

      showPreview.value = false
      selectedFile.value = null
    } else {
      ElMessage.error(responseData.msg || '更新失败')
    }
  } catch (error) {
    console.error('头像上传失败:', error)
    ElMessage.error('头像上传失败: ' + (error.message || '未知错误'))
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.avatar-wrapper {
  position: relative;
  display: inline-block;
  margin-bottom: 16px;
  cursor: pointer;
  border-radius: 50%;
  overflow: hidden;

  &::after {
    content: '修改头像';
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 36px;
    line-height: 36px;
    text-align: center;
    color: #fff;
    font-size: 14px;
    background: rgba(0, 0, 0, .45);
    opacity: 0;
    transition: opacity .3s;
  }

  &:hover::after {
    opacity: 1;
  }
}

.preview-box {
  text-align: center;
}
</style>
