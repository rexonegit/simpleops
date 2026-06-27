<template>
  <div class="database-container">
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="请输入实例名、项目、负责人、主机地址、数据库名"
        clearable
        style="width: 350px; margin-right: 10px;"
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
            <span>数据库总数</span>
          </div>
          <div class="card-body">
            <div class="display-4">{{ stats.total }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="card-header">
            <el-icon class="card-icon"><Collection /></el-icon>
            <span>生产环境</span>
          </div>
          <div class="card-body">
            <div class="display-4 text-primary">{{ stats.prod_count }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="card-header">
            <el-icon class="card-icon"><Cpu /></el-icon>
            <span>Oracle</span>
          </div>
          <div class="card-body">
            <div class="display-4 text-info">{{ stats.oracle_count }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="card-header">
            <el-icon class="card-icon"><Menu /></el-icon>
            <span>MySQL</span>
          </div>
          <div class="card-body">
            <div class="display-4 text-success">{{ stats.mysql_count }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;" class="table-card">
      <el-table
        v-loading="listLoading"
        :data="databaseList"
        style="width: 100%"
        stripe
        border
        :key="tableKey"
      >
        <el-table-column prop="project" label="所属项目" min-width="150" sortable />
        <el-table-column prop="environment" label="环境类型" min-width="120" sortable>
          <template #default="{ row }">
            <el-tag :type="getEnvTagType(row.environment)" size="small">
              {{ getEnvLabel(row.environment) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" min-width="120" sortable />
        <el-table-column prop="name" label="数据库名称" min-width="180" sortable fixed="left" />
        <el-table-column prop="db_type" label="数据库类型" min-width="120" sortable>
          <template #default="{ row }">
            <el-tag :type="getDbTypeTag(row.db_type)" size="small">
              {{ getDbTypeLabel(row.db_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" min-width="100" />
        <el-table-column prop="host" label="主机地址" min-width="150" />
        <el-table-column prop="port" label="端口" min-width="80" />
        <el-table-column prop="instance" label="实例名/SID" min-width="120" />
        <el-table-column prop="db_name" label="数据库名/PDB" min-width="120" />
        <el-table-column prop="charset" label="字符集" min-width="100" />
        <el-table-column prop="description" label="备注" min-width="200" show-overflow-tooltip />
        <el-table-column prop="updated_at" label="更新时间" min-width="160" sortable :formatter="formatDate" />
        <el-table-column label="操作" width="260">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="openDetailDialog(row)">
              <el-icon style="margin-right: 2px;"><View /></el-icon>详情
            </el-button>
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

    <!-- 详情弹窗 -->
  <el-dialog
    title="数据库实例详情"
    v-model="detailDialogVisible"
    width="900px"
    top="5vh"
    destroy-on-close
    class="detail-dialog"
  >
    <div class="detail-container" v-if="detailData">
      <!-- 基本信息 -->
      <el-descriptions :column="3" border class="detail-section">
        <template #title>
          <div class="section-header">
            <el-icon><InfoFilled /></el-icon>
            <span>基本信息</span>
          </div>
        </template>
        <el-descriptions-item label="实例名称">
          <div class="copyable">
            <span>{{ detailData.name }}</span>
            <el-icon @click="copyToClipboard(detailData.name)"><CopyDocument /></el-icon>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="数据库类型">
          <el-tag :type="getDbTypeTag(detailData.db_type)" size="small">
            {{ getDbTypeLabel(detailData.db_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="版本">{{ detailData.version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="所属项目">
          <div class="copyable">
            <span>{{ detailData.project }}</span>
            <el-icon @click="copyToClipboard(detailData.project)"><CopyDocument /></el-icon>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="环境类型">
          <el-tag :type="getEnvTagType(detailData.environment)" size="small">
            {{ getEnvLabel(detailData.environment) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="负责人">
          <el-tag size="small">{{ detailData.owner }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 连接配置 -->
      <el-descriptions :column="3" border class="detail-section">
        <template #title>
          <div class="section-header">
            <el-icon><Connection /></el-icon>
            <span>连接配置</span>
          </div>
        </template>
        <el-descriptions-item label="主机地址">
          <div class="copyable">
            <span>{{ detailData.host }}</span>
            <el-icon @click="copyToClipboard(detailData.host)"><CopyDocument /></el-icon>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="端口">{{ detailData.port }}</el-descriptions-item>
        <el-descriptions-item label="实例名/SID">{{ detailData.instance || '-' }}</el-descriptions-item>
        <el-descriptions-item label="数据库名/PDB">{{ detailData.db_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="字符集">
          <el-tag size="small">{{ detailData.charset || '默认' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="连接状态">
          <el-tag type="success" size="small">正常</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 资源配置 -->
      <el-descriptions :column="3" border class="detail-section">
        <template #title>
          <div class="section-header">
            <el-icon><Monitor /></el-icon>
            <span>资源配置</span>
          </div>
        </template>
        <el-descriptions-item label="CPU">
          <el-tag type="warning" size="small">{{ detailData.cpu || '未分配' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="内存">
          <el-tag type="warning" size="small">{{ detailData.memory || '未分配' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="磁盘">
          <el-tag type="warning" size="small">{{ detailData.disk || '未分配' }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 安全信息 -->
      <el-descriptions :column="1" border class="detail-section">
        <template #title>
          <div class="section-header">
            <el-icon><Lock /></el-icon>
            <span>安全信息</span>
          </div>
        </template>
        <el-descriptions-item label="用户名">
          <div class="copyable">
            <span>{{ detailData.username || '-' }}</span>
            <el-icon @click="copyToClipboard(detailData.username)"><CopyDocument /></el-icon>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="密码">
          <span>***</span>
          <el-button type="text" size="small" @click="showPassword = !showPassword" style="margin-left: 10px;">
            {{ showPassword ? '隐藏' : '显示' }}
          </el-button>
          <transition name="fade">
            <span v-if="showPassword" class="password-show">{{ detailData.password || '未设置' }}</span>
          </transition>
        </el-descriptions-item>
        <el-descriptions-item label="连接字符串">
          <div class="copyable">
            <el-input
              v-model="detailData.connection_string"
              type="textarea"
              :rows="2"
              readonly
              size="small"
            />
            <el-button
              type="primary"
              size="small"
              @click="copyToClipboard(detailData.connection_string)"
              style="margin-left: 8px;"
            >
              复制
            </el-button>
          </div>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 运维策略 -->
      <el-descriptions :column="2" border class="detail-section">
        <template #title>
          <div class="section-header">
            <el-icon><Tools /></el-icon>
            <span>运维策略</span>
          </div>
        </template>
        <el-descriptions-item label="维护窗口">{{ detailData.maintenance_window || '未设置' }}</el-descriptions-item>
        <el-descriptions-item label="备份策略">
          <el-popover
            placement="top-start"
            title="备份策略详情"
            :width="300"
            trigger="hover"
            :content="detailData.backup_policy || '未设置备份策略'"
          >
            <template #reference>
              <el-text truncated>{{ detailData.backup_policy || '未设置' }}</el-text>
            </template>
          </el-popover>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 备注信息 -->
      <el-descriptions :column="1" border class="detail-section" v-if="detailData.description">
        <template #title>
          <div class="section-header">
            <el-icon><Document /></el-icon>
            <span>备注信息</span>
          </div>
        </template>
        <el-descriptions-item>{{ detailData.description }}</el-descriptions-item>
      </el-descriptions>

      <!-- 元数据 -->
      <el-descriptions :column="2" border class="detail-section">
        <template #title>
          <div class="section-header">
            <el-icon><Clock /></el-icon>
            <span>元数据</span>
          </div>
        </template>
        <el-descriptions-item label="创建时间">{{ formatDate(null, null, detailData.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDate(null, null, detailData.updated_at) }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <template #footer>
      <el-button @click="detailDialogVisible = false">关闭</el-button>
      <el-button type="primary" @click="openDialog(detailData)">编辑</el-button>
    </template>
  </el-dialog>

    <el-dialog
      :title="editedItem.id ? '编辑数据库实例' : '新增数据库实例'"
      v-model="dialogVisible"
      width="800px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="editedItem" :rules="formRules" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="实例名称" prop="name">
              <el-input v-model="editedItem.name" />
            </el-form-item>
            <el-form-item label="数据库类型" prop="db_type">
              <el-select v-model="editedItem.db_type" style="width: 100%">
                <el-option v-for="item in dbTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="数据库版本">
              <el-input v-model="editedItem.version" />
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
            <el-form-item label="主机地址" prop="host">
              <el-input v-model="editedItem.host" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="端口号" prop="port">
              <el-input-number v-model="editedItem.port" :min="1" :max="65535" style="width: 100%" />
            </el-form-item>
            <el-form-item label="实例名/SID">
              <el-input v-model="editedItem.instance" />
            </el-form-item>
            <el-form-item label="数据库名">
              <el-input v-model="editedItem.db_name" />
            </el-form-item>
            <el-form-item label="字符集">
              <el-input v-model="editedItem.charset" />
            </el-form-item>
            <el-form-item label="CPU分配">
              <el-input v-model="editedItem.cpu" placeholder="如: 4核" />
            </el-form-item>
            <el-form-item label="内存分配">
              <el-input v-model="editedItem.memory" placeholder="如: 16GB" />
            </el-form-item>
            <el-form-item label="磁盘大小">
              <el-input v-model="editedItem.disk" placeholder="如: 500GB" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="连接字符串">
          <el-input v-model="editedItem.connection_string" type="textarea" :rows="2" placeholder="如: jdbc:mysql://host:port/dbname" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用户名">
              <el-input v-model="editedItem.username" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="密码">
              <el-input v-model="editedItem.password" type="password" show-password placeholder="若不修改请留空" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="维护窗口">
          <el-input v-model="editedItem.maintenance_window" placeholder="如: 每周六 03:00-05:00" />
        </el-form-item>
        <el-form-item label="备份策略">
          <el-input v-model="editedItem.backup_policy" type="textarea" :rows="3" placeholder="描述备份策略" />
        </el-form-item>
        <el-form-item label="备注">
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
          确定要删除数据库实例 <strong>{{ deleteItemData.name }}</strong> 吗？
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
import {
  Search, Plus, DataAnalysis, Collection, Cpu, Menu,
  Edit, Delete, Warning, View, InfoFilled, CopyDocument,
  Connection, Monitor, Lock, Tools, Document, Clock
} from '@element-plus/icons-vue'
import {
  listcmdbdatabase,
  createcmdbdatabase,
  updatecmdbdatabase,
  deletecmdbdatabase
} from '@/api/cmdb/cmdbdatabase'

const tableKey = ref(0)
const listLoading = ref(true)
const databaseList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')

// 新增详情相关状态
const detailDialogVisible = ref(false)
const detailData = ref(null)
const showPassword = ref(false)

// 打开详情弹窗
const openDetailDialog = (row) => {
  detailData.value = { ...row }
  showPassword.value = false
  detailDialogVisible.value = true
}

// 复制到剪贴板
const copyToClipboard = async (text) => {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch (err) {
    // 降级方案
    const textarea = document.createElement('textarea')
    textarea.value = text
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success('已复制到剪贴板')
  }
}

const stats = ref({
  total: 0,
  prod_count: 0,
  oracle_count: 0,
  mysql_count: 0
})

const dialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const deleteItemData = ref({})

const editedItem = ref({
  id: null, name: '', db_type: 'mysql', version: '', project: '', environment: 'prod', owner: '',
  host: '', port: 3306, instance: '', db_name: '', charset: '', cpu: '', memory: '', disk: '',
  connection_string: '', username: '', password: '', backup_policy: '', maintenance_window: '', description: ''
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

const dbTypeOptions = [
  { label: 'Oracle', value: 'oracle' },
  { label: 'MySQL', value: 'mysql' },
  { label: 'MongoDB', value: 'mongodb' },
  { label: 'PostgreSQL', value: 'postgresql' },
  { label: 'SQL Server', value: 'sqlserver' },
  { label: 'Redis', value: 'redis' },
  { label: 'Elasticsearch', value: 'elasticsearch' },
  { label: '其他', value: 'other' }
]

const formRef = ref(null)
const formRules = {
  name: [{ required: true, message: '实例名称不能为空', trigger: 'blur' }],
  db_type: [{ required: true, message: '请选择数据库类型', trigger: 'change' }],
  project: [{ required: true, message: '所属项目不能为空', trigger: 'blur' }],
  environment: [{ required: true, message: '请选择环境类型', trigger: 'change' }],
  owner: [{ required: true, message: '负责人不能为空', trigger: 'blur' }],
  host: [{ required: true, message: '主机地址不能为空', trigger: 'blur' }],
  port: [{ required: true, message: '端口号不能为空', trigger: 'blur' }]
}

const fetchData = async () => {
  listLoading.value = true
  try {
    const params = { page: currentPage.value, pageSize: pageSize.value, search: searchQuery.value }
    const res = await listcmdbdatabase(params)
    const payload = res.data || res
    const listData = payload.results || payload.list || payload.data || []
    databaseList.value = listData
    total.value = payload.count || payload.total || listData.length

    stats.value = {
      total: total.value,
      prod_count: listData.filter(db => db.environment === 'prod').length,
      oracle_count: listData.filter(db => db.db_type === 'oracle').length,
      mysql_count: listData.filter(db => db.db_type === 'mysql').length
    }
  } catch (err) {
    console.error(err)
    ElMessage.error('数据加载失败')
    databaseList.value = []
  } finally {
    listLoading.value = false
    tableKey.value++
  }
}

const getEnvLabel = (val) => environmentOptions.find(e => e.value === val)?.label || val
const getEnvTagType = (env) => ({ prod: 'danger', test: 'warning', dev: 'success', uat: 'primary', stg: 'info', dr: 'danger' }[env] || 'info')
const getDbTypeLabel = (val) => dbTypeOptions.find(e => e.value === val)?.label || val
const getDbTypeTag = (type) => ({ oracle: 'danger', mysql: 'success', mongodb: 'warning', postgresql: 'primary', sqlserver: 'info', redis: 'danger', elasticsearch: 'warning' }[type] || 'info')

const formatDate = (_, __, cellValue) => {
  if (!cellValue) return '-'
  try { return new Date(cellValue).toLocaleString() } catch { return cellValue }
}

const handleSearch = () => { currentPage.value = 1; fetchData() }
const handleSizeChange = (val) => { pageSize.value = val; fetchData() }
const handleCurrentChange = (val) => { currentPage.value = val; fetchData() }

const openDialog = (item) => {
  editedItem.value = item ? { ...item, password: '' } : {
    id: null, name: '', db_type: 'mysql', version: '', project: '', environment: 'prod', owner: '',
    host: '', port: 3306, instance: '', db_name: '', charset: '', cpu: '', memory: '', disk: '',
    connection_string: '', username: '', password: '', backup_policy: '', maintenance_window: '', description: ''
  }
  dialogVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

const closeDialog = () => { dialogVisible.value = false }

const save = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      const payload = { ...editedItem.value }
      if (!payload.password) delete payload.password

      if (editedItem.value.id) {
        await updatecmdbdatabase(editedItem.value.id, payload)
        ElMessage.success('更新成功')
      } else {
        await createcmdbdatabase(payload)
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
    await deletecmdbdatabase(deleteItemData.value.id)
    ElMessage.success('删除成功')
    deleteDialogVisible.value = false
    fetchData()
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(() => { fetchData() })
</script>

<style scoped>
.database-container { padding: 20px; background-color: #f5f7fa; }
.search-bar { display: flex; align-items: center; margin-bottom: 10px; }
.card-icon { font-size: 20px; margin-right: 8px; }
.stat-card { border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); transition: all 0.3s; }
.stat-card:hover { transform: translateY(-5px); box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15); }
.card-header { display: flex; align-items: center; margin-bottom: 10px; color: #606266; }
.card-body { text-align: center; }
.display-4 { font-size: 28px; font-weight: bold; color: #409EFF; }
.text-primary { color: #409EFF; }
.text-info { color: #909399; }
.text-success { color: #67C23A; }
.table-card { border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); }
.pagination-container { margin-top: 20px; display: flex; justify-content: flex-end; }
</style>
