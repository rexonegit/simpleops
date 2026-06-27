<template>
  <div class="alert-container">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="请输入告警名称、主机、IP或项目"
        clearable
        style="width: 300px; margin-right: 10px;"
        @keyup.enter="handleSearch"
      />
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px; margin-right: 10px;" @change="handleSearch">
        <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-select v-model="filterLevel" placeholder="级别" clearable style="width: 120px; margin-right: 10px;" @change="handleSearch">
        <el-option v-for="item in levelOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-button type="primary" @click="handleSearch">
        <el-icon style="margin-right: 4px;"><Search /></el-icon>搜索
      </el-button>
      <el-button type="primary" @click="openCreateDialog" style="margin-left: 8px;">
        <el-icon style="margin-right: 4px;"><Plus /></el-icon>新建
      </el-button>
      <el-button type="success" @click="openPasteDialog" style="margin-left: 8px;">
        <el-icon style="margin-right: 4px;"><DocumentCopy /></el-icon>智能粘贴
      </el-button>
    </div>

    <!-- 统计徽章 -->
    <el-card style="margin-top: 20px; padding: 15px;">
      <div class="stats-container">
        <el-badge :value="stats.total" class="stat-badge" type="info">
          <el-tag size="large" effect="plain">告警总数</el-tag>
        </el-badge>
        <el-badge :value="stats.status_counts?.PROBLEM || 0" class="stat-badge" type="danger">
          <el-tag size="large" effect="plain" type="danger">告警中</el-tag>
        </el-badge>
        <el-badge :value="stats.status_counts?.RECOVERY || 0" class="stat-badge" type="success">
          <el-tag size="large" effect="plain" type="success">已恢复</el-tag>
        </el-badge>
        <el-badge :value="stats.status_counts?.MUTED || 0" class="stat-badge" type="warning">
          <el-tag size="large" effect="plain" type="warning">已屏蔽</el-tag>
        </el-badge>
        <el-badge :value="stats.level_counts?.fatal || 0" class="stat-badge" type="danger">
          <el-tag size="large" effect="plain" type="danger">致命</el-tag>
        </el-badge>
        <el-badge :value="stats.level_counts?.critical || 0" class="stat-badge" type="warning">
          <el-tag size="large" effect="plain" type="warning">严重</el-tag>
        </el-badge>
        <el-badge :value="stats.level_counts?.warning || 0" class="stat-badge" type="primary">
          <el-tag size="large" effect="plain" type="primary">警告</el-tag>
        </el-badge>
      </div>
    </el-card>

    <!-- 数据表格 -->
    <el-card style="margin-top: 20px;" class="table-card">
      <el-table
        v-loading="listLoading"
        :data="alertList"
        style="width: 100%"
        stripe
        border
        :key="tableKey"
      >
        <el-table-column prop="id" label="序号" width="70" sortable />
        <el-table-column prop="alert_name" label="告警名称" min-width="200" sortable show-overflow-tooltip />
        <el-table-column prop="project" label="项目" width="120" sortable />
        <el-table-column prop="host" label="告警主机" min-width="150" sortable show-overflow-tooltip />
        <el-table-column prop="ip_address" label="IP地址" width="130" />
        <el-table-column prop="alert_level" label="告警级别" width="90" sortable>
          <template #default="{ row }">
            <el-tag :type="levelTagType(row.alert_level)" size="small">
              {{ getLevelLabel(row.alert_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_status" label="当前状态" width="90" sortable>
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.current_status)" size="small">
              {{ getStatusLabel(row.current_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trigger_time" label="触发时间" width="160" sortable :formatter="formatDate" />
        <el-table-column prop="duration" label="持续时长" width="120" />
        <el-table-column prop="registered_by" label="登记人" width="100" />
        <el-table-column prop="registered_at" label="登记时间" width="160" sortable :formatter="formatDate" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="openEditDialog(row)">
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

    <!-- 智能粘贴对话框 -->
    <el-dialog title="智能粘贴告警信息" v-model="pasteDialogVisible" width="900px" destroy-on-close>
      <el-alert
        title="粘贴告警内容到下方文本框，系统将自动解析并填充表单字段"
        type="info"
        :closable="false"
        style="margin-bottom: 15px;"
      />
      <el-input
        v-model="pasteRawText"
        type="textarea"
        :rows="8"
        placeholder="在此粘贴告警内容..."
        @paste="handlePaste"
        style="font-family: monospace;"
      />
      <div v-if="parseError" style="color: #E6A23C; margin-top: 10px;">
        <el-icon><Warning /></el-icon> {{ parseError }}
      </div>
      <el-divider>解析结果预览</el-divider>
      <el-form :model="editedItem" label-width="120px" size="small">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="告警名称"><el-input v-model="editedItem.alert_name" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="项目"><el-input v-model="editedItem.project" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="告警主机"><el-input v-model="editedItem.host" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="IP地址"><el-input v-model="editedItem.ip_address" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="告警级别">
              <el-select v-model="editedItem.alert_level" style="width: 100%">
                <el-option v-for="item in levelOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="当前状态">
              <el-select v-model="editedItem.current_status" style="width: 100%">
                <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="触发时间">
              <el-date-picker v-model="editedItem.trigger_time" type="datetime" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="恢复时间">
              <el-date-picker v-model="editedItem.recovery_time" type="datetime" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="阈值"><el-input v-model="editedItem.threshold" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="触发时值"><el-input v-model="editedItem.trigger_value" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="告警类型"><el-input v-model="editedItem.alert_type" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="监控项"><el-input v-model="editedItem.monitor_item" /></el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="pasteDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmPasteAndOpen">确认并编辑完整表单</el-button>
      </template>
    </el-dialog>

    <!-- 新建/编辑对话框 -->
    <el-dialog :title="editedItem.id ? '编辑告警记录' : '新建告警记录'" v-model="dialogVisible" width="900px" destroy-on-close>
      <el-form ref="alertForm" :model="editedItem" :rules="formRules" label-width="120px">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="基本信息" name="basic">
            <el-row :gutter="20">
              <el-col :span="24">
                <el-form-item label="告警信息" prop="alert_info">
                  <el-input v-model="editedItem.alert_info" type="textarea" :rows="3" placeholder="完整告警描述" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="告警名称" prop="alert_name">
                  <el-input v-model="editedItem.alert_name" placeholder="简短描述告警内容" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="项目" prop="project">
                  <el-input v-model="editedItem.project" placeholder="OA、OracleDB-host等" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="告警主机" prop="host">
                  <el-input v-model="editedItem.host" placeholder="主机名称" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="IP地址" prop="ip_address">
                  <el-input v-model="editedItem.ip_address" placeholder="主机IP" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="告警类型">
                  <el-input v-model="editedItem.alert_type" placeholder="exporter类型或监控来源" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="监控项">
                  <el-input v-model="editedItem.monitor_item" placeholder="具体监控指标" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-tab-pane>

          <el-tab-pane label="告警详情" name="detail">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="阈值" prop="threshold">
                  <el-input v-model="editedItem.threshold" placeholder="如>85%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="触发时值" prop="trigger_value">
                  <el-input v-model="editedItem.trigger_value" placeholder="触发时的实际值" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="告警级别" prop="alert_level">
                  <el-select v-model="editedItem.alert_level" style="width: 100%">
                    <el-option v-for="item in levelOptions" :key="item.value" :label="item.label" :value="item.value" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="当前状态" prop="current_status">
                  <el-select v-model="editedItem.current_status" style="width: 100%">
                    <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="触发时间" prop="trigger_time">
                  <el-date-picker v-model="editedItem.trigger_time" type="datetime" style="width: 100%" value-format="YYYY-MM-DD HH:mm:ss" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="恢复时间">
                  <el-date-picker v-model="editedItem.recovery_time" type="datetime" style="width: 100%" value-format="YYYY-MM-DD HH:mm:ss" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-tab-pane>

          <el-tab-pane label="处理信息" name="handle">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="特殊处理类型" prop="special_handle_type">
                  <el-select v-model="editedItem.special_handle_type" style="width: 100%">
                    <el-option v-for="item in handleTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="是否永久屏蔽">
                  <el-switch v-model="editedItem.is_permanent_mute" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="屏蔽结束时间">
                  <el-date-picker v-model="editedItem.mute_end_time" type="datetime" style="width: 100%" value-format="YYYY-MM-DD HH:mm:ss" :disabled="editedItem.is_permanent_mute" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="24">
                <el-form-item label="屏蔽/处理原因" prop="mute_reason">
                  <el-input v-model="editedItem.mute_reason" type="textarea" :rows="3" placeholder="人工输入处理原因" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="24">
                <el-form-item label="备注">
                  <el-input v-model="editedItem.remarks" type="textarea" :rows="2" placeholder="其他补充说明" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-tab-pane>
        </el-tabs>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 删除确认对话框 -->
    <el-dialog title="删除确认" v-model="deleteDialogVisible" width="500px" destroy-on-close>
      <div style="margin-bottom: 20px;">
        <el-icon style="color: #E6A23C; font-size: 24px; vertical-align: middle;"><Warning /></el-icon>
        <span style="vertical-align: middle; margin-left: 10px;">
          确定要删除告警记录 <strong>{{ deleteItemData.alert_name }}</strong> 吗？
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
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Plus, Edit, Delete, Warning, DocumentCopy } from '@element-plus/icons-vue'
import { listAlerts, getAlertStats, createAlert, updateAlert, deleteAlert } from '@/api/opsmgmt/alert'

const tableKey = ref(0)
const listLoading = ref(true)
const alertList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const filterStatus = ref('')
const filterLevel = ref('')
const activeTab = ref('basic')

const stats = ref({
  total: 0,
  status_counts: {},
  level_counts: {}
})

const dialogVisible = ref(false)
const pasteDialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const deleteItemData = ref({})
const pasteRawText = ref('')
const parseError = ref('')

const statusOptions = [
  { label: '告警中', value: 'PROBLEM' },
  { label: '已恢复', value: 'RECOVERY' },
  { label: '已屏蔽', value: 'MUTED' }
]

const levelOptions = [
  { label: '警告', value: 'warning' },
  { label: '严重', value: 'critical' },
  { label: '致命', value: 'fatal' }
]

const handleTypeOptions = [
  { label: '屏蔽', value: 'mute' },
  { label: '抑制通知', value: 'suppress' },
  { label: '降级', value: 'downgrade' },
  { label: '其他', value: 'other' }
]

const getDefaultItem = () => ({
  id: null,
  alert_info: '',
  alert_name: '',
  project: '',
  host: '',
  ip_address: '',
  alert_type: '',
  monitor_item: '',
  threshold: '',
  trigger_value: '',
  alert_level: 'warning',
  trigger_time: '',
  recovery_time: null,
  current_status: 'PROBLEM',
  special_handle_type: 'mute',
  mute_reason: '',
  mute_end_time: null,
  is_permanent_mute: false,
  remarks: ''
})

const editedItem = ref(getDefaultItem())

const alertForm = ref(null)
const formRules = {
  alert_name: [{ required: true, message: '告警名称不能为空', trigger: 'blur' }],
  project: [{ required: true, message: '项目不能为空', trigger: 'blur' }],
  host: [{ required: true, message: '告警主机不能为空', trigger: 'blur' }],
  ip_address: [{ required: true, message: 'IP地址不能为空', trigger: 'blur' }],
  threshold: [{ required: true, message: '阈值不能为空', trigger: 'blur' }],
  trigger_value: [{ required: true, message: '触发时值不能为空', trigger: 'blur' }],
  alert_level: [{ required: true, message: '请选择告警级别', trigger: 'change' }],
  trigger_time: [{ required: true, message: '触发时间不能为空', trigger: 'change' }],
  current_status: [{ required: true, message: '请选择当前状态', trigger: 'change' }],
  special_handle_type: [{ required: true, message: '请选择处理类型', trigger: 'change' }],
  mute_reason: [{ required: true, message: '屏蔽/处理原因不能为空', trigger: 'blur' }]
}

// 键名映射表（支持多种告警格式）
const keyMap = {
  '告警事件ID': 'eventId',
  '事件ID': 'eventId',
  '告警级别': 'alert_level',
  '告警等级': 'alert_level',
  '项目名称': 'project',
  '项目': 'project',
  '告警主机': 'host',
  '主机名称': 'host',
  '主机': 'host',
  '主机地址': 'ip_address',
  '告警IP': 'ip_address',
  'IP地址': 'ip_address',
  'IP': 'ip_address',
  'ESXI地址': 'ip_address',
  '监控项': 'monitor_item',
  '监控项目': 'monitor_item',
  '监控取值': 'trigger_value',
  '触发时值': 'trigger_value',
  '当前值': 'trigger_value',
  '阈值': 'threshold',
  '触发时间': 'trigger_time',
  '告警时间': 'trigger_time',
  '首次触发时间': 'trigger_time',
  '恢复时间': 'recovery_time',
  '持续时长': 'duration',
  '当前状态': 'current_status',
  '告警状态': 'current_status',
  '告警信息': 'alert_info',
  '告警类型': 'alert_type',
  '告警名称': 'alert_name'
}

// 告警级别映射
const levelMap = {
  '警告': 'warning',
  'warning': 'warning',
  '严重': 'critical',
  'critical': 'critical',
  '致命': 'fatal',
  'fatal': 'fatal',
  '紧急': 'fatal',
  '一般': 'warning'
}

// 状态映射
const statusMap = {
  'PROBLEM': 'PROBLEM',
  'RECOVERY': 'RECOVERY',
  'OK': 'RECOVERY',
  '告警中': 'PROBLEM',
  '已恢复': 'RECOVERY',
  '已屏蔽': 'MUTED',
  'Firing': 'PROBLEM',
  'Resolved': 'RECOVERY'
}

const fetchData = async () => {
  listLoading.value = true
  try {
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value,
      search: searchQuery.value
    }
    if (filterStatus.value) params.current_status = filterStatus.value
    if (filterLevel.value) params.alert_level = filterLevel.value

    const res = await listAlerts(params)
    const payload = res.data || res
    alertList.value = payload.results || payload.list || payload.data || []
    total.value = payload.count || payload.total || alertList.value.length

    await fetchStats()
  } catch (err) {
    console.error('数据加载失败:', err)
    ElMessage.error('数据加载失败')
    alertList.value = []
    total.value = 0
  } finally {
    listLoading.value = false
    tableKey.value++
  }
}

const fetchStats = async () => {
  try {
    const res = await getAlertStats()
    stats.value = res.data || res
  } catch (e) {
    console.error('统计加载失败:', e)
  }
}

const getLevelLabel = (value) => levelOptions.find(e => e.value === value)?.label || value
const getStatusLabel = (value) => statusOptions.find(e => e.value === value)?.label || value

const levelTagType = (level) => {
  const map = { warning: 'primary', critical: 'warning', fatal: 'danger' }
  return map[level] || 'info'
}

const statusTagType = (status) => {
  const map = { PROBLEM: 'danger', RECOVERY: 'success', MUTED: 'warning' }
  return map[status] || 'info'
}

const formatDate = (_, __, cellValue) => {
  if (!cellValue) return '-'
  return new Date(cellValue).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
  })
}

const handleSearch = () => { currentPage.value = 1; fetchData() }
const handleSizeChange = (val) => { pageSize.value = val; currentPage.value = 1; fetchData() }
const handleCurrentChange = (val) => { currentPage.value = val; fetchData() }

const openCreateDialog = () => {
  editedItem.value = getDefaultItem()
  activeTab.value = 'basic'
  dialogVisible.value = true
  nextTick(() => alertForm.value?.clearValidate())
}

const openEditDialog = (item) => {
  editedItem.value = { ...item }
  activeTab.value = 'basic'
  dialogVisible.value = true
  nextTick(() => alertForm.value?.clearValidate())
}

const openPasteDialog = () => {
  editedItem.value = getDefaultItem()
  pasteRawText.value = ''
  parseError.value = ''
  pasteDialogVisible.value = true
}

// 智能粘贴解析
const handlePaste = (event) => {
  event.preventDefault()
  const text = event.clipboardData.getData('text')
  pasteRawText.value = text
  parseError.value = ''
  parseAlertText(text)
}

const parseAlertText = (text) => {
  // 重置表单
  editedItem.value = getDefaultItem()

  // 处理转义换行并分割行
  const lines = text
    .replace(/\\\s*/g, '')
    .split('\n')
    .map(l => l.trim())
    .filter(l => l)

  if (lines.length === 0) return

  // 第一行通常是标题
  const firstLine = lines[0]
  let alertName = firstLine
    .replace(/^🔔【告警】/, '')
    .replace(/^【告警】/, '')
    .replace(/^【恢复】/, '')
    .replace(/^故障!\s*/, '')
    .trim()
  editedItem.value.alert_name = alertName || firstLine

  // 存储解析出的键值对
  const parsed = {}
  let messageLines = []

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    // 跳过分隔行
    if (line.includes('| 屏蔽') || line.trim() === '|' || line.match(/^\|+$/)) continue

    // 找冒号
    const colonIndex = line.indexOf('：') !== -1 ? line.indexOf('：') : line.indexOf(':')
    if (colonIndex !== -1) {
      let key = line.substring(0, colonIndex).trim()
      let value = line.substring(colonIndex + 1).trim()

      const standardKey = keyMap[key]
      if (standardKey) {
        if (standardKey === 'alert_info') {
          messageLines = [value]
          for (let j = i + 1; j < lines.length; j++) {
            const nextLine = lines[j]
            if (nextLine.includes('：') || nextLine.includes(':')) break
            if (nextLine.trim()) messageLines.push(nextLine.trim())
          }
          parsed[standardKey] = messageLines.join('\n')
        } else if (standardKey === 'alert_level') {
          parsed[standardKey] = levelMap[value] || 'warning'
        } else if (standardKey === 'current_status') {
          parsed[standardKey] = statusMap[value] || 'PROBLEM'
        } else {
          parsed[standardKey] = value
        }
      }
    }
  }

  // 赋值到表单
  Object.keys(parsed).forEach(key => {
    if (key in editedItem.value) {
      editedItem.value[key] = parsed[key]
    }
  })

  // 提示解析结果
  if (!parsed.host && !parsed.ip_address) {
    parseError.value = '未能解析到主机或IP信息，请手动补充'
  }
}

