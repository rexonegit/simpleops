<template>
  <div class="baremetal-asset-container">
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="请输入主机名、项目、负责人、IP、序列号"
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

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="card-header">
            <el-icon class="card-icon"><DataAnalysis /></el-icon>
            <span>物理机总数</span>
          </div>
          <div class="card-body">
            <div class="display-4">{{ stats.total }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="card-header">
            <el-icon class="card-icon"><AlarmClock /></el-icon>
            <span>即将过期 (3个月内)</span>
          </div>
          <div class="card-body">
            <div class="display-4 text-warning">{{ stats.expiring_soon }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="card-header">
            <el-icon class="card-icon"><Warning /></el-icon>
            <span>已经过保</span>
          </div>
          <div class="card-body">
            <div class="display-4 text-danger">{{ stats.expired }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;" class="table-card">
      <el-table
        v-loading="listLoading"
        :data="baremetalList"
        style="width: 100%"
        stripe
        border
        :key="tableKey"
      >
        <el-table-column prop="hostname" label="主机名" min-width="150" sortable />
        <el-table-column prop="project" label="项目" min-width="150" sortable />
        <el-table-column prop="environment" label="环境类型" min-width="120" sortable>
          <template #default="{ row }">
            <el-tag :type="getEnvTagType(row.environment)">
              {{ getEnvLabel(row.environment) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" min-width="120" sortable />
        <el-table-column prop="ip_address" label="IP地址" min-width="140" />
        <el-table-column prop="os_info" label="操作系统" min-width="150" sortable />
        <el-table-column prop="hostmodel" label="型号" min-width="150" sortable />
        <el-table-column prop="SerialNumber" label="序列号" min-width="150" sortable />
        <el-table-column prop="ExpressServiceCode" label="快速服务码" min-width="120" sortable />
        <el-table-column prop="cpu" label="CPU" min-width="150" sortable />
        <el-table-column prop="memory" label="内存" min-width="100" sortable />
        <el-table-column prop="disk" label="磁盘" min-width="150" sortable />
        <el-table-column prop="creation_time" label="生产日期" min-width="120" sortable :formatter="formatDate" />
        <el-table-column prop="expire_time" label="保修到期" min-width="120" sortable>
          <template #default="{ row }">
            <span :class="{ 'text-danger': isExpiring(row.expire_time) }">
              {{ formatDate(null, null, row.expire_time) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="DataCenter" label="数据中心" min-width="120" sortable />
        <el-table-column prop="Vendor" label="供应商" min-width="120" sortable />
        <el-table-column prop="description" label="备注" min-width="150" sortable />
        <el-table-column label="操作" width="150" fixed="right">
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
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-dialog :title="editedItem.id ? '编辑物理机' : '新增物理机'" v-model="dialogVisible" width="800px" destroy-on-close>
      <el-form ref="formRef" :model="editedItem" :rules="formRules" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="主机名" prop="hostname">
              <el-input v-model="editedItem.hostname" />
            </el-form-item>
            <el-form-item label="所属项目" prop="project">
              <el-input v-model="editedItem.project" />
            </el-form-item>
            <el-form-item label="环境类型" prop="environment">
              <el-select v-model="editedItem.environment" style="width: 100%">
                <el-option v-for="item in environmentOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="负责人" prop="owner">
              <el-input v-model="editedItem.owner" />
            </el-form-item>
            <el-form-item label="IP地址" prop="ip_address">
              <el-input v-model="editedItem.ip_address" />
            </el-form-item>
            <el-form-item label="操作系统" prop="os_info">
              <el-input v-model="editedItem.os_info" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="型号" prop="hostmodel">
              <el-input v-model="editedItem.hostmodel" />
            </el-form-item>
            <el-form-item label="序列号" prop="SerialNumber">
              <el-input v-model="editedItem.SerialNumber" />
            </el-form-item>
            <el-form-item label="快速服务码" prop="ExpressServiceCode">
              <el-input v-model="editedItem.ExpressServiceCode" />
            </el-form-item>
            <el-form-item label="CPU" prop="cpu">
              <el-input v-model="editedItem.cpu" placeholder="如: 2核 Intel Xeon" />
            </el-form-item>
            <el-form-item label="内存" prop="memory">
              <el-input v-model="editedItem.memory" placeholder="如: 32GB" />
            </el-form-item>
            <el-form-item label="磁盘" prop="disk">
              <el-input v-model="editedItem.disk" placeholder="如: 2x1TB SSD" />
            </el-form-item>
            <el-form-item label="生产日期" prop="creation_time">
              <el-date-picker v-model="editedItem.creation_time" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
            <el-form-item label="保修到期" prop="expire_time">
              <el-date-picker v-model="editedItem.expire_time" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
            <el-form-item label="数据中心" prop="DataCenter">
              <el-input v-model="editedItem.DataCenter" />
            </el-form-item>
            <el-form-item label="供应商" prop="Vendor">
              <el-input v-model="editedItem.Vendor" placeholder="如: DELL HPE" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注" prop="description">
          <el-input v-model="editedItem.description" type="textarea" :rows="3" placeholder="附加说明信息" />
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
          确定要删除物理机 <strong>{{ deleteItemData.hostname }}</strong> 吗？
        </span>
      </div>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmDelete">确认删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Plus, DataAnalysis, AlarmClock, Warning, Edit, Delete } from '@element-plus/icons-vue'
import {
  listProjectBareMetal,
  createProjectBareMetal,
  updateProjectBareMetal,
  deleteProjectBareMetal
} from '@/api/datacenter/projectbaremetal'

const tableKey = ref(0)
const listLoading = ref(true)
const baremetalList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')

const stats = ref({
  total: 0,
  expiring_soon: 0,
  expired: 0
})

const dialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const deleteItemData = ref({})

const editedItem = ref({
  id: null,
  hostname: '',
  project: '',
  environment: 'prod',
  owner: '',
  ip_address: '',
  os_info: '',
  hostmodel: '',
  SerialNumber: '',
  cpu: '',
  memory: '',
  disk: '',
  creation_time: null,
  expire_time: null,
  description: '',
  DataCenter: '',
  Vendor: '',
  ExpressServiceCode: ''
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

const formRef = ref(null)
const formRules = {
  hostname: [{ required: true, message: '主机名不能为空', trigger: 'blur' }],
  project: [{ required: true, message: '所属项目不能为空', trigger: 'blur' }],
  environment: [{ required: true, message: '请选择环境类型', trigger: 'change' }],
  owner: [{ required: true, message: '负责人不能为空', trigger: 'blur' }]
}

const fetchData = async () => {
  listLoading.value = true
  try {
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value,
      search: searchQuery.value
    }
    const res = await listProjectBareMetal(params)
    const payload = res.data || res
    const listData = payload.results || payload.list || payload.data || []
    baremetalList.value = listData
    total.value = payload.count || payload.total || listData.length
    
    // 简易统计计算
    stats.value.total = total.value
    stats.value.expiring_soon = calculateExpiringSoon(listData)
    stats.value.expired = calculateExpired(listData)
  } catch (err) {
    console.error('数据加载失败', err)
    ElMessage.error('数据加载失败')
    baremetalList.value = []
  } finally {
    listLoading.value = false
    tableKey.value++
  }
}

const calculateExpiringSoon = (list) => {
  return list.filter(item => {
    if (!item.expire_time) return false
    const expireDate = new Date(item.expire_time)
    const today = new Date()
    const daysLeft = Math.ceil((expireDate - today) / (1000 * 3600 * 24))
    return daysLeft > 0 && daysLeft <= 90
  }).length
}

const calculateExpired = (list) => {
  return list.filter(item => {
    if (!item.expire_time) return false
    const expireDate = new Date(item.expire_time)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    expireDate.setHours(0, 0, 0, 0)
    return expireDate < today
  }).length
}

const isExpiring = (dateStr) => {
  if (!dateStr) return false
  const expireDate = new Date(dateStr)
  const daysLeft = Math.ceil((expireDate - Date.now()) / (1000 * 3600 * 24))
  return daysLeft > 0 && daysLeft <= 30
}

const getEnvLabel = (value) => {
  return environmentOptions.find(e => e.value === value)?.label || value
}

const getEnvTagType = (env) => {
  const map = {
    'prod': 'danger', 'test': 'warning', 'dev': 'success',
    'uat': 'primary', 'stg': 'info', 'dr': 'danger', 'other': 'info'
  }
  return map[env] || 'info'
}

const formatDate = (_, __, cellValue) => {
  if (!cellValue) return '-'
  try {
    const date = new Date(cellValue)
    if (isNaN(date.getTime())) return cellValue
    return date.toISOString().split('T')[0]
  } catch {
    return cellValue
  }
}

const handleSearch = () => { currentPage.value = 1; fetchData() }
const handleSizeChange = (val) => { pageSize.value = val; fetchData() }
const handleCurrentChange = (val) => { currentPage.value = val; fetchData() }

const openDialog = (item) => {
  editedItem.value = item ? { ...item } : {
    id: null, hostname: '', project: '', environment: 'prod', owner: '',
    ip_address: '', os_info: '', hostmodel: '', SerialNumber: '', cpu: '', memory: '', disk: '',
    creation_time: null, expire_time: null, description: '', DataCenter: '', Vendor: '', ExpressServiceCode: ''
  }
  dialogVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

const closeDialog = () => { dialogVisible.value = false }

const save = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      if (editedItem.value.id) {
        await updateProjectBareMetal(editedItem.value.id, editedItem.value)
        ElMessage.success('更新成功')
      } else {
        await createProjectBareMetal(editedItem.value)
        ElMessage.success('创建成功')
      }
      closeDialog()
      fetchData()
    } catch (err) {
      ElMessage.error(err?.response?.data?.detail || '操作失败')
    }
  })
}

const deleteItem = (item) => { deleteItemData.value = { ...item }; deleteDialogVisible.value = true }

const confirmDelete = async () => {
  try {
    await deleteProjectBareMetal(deleteItemData.value.id)
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
.baremetal-asset-container { padding: 20px; background-color: #f5f7fa; }
.search-bar { display: flex; align-items: center; margin-bottom: 10px; }
.card-icon { font-size: 20px; margin-right: 8px; }
.stat-card { border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); transition: all 0.3s; }
.stat-card:hover { transform: translateY(-5px); box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15); }
.card-header { display: flex; align-items: center; margin-bottom: 10px; color: #606266; }
.card-body { text-align: center; }
.display-4 { font-size: 28px; font-weight: bold; color: #409EFF; }
.text-warning { color: #e6a23c; }
.text-danger { color: #f56c6c; }
.table-card { border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); }
.pagination-container { margin-top: 20px; display: flex; justify-content: flex-end; }
</style>
