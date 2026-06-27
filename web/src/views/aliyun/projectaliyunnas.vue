<template>
  <div class="aliyun-container">
    <!-- 搜索 + 新建按钮 -->
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="请输入文件系统名称、项目或负责人"
        clearable
        style="width: 300px; margin-right: 10px;"
        @keyup.enter="handleSearch"
      />
      <el-button type="primary" @click="handleSearch">
        <el-icon style="margin-right: 4px;"><Search /></el-icon>搜索
      </el-button>
      <el-button type="primary" @click="openDialog(null)">
        <el-icon style="margin-right: 4px;"><Plus /></el-icon>新建
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="card-header">
            <el-icon class="card-icon"><DataAnalysis /></el-icon>
            <span>NAS总数</span>
          </div>
          <div class="card-body">
            <div class="display-4">{{ stats.total }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col v-for="(count, env) in stats.env_counts" :key="env" :span="6">
        <el-card class="stat-card">
          <div class="card-header">
            <el-icon class="card-icon"><Setting /></el-icon>
            <span>{{ getEnvLabel(env) }}</span>
          </div>
          <div class="card-body">
            <div class="display-4">{{ count }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据表格 -->
    <el-card style="margin-top: 20px;" class="table-card">
      <el-table
        v-loading="listLoading"
        :data="vmList"
        style="width: 100%"
        stripe
        border
        :key="tableKey"
      >
        <el-table-column prop="file_system_name" label="文件系统名称" min-width="200" sortable />
        <el-table-column prop="project" label="所属项目" min-width="180" sortable />
        <el-table-column prop="environment" label="环境类型" width="120" sortable sort-by="environment">
          <template #default="{ row }">
            <el-tag :type="envTagType(row.environment)" size="mini">
              {{ getEnvLabel(row.environment) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" min-width="120" sortable />
        <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" min-width="170" sortable :formatter="formatDate" />
        <el-table-column prop="updated_at" label="更新时间" min-width="170" sortable :formatter="formatDate" />
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

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          :current-page="currentPage"
          :page-sizes="[10, 20, 50, 100, 200]"
          :page-size="pageSize"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      :title="editedItem.id ? '编辑' : '新建'"
      v-model="dialogVisible"
      width="600px"
      destroy-on-close
    >
      <el-form ref="vmForm" :model="editedItem" :rules="formRules" label-width="120px">
        <el-form-item label="文件系统名称" prop="file_system_name">
          <el-input v-model="editedItem.file_system_name" placeholder="请输入NAS文件系统名称" />
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
        <el-form-item label="说明" prop="description">
          <el-input v-model="editedItem.description" type="textarea" :rows="3" placeholder="请输入NAS文件系统说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 删除确认对话框 -->
    <el-dialog
      title="删除确认"
      v-model="deleteDialogVisible"
      width="500px"
      destroy-on-close
    >
      <div style="margin-bottom: 20px;">
        <el-icon style="color: #E6A23C; font-size: 24px; vertical-align: middle;"><Warning /></el-icon>
        <span style="vertical-align: middle; margin-left: 10px;">
          确定要删除NAS文件系统 <strong>{{ deleteItemData.file_system_name }}</strong> 吗？
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
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, DataAnalysis, Setting, Edit, Delete, Warning } from '@element-plus/icons-vue'
import {
  listProjectAliyunNAS,
  createProjectAliyunNAS,
  updateProjectAliyunNAS,
  deleteProjectAliyunNAS
} from '@/api/aliyun/nas'

const tableKey = ref(0)
const listLoading = ref(true)
const vmList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')

const stats = ref({
  total: 0,
  env_counts: {}
})

const dialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const deleteItemData = ref({})

const editedItem = ref({
  id: null,
  file_system_name: '',
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

const formRules = {
  file_system_name: [
    { required: true, message: '文件系统名称不能为空', trigger: 'blur' },
    { min: 1, max: 255, message: '长度在 1 到 255 个字符', trigger: 'blur' }
  ],
  project: [{ required: true, message: '所属项目不能为空', trigger: 'blur' }],
  environment: [{ required: true, message: '请选择环境类型', trigger: 'change' }],
  owner: [{ required: true, message: '负责人不能为空', trigger: 'blur' }]
}

const vmForm = ref(null)

const fetchData = async () => {
  listLoading.value = true
  try {
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value,
      search: searchQuery.value
    }

    const res = await listProjectAliyunNAS(params)
    
    if (res.code === 200) {
      vmList.value = res.data.data || []
      total.value = res.data.total || 0
    } else {
      vmList.value = []
      total.value = 0
    }

    stats.value = {
      total: total.value,
      env_counts: calculateEnvCounts()
    }
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

const calculateEnvCounts = () => {
  return vmList.value.reduce((acc, vm) => {
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
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const handleSearch = () => {
  currentPage.value = 1
  fetchData()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  fetchData()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchData()
}

const openDialog = (item) => {
  editedItem.value = item ? { ...item } : {
    id: null, file_system_name: '', project: '', environment: 'prod', owner: '', description: ''
  }
  dialogVisible.value = true
  nextTick(() => vmForm.value?.clearValidate())
}

const closeDialog = () => {
  dialogVisible.value = false
}

const save = () => {
  vmForm.value.validate(async (valid) => {
    if (!valid) return
    try {
      if (editedItem.value.id) {
        await updateProjectAliyunNAS(editedItem.value.id, editedItem.value)
        ElMessage.success('更新成功')
      } else {
        await createProjectAliyunNAS(editedItem.value)
        ElMessage.success('创建成功')
      }
      closeDialog()
      fetchData()
    } catch (err) {
      ElMessage.error(err.response?.data?.detail || '操作失败')
    }
  })
}

const deleteItem = (item) => {
  deleteItemData.value = { ...item }
  deleteDialogVisible.value = true
}

const confirmDelete = async () => {
  try {
    await deleteProjectAliyunNAS(deleteItemData.value.id)
    ElMessage.success('删除成功')
    deleteDialogVisible.value = false
    fetchData()
  } catch (err) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchData()
})

onBeforeUnmount(() => {
  dialogVisible.value = false
  deleteDialogVisible.value = false
  listLoading.value = false
})
</script>

<style scoped>
.aliyun-container {
  padding: 20px;
  background-color: #f5f7fa;
}

.search-bar {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.card-icon {
  font-size: 20px;
  margin-right: 8px;
}

.stat-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  color: #606266;
}

.card-body {
  text-align: center;
}

.display-4 {
  font-size: 28px;
  font-weight: bold;
  color: #409EFF;
}

.table-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