const confirmPasteAndOpen = () => {
  pasteDialogVisible.value = false
  activeTab.value = 'basic'
  dialogVisible.value = true
  nextTick(() => alertForm.value?.clearValidate())
}

const save = () => {
  alertForm.value.validate(async (valid) => {
    if (!valid) return
    try {
      if (editedItem.value.id) {
        await updateAlert(editedItem.value.id, editedItem.value)
        ElMessage.success('更新成功')
      } else {
        await createAlert(editedItem.value)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      fetchData()
    } catch (err) {
      const errData = err?.response?.data
      if (errData) {
        const firstKey = Object.keys(errData)[0]
        if (firstKey) {
          const firstError = Array.isArray(errData[firstKey]) ? errData[firstKey][0] : errData[firstKey]
          ElMessage.error(firstError)
        } else {
          ElMessage.error('操作失败')
        }
      } else {
        ElMessage.error('操作失败')
      }
    }
  })
}

const deleteItem = (item) => {
  deleteItemData.value = { ...item }
  deleteDialogVisible.value = true
}

const confirmDelete = async () => {
  try {
    await deleteAlert(deleteItemData.value.id)
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
.alert-container { padding: 20px; background-color: #f5f7fa; }
.search-bar { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; }
.stats-container {
  display: flex;
  flex-wrap: wrap;
  gap: 30px;
  align-items: center;
  justify-content: flex-start;
}
.stat-badge { margin: 0; }
.table-card { border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); }
.pagination-container { margin-top: 20px; display: flex; justify-content: flex-end; }

@media (max-width: 768px) {
  .stats-container { gap: 15px; }
  .stat-badge:deep(.el-tag) { font-size: 13px; padding: 0 10px; }
}
</style>
