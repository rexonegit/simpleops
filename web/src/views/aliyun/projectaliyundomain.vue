<template>
  <div class="domain-container">
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="请输入完整域名、项目或负责人"
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
            <span>域名记录总数</span>
          </div>
          <div class="card-body">
            <div class="display-4">{{ stats.total }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="card-header">
            <el-icon class="card-icon"><Setting /></el-icon>
            <span>记录类型分布</span>
          </div>
          <div class="card-body" style="line-height: 1.8;">
            <div v-for="(count, type) in stats.type_counts" :key="type">
              {{ getTypeLabel(type) }}：{{ count }}
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;" class="table-card">
      <el-table
        v-loading="listLoading"
        :data="domainList"
        style="width: 100%"
        stripe
        border
        :key="tableKey"
      >
        <el-table-column prop="complete_domain" label="完整域名" min-width="220" sortable />
        <el-table-column prop="type" label="记录类型" min-width="120" sortable :formatter="formatType" />
        <el-table-column prop="rr" label="主机记录" min-width="160" sortable />
        <el-table-column prop="project" label="所属项目" min-width="160" sortable />
        <el-table-column prop="environment" label="环境类型" width="120" sortable sort-by="environment">
          <template #default="{ row }">
            <el-tag :type="envTagType(row.environment)" size="small">
              {{ getEnvLabel(row.environment) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" min-width="150" sortable />
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
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-dialog :title="editedItem.id ? '编辑记录' : '新增记录'" v-model="dialogVisible" width="700px" destroy-on-close>
      <el-form ref="formRef" :model="editedItem" :rules="formRules" label-width="120px">
        <el-form-item label="完整域名" prop="complete_domain">
          <el-input v-model="editedItem.complete_domain" />
        </el-form-item>
        <el-form-item label="记录类型" prop="type">
          <el-select v-model="editedItem.type" style="width: 100%">
            <el-option v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="主机记录" prop="rr">
          <el-input v-model="editedItem.rr" />
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
        <el-form-item label="描述">
          <el-input v-model="editedItem.description" type="textarea" :rows="3" />
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
        <span style="vertical-align: middle; margin-left: 10px;">确定要删除域名记录 <strong>{{ deleteItemData.complete_domain }}</strong> 吗？</span>
      </div>
      <div style="color: #909399; font-size: 14px; margin-left: 34px;">此操作不可恢复，请谨慎操作！</div>
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
import { Search, Plus, DataAnalysis, Setting, Edit, Delete, Warning } from '@element-plus/icons-vue'
import { listProjectAliyunDomain, createProjectAliyunDomain, updateProjectAliyunDomain, deleteProjectAliyunDomain } from '@/api/aliyun/projectaliyundomain'

const tableKey = ref(0)
const listLoading = ref(true)
const domainList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')

const stats = ref({ total: 0, type_counts: {} })

const dialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const deleteItemData = ref({})

const editedItem = ref({
  id: null,
  complete_domain: '',
  type: 'A',
  rr: '',
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

const typeOptions = [
  { label: 'A记录', value: 'A' },
  { label: 'CNAME记录', value: 'CNAME' },
  { label: 'MX记录', value: 'MX' },
  { label: 'TXT记录', value: 'TXT' },
  { label: 'NS记录', value: 'NS' },
  { label: 'SRV记录', value: 'SRV' },
  { label: 'AAAA记录', value: 'AAAA' },
  { label: 'CAA记录', value: 'CAA' }
]

const formRef = ref(null)
const formRules = {
  complete_domain: [{ required: true, message: '完整域名不能为空', trigger: 'blur' }],
  type: [{ required: true, message: '请选择记录类型', trigger: 'change' }],
  rr: [{ required: true, message: '主机记录不能为空', trigger: 'blur' }],
  project: [{ required: true, message: '所属项目不能为空', trigger: 'blur' }],
  environment: [{ required: true, message: '请选择环境类型', trigger: 'change' }],
  owner: [{ required: true, message: '负责人不能为空', trigger: 'blur' }]
}

const fetchData = async () => {
  listLoading.value = true
  try {
    const params = { page: currentPage.value, pageSize: pageSize.value, search: searchQuery.value }
    const res = await listProjectAliyunDomain(params)
    if (res.code === 200) {
      domainList.value = res.data.data || []
      total.value = res.data.total || 0
    } else {
      domainList.value = []
      total.value = 0
    }
    stats.value = { total: total.value, type_counts: calculateTypeCounts() }
  } catch (e) {
    ElMessage.error('数据加载失败')
    domainList.value = []
    total.value = 0
  } finally {
    listLoading.value = false
    tableKey.value++
  }
}

const calculateTypeCounts = () => {
  return domainList.value.reduce((acc, cur) => {
    const type = cur.type || '未分类'
    acc[type] = (acc[type] || 0) + 1
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

const getTypeLabel = (type) => {
  const opt = typeOptions.find(o => o.value === type)
  return opt ? opt.label : type
}

const formatType = (_, __, cellValue) => getTypeLabel(cellValue)

const handleSearch = () => { currentPage.value = 1; fetchData() }
const handleSizeChange = (val) => { pageSize.value = val; fetchData() }
const handleCurrentChange = (val) => { currentPage.value = val; fetchData() }

const openDialog = (item) => {
  editedItem.value = item ? { ...item } : {
    id: null, complete_domain: '', type: 'A', rr: '', project: '', environment: 'prod', owner: '', description: ''
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
        await updateProjectAliyunDomain(editedItem.value.id, editedItem.value)
        ElMessage.success('更新成功')
      } else {
        await createProjectAliyunDomain(editedItem.value)
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
    await deleteProjectAliyunDomain(deleteItemData.value.id)
    ElMessage.success('删除成功')
    deleteDialogVisible.value = false
    fetchData()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => { fetchData() })
</script>

<style scoped>
.domain-container { padding: 20px; }
.search-bar { display: flex; align-items: center; margin-bottom: 10px; }
.card-icon { font-size: 20px; margin-right: 8px; }
.stat-card { border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); transition: all 0.3s; }
.stat-card:hover { transform: translateY(-5px); box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15); }
.card-header { display: flex; align-items: center; margin-bottom: 10px; color: #606266; }
.card-body { text-align: center; }
.display-4 { font-size: 28px; font-weight: bold; color: #409EFF; }
.table-card { border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); }
.pagination-container { margin-top: 20px; display: flex; justify-content: flex-end; }
</style>

