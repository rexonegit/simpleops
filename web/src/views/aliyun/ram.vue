<!--web/src/views/aliyun/ramuser/index.vue-->
<template>
  <div class="app-container">
    <!-- ============== 列表页 ============== -->
    <div v-if="!selectedUser" class="page-list">
      <!-- 查询卡片 -->
      <el-card shadow="always">
        <el-form
          :model="queryParams"
          ref="queryFormRef"
          :inline="true"
          label-width="78px"
        >
          <el-form-item label="登录名称" prop="search">
            <el-input
              v-model="queryParams.search"
              placeholder="用户登录名称查询"
              clearable
              style="width:200px"
              @keyup.enter="handleQuery"
            />
          </el-form-item>
          <el-form-item label="显示名称" prop="display_name">
            <el-input
              v-model="queryParams.display_name"
              placeholder="显示名称查询"
              clearable
              style="width:160px"
              @keyup.enter="handleQuery"
            />
          </el-form-item>
          <el-form-item label="账号状态" prop="active">
            <el-select v-model="queryParams.active" clearable style="width:120px">
              <el-option label="激活" :value="true" />
              <el-option label="禁用" :value="false" />
            </el-select>
          </el-form-item>
          <el-form-item label="MFA状态" prop="mfa_enabled">
            <el-select v-model="queryParams.mfa_enabled" clearable style="width:120px">
              <el-option label="已启用" :value="true" />
              <el-option label="未启用" :value="false" />
            </el-select>
          </el-form-item>
          <el-form-item label="所属账号" prop="account_name">
            <el-select v-model="queryParams.account_name" clearable style="width:160px">
              <el-option v-for="a in accountOptions" :key="a" :label="a" :value="a" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleQuery">
              <el-icon><Search /></el-icon>搜索
            </el-button>
            <el-button @click="resetQuery">
              <el-icon><Refresh /></el-icon>重置
            </el-button>
            <el-button type="success" @click="handleSync">
              <el-icon><RefreshRight /></el-icon>同步
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 列表表格 -->
      <el-card class="mt-10">
        <template #header>
          <div class="card-header">
            <span>RAM用户列表</span>
            <el-button type="primary" plain @click="handleExport">
              <el-icon><Download /></el-icon>导出
            </el-button>
          </div>
        </template>
        <el-table
          v-loading="loading"
          :data="tableData"
          stripe
          border
          height="calc(100vh - 360px)"
        >
          <el-table-column prop="user_principal_name" label="用户登录名称" min-width="200" sortable />
          <el-table-column prop="display_name" label="显示名称" min-width="120" sortable />
          <el-table-column label="账号状态" width="90" align="center">
            <template #default="{row}">
              <el-tag :type="row.active ? 'success' : 'danger'">
                {{ row.active ? '激活' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="MFA状态" width="90" align="center">
            <template #default="{row}">
              <el-tag :type="row.mfa_enabled ? 'success' : 'warning'">
                {{ row.mfa_enabled ? '已启用' : '未启用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="控制台访问" width="110" align="center">
            <template #default="{row}">
              <el-tag :type="getConsoleStatusType(row.console_status)" size="small">
                {{ row.console_status || '未知' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="account_name" label="所属账号" min-width="120" sortable />
          <el-table-column prop="email" label="邮箱" min-width="180" sortable />
          <el-table-column prop="mobile_phone" label="手机号" min-width="120" sortable />

          <el-table-column prop="access_keys_count" label="访问密钥" width="90" align="center" sortable />
          <el-table-column label="用户组" min-width="150">
            <template #default="{row}">
              <div v-if="row.groups?.length">
                <el-tag v-for="g in row.groups.slice(0,2)" :key="g.group_name" size="small" class="mr-5">
                  {{ g.group_name }}
                </el-tag>
                <el-tag v-if="row.groups.length>2" size="small">+{{ row.groups.length-2 }}</el-tag>
              </div>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="create_date" label="创建时间" width="160" sortable />
          <el-table-column prop="update_date" label="更新时间" width="160" sortable />
          <el-table-column label="操作" width="120" fixed="right" align="center">
            <template #default="scope">
              <el-button size="small" type="primary" @click="openDetail(scope.row)">
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.pageSize"
          :page-sizes="[10,20,30,50,100]"
          layout="->, total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </el-card>
    </div>

    <!-- ============== 详情页 ============== -->
    <div v-else class="page-detail">
      <!-- 面包屑 -->
      <div class="detail-header">
        <el-breadcrumb separator-class="el-icon-arrow-right">
          <el-breadcrumb-item>
            <a @click="closeDetail">RAM用户管理</a>
          </el-breadcrumb-item>
          <el-breadcrumb-item>用户详情</el-breadcrumb-item>
        </el-breadcrumb>
        <el-button icon="el-icon-back" @click="closeDetail">返回列表</el-button>
      </div>

      <el-card v-loading="detailLoading" shadow="never">
        <template #header>
          <span>RAM用户详情 - {{ ramUserDetail.user_principal_name || ramUserDetail.user_name }}</span>
        </template>

        <el-descriptions title="基本信息" :column="2" border>
          <el-descriptions-item label="用户ID">{{ ramUserDetail.user_id }}</el-descriptions-item>
          <el-descriptions-item label="用户名">{{ ramUserDetail.user_name }}</el-descriptions-item>
          <el-descriptions-item label="登录名称">{{ ramUserDetail.user_principal_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="显示名称">{{ ramUserDetail.display_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="所属账号">{{ ramUserDetail.account_name }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ ramUserDetail.email || '-' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ ramUserDetail.mobile_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="控制台访问状态">
            <el-tag :type="getConsoleStatusType(ramUserDetail.console_status)">
              {{ ramUserDetail.console_status || '未知状态' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="账号状态">
            <el-tag :type="ramUserDetail.active ? 'success' : 'danger'">
              {{ ramUserDetail.active ? '激活' : '禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="MFA状态">
            <el-tag :type="ramUserDetail.mfa_enabled ? 'success' : 'warning'">
              {{ ramUserDetail.mfa_enabled ? '已启用' : '未启用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="访问密钥数量">{{ ramUserDetail.access_keys_count }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(ramUserDetail.create_date) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDateTime(ramUserDetail.update_date) }}</el-descriptions-item>
          <el-descriptions-item label="最后登录时间">{{ formatDateTime(ramUserDetail.last_login_date) || '从未登录' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ ramUserDetail.comments || '-' }}</el-descriptions-item>
        </el-descriptions>

        <!-- AccessKey信息 -->
        <el-divider />
        <h3>访问密钥 (AccessKeys)</h3>
        <el-table
          v-if="ramUserDetail.access_keys && ramUserDetail.access_keys.length"
          :data="ramUserDetail.access_keys"
          stripe
          border
          class="mt-10"
        >
          <el-table-column prop="access_key_id" label="AccessKey ID" min-width="200">
            <template #default="{ row }">
              <span class="access-key-id">{{ row.access_key_id }}</span>
              <el-button
                @click="copyToClipboard(row.access_key_id)"
                size="small"
                link
                type="primary"
                class="ml-5"
              >
                <el-icon><DocumentCopy /></el-icon>
              </el-button>
            </template>
          </el-table-column>

          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag
                :type="row.status === 'Active' ? 'success' : 'danger'"
                size="small"
              >
                {{ row.status === 'Active' ? '已启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="最后使用云服务 / 时间" min-width="180">
            <template #default="{ row }">
              <div v-if="row.last_used_date || row.service_name">
                <div v-if="row.service_name" class="service-name">
                  {{ row.service_name }}
                </div>
                <div v-if="row.last_used_date" class="last-used-time">
                  {{ formatDateTime(row.last_used_date) }}
                </div>
                <div v-else class="no-data">从未使用</div>
              </div>
              <span v-else class="no-data">无使用记录</span>
            </template>
          </el-table-column>

          <el-table-column label="创建时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.create_date) || '-' }}
            </template>
          </el-table-column>

          <el-table-column label="更新时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.update_date) || '-' }}
            </template>
          </el-table-column>

          <el-table-column label="已创建时间" width="120">
            <template #default="{ row }">
              {{ getCreatedTime(row.create_date) }}
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无访问密钥" :image-size="80" />

        <el-divider />
        <h3>用户权限</h3>
        <el-table
          v-if="ramUserDetail.attached_policies?.length"
          :data="ramUserDetail.attached_policies"
          stripe
          border
        >
          <el-table-column prop="policy_name" label="策略名" min-width="150" />
          <el-table-column prop="policy_type" label="类型" width="100" />
          <el-table-column prop="description" label="描述" min-width="200" />
          <el-table-column prop="attach_date" label="附加时间" width="160" />
        </el-table>
        <el-empty v-else description="暂未分配权限" :image-size="80" />
        <el-divider />

        <h3>所属用户组</h3>
        <el-table
          v-if="ramUserDetail.groups?.length"
          :data="ramUserDetail.groups"
          stripe
          border
        >
          <el-table-column prop="group_name" label="组名" min-width="150" />
          <el-table-column prop="comments" label="描述" min-width="200" />
        </el-table>
        <el-empty v-else description="暂无用户组信息" :image-size="80" />

      </el-card>
    </div>
  </div>
</template>


<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessageBox, ElMessage } from "element-plus"
import { handleFileError } from "@/utils/export"
import {
  Search,
  Refresh,
  RefreshRight,
  Download,
  DocumentCopy
} from '@element-plus/icons-vue'
import {
  listRAMUsers,
  syncRAMUsers,
  exportRAMUsers
} from '@/api/aliyun/ramuser'

const loading = ref(false)
const detailLoading = ref(false)
const tableData = ref([])
const total = ref(0)
const accountOptions = ref([])

// 控制台状态标签类型
const getConsoleStatusType = (status) => {
  switch (status) {
    case '已开启':
      return 'success'
    case '已禁用':
      return 'danger'
    case '未开启':
      return 'info'
    case '权限不足':
    case '获取失败':
    case 'API错误':
      return 'warning'
    default:
      return 'warning'
  }
}

const selectedUser = ref(null)
const ramUserDetail = ref({})

// 查询表单引用
const queryFormRef = ref()

// 查询参数
const queryParams = reactive({
  page: 1,
  pageSize: 10,
  search: '',
  display_name: '',
  active: undefined,
  mfa_enabled: undefined,
  account_name: ''
})

// 搜索
const handleQuery = () => {
  queryParams.page = 1
  getList()
}

// 重置查询
const resetQuery = () => {
  queryFormRef.value?.resetFields()
  queryParams.page = 1
  queryParams.pageSize = 10
  queryParams.search = ''
  queryParams.display_name = ''
  queryParams.active = undefined
  queryParams.mfa_enabled = undefined
  queryParams.account_name = ''
  getList()
}

// 复制到剪贴板
const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('AccessKey ID 已复制到剪贴板')
  }).catch(() => {
    const textArea = document.createElement('textarea')
    textArea.value = text
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      ElMessage.success('AccessKey ID 已复制到剪贴板')
    } catch (err) {
      ElMessage.error('复制失败')
    }
    document.body.removeChild(textArea)
  })
}

// 格式化日期时间
const formatDateTime = (dateString) => {
  if (!dateString) return ''
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    return dateString
  }
}

// 计算已创建时间
const getCreatedTime = (createDate) => {
  if (!createDate) return '-'
  try {
    const createTime = new Date(createDate).getTime()
    const now = new Date().getTime()
    const diff = now - createTime
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    const months = Math.floor(days / 30)
    const years = Math.floor(months / 12)

    if (years > 0) return `${years}年`
    if (months > 0) return `${months}个月`
    if (days > 0) return `${days}天`
    return '今天'
  } catch (error) {
    return '-'
  }
}

/* 列表查询 */
const getList = async () => {
  loading.value = true
  try {
    const params = { ...queryParams }
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === undefined) {
        delete params[key]
      }
    })

    const res = await listRAMUsers(params)
    const { code, data, msg } = res || {}
    if (code === 200 && data) {
      tableData.value = data.data || []
      total.value = data.total || 0
      accountOptions.value = [...new Set((data.data || []).map(i => i.account_name))].filter(Boolean)
    } else {
      ElMessage.error(msg || '获取数据失败')
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const openDetail = (row) => {
  selectedUser.value = row
  detailLoading.value = true
  try {
    ramUserDetail.value = { ...row }
  } catch (e) {
    console.error('处理详情数据异常:', e)
    ElMessage.error('展示详情失败')
  } finally {
    detailLoading.value = false
  }
}

const closeDetail = () => {
  selectedUser.value = null
  ramUserDetail.value = {}
}

const handleSync = async () => {
  loading.value = true
  try {
    const res = await syncRAMUsers()
    const { code, msg } = res || {}
    if (code === 200) {
      ElMessage.success(msg || '同步成功')
      getList()
    } else {
      ElMessage.error(msg || '同步失败')
    }
  } catch (error) {
    console.error('同步失败:', error)
    ElMessage.error('同步失败')
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (val) => {
  queryParams.pageSize = val
  queryParams.page = 1
  getList()
}

const handleCurrentChange = (val) => {
  queryParams.page = val
  getList()
}

const exportLoading = ref(false)

const handleExport = async () => {
  try {
    await ElMessageBox.confirm('是否确认导出所有RAM用户数据?', '导出确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    exportLoading.value = true
    const response = await exportRAMUsers({ ...queryParams })

    if (response && response.type === 'application/json') {
      const reader = new FileReader()
      reader.onload = function () {
        try {
          const errorData = JSON.parse(reader.result)
          ElMessage.error(errorData.msg || errorData.error_detail || '导出失败')
        } catch (e) {
          ElMessage.error('导出失败：无法解析错误信息')
        }
      }
      reader.readAsText(response)
    } else if (response) {
      const timestamp = new Date().getTime()
      handleFileError(response, `ram_users_${timestamp}.csv`)
      ElMessage.success('导出成功')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('导出失败:', error)
      ElMessage.error('导出失败')
    }
  } finally {
    exportLoading.value = false
  }
}

onMounted(() => {
  getList()
})

// Clean up state on unmount to prevent memory leaks and white screen issues
onUnmounted(() => {
  selectedUser.value = null
  ramUserDetail.value = {}
  tableData.value = []
  accountOptions.value = []
  loading.value = false
  detailLoading.value = false
  exportLoading.value = false
})
</script>

<style scoped>
.app-container {
  padding: 20px;
}
.mt-10 {
  margin-top: 10px;
}
.ml-5 {
  margin-left: 5px;
}
.mr-5 {
  margin-right: 5px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  background: #fff;
  padding: 10px 15px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,.1);
}

.access-key-id {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  border: 1px solid #e4e7ed;
}

.service-name {
  font-weight: 500;
  color: #409eff;
}

.last-used-time {
  font-size: 12px;
  color: #909399;
}

.no-data {
  color: #c0c4cc;
  font-style: italic;
}

:deep(.el-table .cell) {
  line-height: 1.6;
}

:deep(.el-tag) {
  margin: 2px 0;
}
</style>
