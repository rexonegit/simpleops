<template>
  <div class="proxmox-container">
        <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="请输入主机名、VMID、项目或负责人"
        clearable
        style="width: 300px; margin-right: 10px;"
        @keyup.enter="handleSearch"
      />
      <el-button type="primary" @click="handleSearch">
        <el-icon style="margin-right: 4px;"><Search /></el-icon>搜索
      </el-button>
      <el-button type="primary" @click="openDialog(null)" style="margin-left: 8px;">
        <el-icon style="margin-right: 4px;"><Plus /></el-icon>新建
      </el-button>
    </div>

    <!-- 紧凑的统计徽章区域 -->
    <el-card style="margin-top: 20px; padding: 15px;">
      <div class="stats-container">
        <!-- 虚拟机总数徽章 -->
        <el-badge :value="stats.total" class="stat-badge" type="info">
          <el-tag size="large" effect="plain">虚拟机总数</el-tag>
        </el-badge>

        <!-- 各环境统计徽章 -->
        <el-badge
          v-for="(count, env) in stats.env_counts"
          :key="env"
          :value="count"
          class="stat-badge"
          :type="envBadgeType(env)"
        >
          <el-tag size="large" effect="plain">{{ getEnvLabel(env) }}</el-tag>
        </el-badge>
      </div>
    </el-card>

    <el-card style="margin-top: 20px;" class="table-card">
      <el-table
        v-loading="listLoading"
        :data="vmList"
        style="width: 100%"
        stripe
        border
        :key="tableKey"
      >
        <el-table-column prop="hostname" label="主机名" min-width="180" sortable />
        <el-table-column prop="vmid" label="VMID" width="100" sortable />
        <el-table-column prop="project" label="所属项目" min-width="180" sortable />
        <el-table-column prop="environment" label="环境类型" width="120" sortable sort-by="environment">
          <template #default="{ row }">
            <el-tag :type="envTagType(row.environment)" size="small">
              {{ getEnvLabel(row.environment) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" min-width="120" sortable />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" min-width="160" sortable :formatter="formatDate" />
        <el-table-column prop="updated_at" label="更新时间" min-width="160" sortable :formatter="formatDate" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="openDialog(row)">
              <el-icon style="margin-right: 2px;"><Edit /></el-icon>编辑
            </el-button>
            <el-button type="text" size="small" style="color: #F56C6C;" @click="deleteItem(row)">
              <el-icon style="margin-right: 2px;"><Delete /></el-icon>删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          :current-page="currentPage"
          :page-sizes="[10, 20, 50, 100, 200, 300, 'all']"
          :page-size="displayPageSize"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-dialog :title="editedItem.id ? '编辑虚拟机' : '新建虚拟机'" v-model="dialogVisible" width="600px" destroy-on-close>
  <el-form ref="vmForm" :model="editedItem" :rules="formRules" label-width="120px">
    <el-form-item label="主机名" prop="hostname">
      <el-input v-model="editedItem.hostname" placeholder="请输入唯一主机名" />
    </el-form-item>

    <el-form-item label="VMID" prop="vmid">
      <el-input v-model="editedItem.vmid" placeholder="请输入Proxmox VMID" />
      <div class="vmid-hint">
        <el-alert
          :closable="false"
          type="info"
          show-icon
          :style="{ padding: '8px 16px', marginTop: '8px' }"
        >
          <template #title>
            <div style="font-size: 13px; line-height: 1.5;">
              <div style="margin-bottom: 4px; font-weight: 500;">VMID 全局唯一，不可重复，按环境分段：</div>
              <div class="vmid-ranges">
                <el-tag size="small" type="danger" effect="plain">生产 1001+</el-tag>
                <el-tag size="small" type="warning" effect="plain">预生产 2001+</el-tag>
                <el-tag size="small" type="primary" effect="plain">UAT 3001+</el-tag>
                <el-tag size="small" type="primary" effect="plain">测试 4001+</el-tag>
                <el-tag size="small" type="success" effect="plain">开发 5001+</el-tag>
                <el-tag size="small" effect="info">其他 6001+</el-tag>
              </div>
            </div>
          </template>
        </el-alert>
      </div>
    </el-form-item>

    <el-form-item label="所属项目" prop="project">
      <el-input v-model="editedItem.project" placeholder="请输入项目名称" />
    </el-form-item>

    <el-form-item label="环境类型" prop="environment">
      <el-select v-model="editedItem.environment" placeholder="请选择环境类型" style="width: 100%">
        <el-option
          v-for="item in environmentOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
    </el-form-item>

    <el-form-item label="负责人" prop="owner">
      <el-input v-model="editedItem.owner" placeholder="请输入负责人姓名" />
    </el-form-item>

    <el-form-item label="描述" prop="description">
      <el-input v-model="editedItem.description" type="textarea" :rows="3" placeholder="请输入描述信息" />
    </el-form-item>
  </el-form>

  <template #footer>
    <el-button @click="closeDialog">取消</el-button>
    <el-button type="primary" @click="save">保存</el-button>
  </template>
</el-dialog>

    <el-dialog title="删除确认" v-model="deleteDialogVisible" width="500px" destroy-on-close>
      <div style="margin-bottom: 20px;">
        <el-icon style="color: #E6A23C; font-size: 24px; vertical-align: middle;"><Warning /></el-icon>
        <span style="vertical-align: middle; margin-left: 10px;">
          确定要删除虚拟机 <strong>{{ deleteItemData.hostname }}</strong> 吗？
        </span>
      </div>
      <div style="color: #909399; font-size: 14px; margin-left: 34px;">
        此操作不可恢复，请谨慎操作！
      </div>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmDelete">确认删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Plus, DataAnalysis, Setting, Edit, Delete, Warning } from '@element-plus/icons-vue'
import {
  listProjectProxmox,
  createProjectProxmox,
  updateProjectProxmox,
  deleteProjectProxmox
} from '@/api/datacenter/projectproxmox'

const tableKey = ref(0)
const listLoading = ref(true)
const vmList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const displayPageSize = ref(10)
const searchQuery = ref('')

const envBadgeType = (envCode) => {
  const map = {
    prod: 'danger',
    stg: 'warning',
    dr: 'warning',
    uat: 'primary',
    test: 'primary',
    dev: 'success',
    other: 'info'
  }
  return map[envCode] || 'info'
}

const stats = ref({
  total: 0,
  env_counts: {}
})

const dialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const deleteItemData = ref({})

const editedItem = ref({
  id: null,
  hostname: '',
  vmid: '',
  project: '',
  environment: 'prod',
  owner: '',
  description: ''
})

const environmentOptions = [
  { label: '生产环境', value: 'prod' },
  { label: '测试环境', value: 'test' },
  { label: '开发环境', value: 'dev' },
  { label: '用户验收环境', value: 'uat' },
  { label: '预生产环境', value: 'stg' },
  { label: '灾备环境', value: 'dr' },
  { label: '其他', value: 'other' }
]

const vmForm = ref(null)
const formRules = {
  hostname: [
    { required: true, message: '主机名不能为空', trigger: 'blur' },
    { min: 3, max: 255, message: '长度在 3 到 255 个字符', trigger: 'blur' }
  ],
  vmid: [{ required: true, message: 'VMID不能为空', trigger: 'blur' }],
  project: [{ required: true, message: '所属项目不能为空', trigger: 'blur' }],
  environment: [{ required: true, message: '请选择环境类型', trigger: 'change' }],
  owner: [{ required: true, message: '负责人不能为空', trigger: 'blur' }]
}

const fetchData = async () => {
  listLoading.value = true
  try {
    const params = {
      page: pageSize.value === 'all' ? 1 : currentPage.value,
      pageSize: pageSize.value,
      search: searchQuery.value
    }

    const res = await listProjectProxmox(params)
    const payload = res.data || res

    if (pageSize.value === 'all') {
      vmList.value = Array.isArray(payload) ? payload : (payload.results || payload.list || [])
      total.value = vmList.value.length
      displayPageSize.value = total.value
    } else {
      vmList.value = payload.results || payload.list || payload.data || []
      total.value = payload.count || payload.total || vmList.value.length
      displayPageSize.value = pageSize.value
    }

    // 获取统计
    await fetchStats()
  } catch (err) {
    console.error('数据加载失败:', err)
    ElMessage.error('数据加载失败')
    vmList.value = []
    total.value = 0
  } finally {
    listLoading.value = false
    tableKey.value++
  }
}

// 修改fetchStats确保数据正确
const fetchStats = async () => {
  try {
    const params = { page: 1, pageSize: 9999, search: searchQuery.value }
    const res = await listProjectProxmox(params)
    const payload = res.data || res
    const allData = Array.isArray(payload)
      ? payload
      : (payload.results || payload.list || payload.data || [])

    stats.value = {
      total: allData.length,
      env_counts: calculateEnvCounts(allData)
    }
  } catch (e) {
    console.error('统计失败:', e)
    ElMessage.error('统计加载失败')
    stats.value = { total: 0, env_counts: {} }
  }
}

const calculateEnvCounts = (data) => {
  return data.reduce((acc, vm) => {
    const env = vm.environment || 'other'
    acc[env] = (acc[env] || 0) + 1
    return acc
  }, {})
}

const getEnvLabel = (value) => {
  return environmentOptions.find(e => e.value === value)?.label || value
}

const envTagType = (envCode) => {
  const map = { prod: 'danger', stg: 'warning', dr: 'warning', uat: 'primary', test: 'primary', dev: 'success', other: 'info' }
  return map[envCode] || 'info'
}

const formatDate = (_, __, cellValue) => {
  if (!cellValue) return '-'
  return new Date(cellValue).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
  })
}

