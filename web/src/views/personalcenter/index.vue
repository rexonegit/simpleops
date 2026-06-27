<template>
  <div class="profile-container">
    <VabPageHeader
      title="个人中心"
      description="您可以在这里管理个人信息、修改密码以及进行安全设置"
      :icon="['fas', 'user-circle']"
    >
        <template #right>
            <el-tag>{{ formatRoles(currentUser.roles, currentUser.roleNames) }}</el-tag>
        </template>
    </VabPageHeader>

    <el-row :gutter="20">
      <!-- 左侧个人信息卡片 -->
      <el-col :span="8">
        <el-card class="user-card" v-loading="loading">
          <div class="user-info">
            <!-- ✅ 直接使用 AvatarUpload 组件 -->
            <AvatarUpload
              :user="currentUser"
              @update-success="handleAvatarUpdate"
            />
            <div class="user-name">
              <span class="username">{{ currentUser.username }}</span>
            </div>
            <div class="user-role">{{ formatRoles(currentUser.roles, currentUser.roleNames) }}</div>
          </div>
          <el-divider />
          <div class="user-stats">
            <div class="stat-item">
              <div class="stat-value">0</div>
              <div class="stat-label">待办</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">0</div>
              <div class="stat-label">消息</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">0</div>
              <div class="stat-label">通知</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧信息卡片 -->
      <el-col :span="16">
        <el-card class="info-card" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>账号信息</span>
              <el-button
                type="primary"
                link
                @click="() => handleOpenDialog(DialogType.ACCOUNT)"
                class="edit-btn"
              >
                修改
              </el-button>
            </div>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="用户名">
              {{ currentUser.username || "未绑定" }}
            </el-descriptions-item>
            <el-descriptions-item label="手机号码">
              {{ currentUser.phone || "未绑定" }}
            </el-descriptions-item>
            <el-descriptions-item label="邮箱">
              {{ currentUser.email || "未绑定" }}
            </el-descriptions-item>
            <el-descriptions-item label="所属角色">
              {{ formatRoles(currentUser.roles, currentUser.roleNames) }}
            </el-descriptions-item>
            <el-descriptions-item label="最后登录">
              {{ currentUser.last_login || "暂无记录" }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card class="security-card" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>安全设置</span>
            </div>
          </template>
          <div class="security-item">
            <div class="security-info">
              <div class="security-title">账户密码</div>
              <div class="security-desc">定期修改密码有助于保护账户安全</div>
            </div>
            <el-button type="primary" link @click="() => handleOpenDialog(DialogType.PASSWORD)">
              修改
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 账号/密码弹窗 -->
    <el-dialog v-model="dialog.visible" :title="dialog.title" width="500px">
      <AccountInfo
        v-if="dialog.type === DialogType.ACCOUNT"
        ref="accountInfoRef"
        :user="currentUser"
        @update-success="handleAccountUpdate"
      />

      <PasswordChange
        v-else-if="dialog.type === DialogType.PASSWORD"
        ref="passwordChangeRef"
        :user="currentUser"
        @update-success="handlePasswordUpdate"
      />

      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { getUserInfo } from '@/api/user' // ✅ 使用你的接口
import { baseURL } from '@/config'
import VabPageHeader from '@/components/VabPageHeader/index.vue'
import AvatarUpload from './components/avatar.vue'
import AccountInfo from './components/userinfo.vue'
import PasswordChange from './components/resetpwd.vue'

defineOptions({ name: 'PersonalCenter' })

// 响应式用户数据
const currentUser = ref({})

// 加载状态
const loading = ref(false)

// 头像上传文件引用
const fileRef = ref(null)

// 工具函数：格式化角色
const formatRoles = (roles, roleNames) => {
  if (roleNames && roleNames.length > 0) return roleNames.join(', ')
  if (!roles || roles.length === 0) return '未分配'
  return roles.join(', ')
}

// 头像URL计算
const avatarUrl = computed(() => {
  const name = currentUser.value.avatar
  if (!name) return ''
  const cleanBaseURL = baseURL.endsWith('/api') ? baseURL.slice(0, -4) : baseURL
  const finalBaseURL = cleanBaseURL.endsWith('/') ? cleanBaseURL.slice(0, -1) : cleanBaseURL
  return `${finalBaseURL}/${name}`
})

// 头像上传相关
function selectFile() {
  fileRef.value?.click()
}

function onFileChange(e) {
  const file = e.target.files[0]
  if (file) {
    console.log('Selected file:', file)
    // 这里可以调用头像上传API
  }
}

// 弹窗管理
const DialogType = {
  ACCOUNT: 'account',
  PASSWORD: 'password'
}

const dialog = ref({
  visible: false,
  title: '',
  type: ''
})

function handleOpenDialog(type) {
  dialog.value.type = type
  dialog.value.visible = true
  switch (type) {
    case DialogType.ACCOUNT:
      dialog.value.title = '账号资料'
      break
    case DialogType.PASSWORD:
      dialog.value.title = '修改密码'
      break
  }
}

function handleAccountUpdate(userData) {
  Object.assign(currentUser.value, userData)
  dialog.value.visible = false
  ElMessage.success('账号信息更新成功')
}

function handlePasswordUpdate() {
  dialog.value.visible = false
  ElMessage.success('密码修改成功')
}

// ✅ 核心：页面加载时获取用户信息
onMounted(async () => {
  loading.value = true
  try {
    const response = await getUserInfo() // ✅ 使用改造后的接口
    if (response.code === 200) { // ✅ 注意：response已经是data
      currentUser.value = response.data
    } else {
      ElMessage.error(response.msg || '获取用户信息失败')
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    ElMessage.error('获取用户信息失败')
  } finally {
    loading.value = false
  }
})

function handleAvatarUpdate(userData) {
  // 更新本地用户信息
  Object.assign(currentUser.value, userData)
  ElMessage.success('头像更新成功')
}

</script>


<style lang="scss" scoped>
.profile-container {
  min-height: calc(100vh - 84px);
  padding: 20px;
  background: var(--el-fill-color-blank);
}

.user-card .user-info {
  text-align: center;
  padding: 20px 0;

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

  .user-name {
    margin-bottom: 8px;

    .username {
      font-size: 18px;
      font-weight: 600;
    }
  }

  .user-role {
    font-size: 14px;
    color: var(--el-text-color-secondary);
  }
}

.user-stats {
  display: flex;
  justify-content: space-around;
  padding: 16px 0;

  .stat-item {
    text-align: center;

    .stat-value {
      font-size: 20px;
      font-weight: 600;
    }

    .stat-label {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
}

.info-card,
.security-card {
  margin-bottom: 20px;

  .card-header {
    font-size: 16px;
    font-weight: 600;
  }
}

.card-header {
  font-size: 16px;
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  align-items: center;

  .edit-btn {
    font-size: 14px;
  }
}

.security-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;

  .security-info {
    .security-title {
      font-size: 16px;
      font-weight: 500;
    }

    .security-desc {
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
  }
}
</style>