const handleSearch = () => { currentPage.value = 1; fetchData() }
const handleSizeChange = (val) => {
  if (val === 'all') {
    pageSize.value = 'all'
  } else {
    pageSize.value = val
  }
  currentPage.value = 1
  fetchData()
}
const handleCurrentChange = (val) => { currentPage.value = val; fetchData() }

const openDialog = (item) => {
  editedItem.value = item ? { ...item } : {
    id: null, hostname: '', vmid: '', project: '', environment: 'prod', owner: '', description: ''
  }
  dialogVisible.value = true
  nextTick(() => vmForm.value?.clearValidate())
}

const closeDialog = () => { dialogVisible.value = false }

const save = () => {
  vmForm.value.validate(async (valid) => {
    if (!valid) return
    try {
      if (editedItem.value.id) {
        await updateProjectProxmox(editedItem.value.id, editedItem.value)
        ElMessage.success('更新成功')
      } else {
        await createProjectProxmox(editedItem.value)
        ElMessage.success('创建成功')
      }
      closeDialog()
      fetchData()
    } catch (err) {
      // 处理后端返回的错误信息
      const errData = err?.response?.data
      if (errData) {
        // 处理字段级别的错误（如 vmid 重复）
        if (errData.vmid) {
          const vmidError = Array.isArray(errData.vmid) ? errData.vmid[0] : errData.vmid
          ElMessage.error(vmidError)
        } else if (errData.hostname) {
          const hostnameError = Array.isArray(errData.hostname) ? errData.hostname[0] : errData.hostname
          ElMessage.error(hostnameError)
        } else if (errData.detail) {
          ElMessage.error(errData.detail)
        } else if (errData.non_field_errors) {
          const nonFieldError = Array.isArray(errData.non_field_errors) ? errData.non_field_errors[0] : errData.non_field_errors
          ElMessage.error(nonFieldError)
        } else {
          // 尝试提取第一个错误信息
          const firstKey = Object.keys(errData)[0]
          if (firstKey) {
            const firstError = Array.isArray(errData[firstKey]) ? errData[firstKey][0] : errData[firstKey]
            ElMessage.error(firstError)
          } else {
            ElMessage.error('操作失败')
          }
        }
      } else {
        ElMessage.error('操作失败')
      }
    }
  })
}

const deleteItem = (item) => { deleteItemData.value = { ...item }; deleteDialogVisible.value = true }

const confirmDelete = async () => {
  try {
    await deleteProjectProxmox(deleteItemData.value.id)
    ElMessage.success('删除成功')
    deleteDialogVisible.value = false
    fetchData()
  } catch (err) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => { fetchData() })
</script>

<style scoped>
<style scoped>
.proxmox-container { padding: 20px; background-color: #f5f7fa; }
.search-bar { display: flex; align-items: center; margin-bottom: 10px; }

/* 新增：统计徽章容器样式 */
.stats-container {
  display: flex;
  flex-wrap: wrap;
  gap: 40px;
  align-items: center;
  justify-content: flex-start;
}

/* 新增：单个统计徽章样式 */
.stat-badge {
  margin: 0;
}



.table-card { border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); }
.pagination-container { margin-top: 20px; display: flex; justify-content: flex-end; }

/* 响应式设计：小屏幕时调整间距 */
@media (max-width: 768px) {
  .stats-container {
    gap: 15px;
  }
  .stat-badge:deep(.el-tag) {
    font-size: 13px;
    padding: 0 10px;
  }
}
.search-bar { display: flex; align-items: center; margin-bottom: 10px; }
.card-icon { font-size: 20px; margin-right: 8px; }
.stat-card { border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); transition: all 0.3s; }
.stat-card:hover { transform: translateY(-5px); box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15); }
.card-header { display: flex; align-items: center; margin-bottom: 10px; color: #606266; }
.card-body { text-align: center; }
.display-4 { font-size: 28px; font-weight: bold; color: #409EFF; }
.table-card { border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); }
.pagination-container { margin-top: 20px; display: flex; justify-content: flex-end; }
.vmid-hint {
  width: 100%;
}

.vmid-ranges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}
</style>
