<template>
  <div class="networkdevice-container">
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="请输入主机名、项目、负责人、管理IP、型号"
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
            <span>网络设备总数</span>
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
            <span>即将过保 (3个月内)</span>
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
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="card-header">
            <el-icon class="card-icon"><SetUp /></el-icon>
            <span>核心设备</span>
          </div>
          <div class="card-body">
            <div class="display-4 text-primary">{{ stats.core_devices }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;" class="table-card">
      <el-table
        v-loading="listLoading"
        :data="networkDeviceList"
        style="width: 100%"
        stripe
        border
        :key="tableKey"
      >
        <el-table-column prop="hostname" label="主机名" min-width="150" sortable />
        <el-table-column prop="management_ip" label="管理IP" min-width="120" sortable />
        <el-table-column prop="project" label="项目" min-width="100" sortable />
        <el-table-column prop="environment" label="环境类型" min-width="110" sortable>
          <template #default="{ row }">
            <el-tag :type="getEnvTagType(row.environment)" size="small">
              {{ getEnvLabel(row.environment) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" min-width="90" sortable />
        <el-table-column prop="device_type" label="设备类型" min-width="100" sortable>
          <template #default="{ row }">
            <el-tag :type="getDeviceTypeTagType(row.device_type)" size="small">
              {{ getDeviceTypeLabel(row.device_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="vendor" label="厂商" min-width="80" sortable>
          <template #default="{ row }">{{ getVendorLabel(row.vendor) }}</template>
        </el-table-column>
        <el-table-column prop="model" label="型号" min-width="150" sortable />
        <el-table-column prop="poe_support" label="POE支持" min-width="120">
          <template #default="{ row }">
            <el-tag v-if="row.poe_support" :type="getPoeTagType(row.poe_support)" size="small">
              {{ getPoeLabel(row.poe_support) }}
            </el-tag>
            <span v-else style="color: #C0C4CC;">未配置</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="100">
          <template #default="{ row }">
            <el-tag v-if="row.status" :type="getStatusTagType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="warranty_expire" label="维保到期" min-width="120" sortable>
          <template #default="{ row }">
            <span :class="{ 'text-danger': isExpiring(row.warranty_expire) }">
              {{ formatDate(row.warranty_expire) }}
            </span>
          </template>
        </el-table-column>
       <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <div style="display: flex; gap: 8px; white-space: nowrap;">
              <el-button type="text" size="small" @click="showDetail(row)">
                <el-icon style="margin-right: 2px;"><View /></el-icon>详情
              </el-button>
              <el-button type="text" size="small" @click="openDialog(row)">
                <el-icon style="margin-right: 2px;"><Edit /></el-icon>编辑
              </el-button>
              <el-button type="text" size="small" style="color: #F56C6C;" @click="deleteItem(row)">
                <el-icon style="margin-right: 2px;"><Delete /></el-icon>删除
              </el-button>
            </div>
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

    <!-- 添加编辑对话框 -->
    <el-dialog
      :title="editedItem.id ? '编辑网络设备' : '新增网络设备'"
      v-model="dialogVisible"
      width="900px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="editedItem" label-width="120px" :rules="formRules">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="主机名" prop="hostname">
              <el-input v-model="editedItem.hostname" />
            </el-form-item>
            <el-form-item label="管理IP" prop="management_ip">
              <el-input v-model="editedItem.management_ip" />
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
            <el-form-item label="操作系统" prop="os_info">
              <el-input v-model="editedItem.os_info" />
            </el-form-item>
            <el-form-item label="设备类型" prop="device_type">
              <el-select v-model="editedItem.device_type" style="width: 100%">
                <el-option v-for="item in deviceTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="厂商">
              <el-select v-model="editedItem.vendor" style="width: 100%">
                <el-option v-for="item in vendorOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="型号">
              <el-input v-model="editedItem.model" />
            </el-form-item>
            <el-form-item label="序列号">
              <el-input v-model="editedItem.serial_number" />
            </el-form-item>
            <el-form-item label="软件版本">
              <el-input v-model="editedItem.software_version" />
            </el-form-item>
            <el-form-item label="POE支持">
              <el-select v-model="editedItem.poe_support" style="width: 100%">
                <el-option v-for="item in poeSupportOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="连接方式">
              <el-select v-model="editedItem.connection_method" style="width: 100%">
                <el-option v-for="item in connectionMethodOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="连接端口">
              <el-input v-model="editedItem.connection_port" placeholder="如: SSH 22" />
            </el-form-item>
            <el-form-item label="位置">
              <el-input v-model="editedItem.location" />
            </el-form-item>
            <el-form-item label="端口数量">
              <el-input-number v-model="editedItem.port_count" :min="0" style="width: 100%" />
            </el-form-item>
            <el-form-item label="接口速率">
              <el-select v-model="editedItem.interface_speed" style="width: 100%">
                <el-option v-for="item in interfaceSpeedOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="editedItem.status" style="width: 100%">
                <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="上联设备">
              <el-input v-model="editedItem.uplink_device" />
            </el-form-item>
            <el-form-item label="MAC地址">
              <el-input v-model="editedItem.mac_address" />
            </el-form-item>
            <el-form-item label="资产标签">
              <el-input v-model="editedItem.asset_tag" />
            </el-form-item>
            <el-form-item label="采购日期">
              <el-date-picker v-model="editedItem.purchase_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
            <el-form-item label="维保到期">
              <el-date-picker v-model="editedItem.warranty_expire" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="editedItem.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog title="网络设备详情" v-model="detailVisible" width="700px" class="apple-style-dialog">
      <div class="apple-detail-container">
        <div class="apple-header">
          <div class="avatar-placeholder">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="header-info">
            <h2 class="device-name">{{ currentDevice.hostname }}</h2>
            <p class="device-ip">{{ currentDevice.management_ip }} · {{ getDeviceTypeLabel(currentDevice.device_type) }}</p>
            <p class="device-project">
              <el-tag type="primary" effect="light">{{ currentDevice.project }}</el-tag>
            </p>
          </div>
        </div>

        <div class="apple-detail-section">
          <h3 class="section-title">基本信息</h3>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="item-label">主机名</span>
              <span class="item-value">{{ currentDevice.hostname }}</span>
            </div>
            <div class="detail-item">
              <span class="item-label">管理IP</span>
              <span class="item-value">{{ currentDevice.management_ip }}</span>
            </div>
            <div class="detail-item">
              <span class="item-label">环境类型</span>
              <span class="item-value">
                <el-tag :type="getEnvTagType(currentDevice.environment)" size="small">
                  {{ getEnvLabel(currentDevice.environment) }}
                </el-tag>
              </span>
            </div>
            <div class="detail-item">
              <span class="item-label">负责人</span>
              <span class="item-value">{{ currentDevice.owner }}</span>
            </div>
            <div class="detail-item">
              <span class="item-label">设备类型</span>
              <span class="item-value">
                <el-tag :type="getDeviceTypeTagType(currentDevice.device_type)" size="small">
                  {{ getDeviceTypeLabel(currentDevice.device_type) }}
                </el-tag>
              </span>
            </div>
            <div class="detail-item">
              <span class="item-label">厂商</span>
              <span class="item-value">{{ getVendorLabel(currentDevice.vendor) }}</span>
            </div>
          </div>
        </div>

        <div class="apple-detail-section">
          <h3 class="section-title">设备规格</h3>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="item-label">型号</span>
              <span class="item-value">{{ currentDevice.model || '未配置' }}</span>
            </div>
            <div class="detail-item">
              <span class="item-label">序列号</span>
              <span class="item-value">{{ currentDevice.serial_number || '未配置' }}</span>
            </div>
            <div class="detail-item">
              <span class="item-label">软件版本</span>
              <span class="item-value">{{ currentDevice.software_version || '未配置' }}</span>
            </div>
            <div class="detail-item">
              <span class="item-label">位置</span>
              <span class="item-value">{{ currentDevice.location || '未配置' }}</span>
            </div>
            <div class="detail-item">
              <span class="item-label">POE支持</span>
              <span class="item-value">
                <el-tag v-if="currentDevice.poe_support" :type="getPoeTagType(currentDevice.poe_support)" size="small">
                  {{ getPoeLabel(currentDevice.poe_support) }}
                </el-tag>
                <span v-else style="color: #C0C4CC;">未配置</span>
              </span>
            </div>
          </div>
        </div>

        <div v-if="currentDevice.description" class="apple-detail-section">
          <h3 class="section-title">备注</h3>
          <p class="remark-content">{{ currentDevice.description }}</p>
        </div>
      </div>
    </el-dialog>

    <el-dialog title="删除确认" v-model="deleteDialogVisible" width="500px">
      <div style="margin-bottom: 20px;">
        <el-icon style="color: #E6A23C; font-size: 24px; vertical-align: middle;"><Warning /></el-icon>
        <span style="vertical-align: middle; margin-left: 10px;">
          确定要删除网络设备 <strong>{{ deleteItemData.hostname }}</strong> 吗？
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
import { Search, Plus, DataAnalysis, AlarmClock, Warning, SetUp, View, Edit, Delete, Monitor } from '@element-plus/icons-vue'
import {
  listProjectNetworkDevice,
  createProjectNetworkDevice,
  updateProjectNetworkDevice,
  deleteProjectNetworkDevice
} from '@/api/datacenter/projectnetworkdevice'

const tableKey = ref(0)
const listLoading = ref(true)
const networkDeviceList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')

const stats = ref({
  total: 0,
  expiring_soon: 0,
  expired: 0,
  core_devices: 0
})

const dialogVisible = ref(false)
const detailVisible = ref(false)
const deleteDialogVisible = ref(false)
const deleteItemData = ref({})
const currentDevice = ref({})

const editedItem = ref({
  id: null, hostname: '', management_ip: '', project: '', environment: 'prod', owner: '',
  os_info: '', device_type: '', vendor: '', model: '', serial_number: '', software_version: '',
  poe_support: '', connection_method: '', connection_port: '', location: '', port_count: 0,
  interface_speed: '', uplink_device: '', mac_address: '', asset_tag: '', purchase_date: null,
  status: '', warranty_expire: null, description: ''
})

const formRef = ref(null)
const formRules = {
  hostname: [{ required: true, message: '请输入主机名', trigger: 'blur' }],
  management_ip: [{ required: true, message: '请输入管理IP', trigger: 'blur' }],
  project: [{ required: true, message: '请输入所属项目', trigger: 'blur' }],
  environment: [{ required: true, message: '请选择环境类型', trigger: 'change' }],
  owner: [{ required: true, message: '请输入负责人', trigger: 'blur' }],
  device_type: [{ required: true, message: '请选择设备类型', trigger: 'change' }]
}

// 选项配置
const environmentOptions = [
  { label: '生产环境', value: 'prod' },
  { label: '测试环境', value: 'test' },
  { label: '开发环境', value: 'dev' },
  { label: '用户验收环境', value: 'uat' },
  { label: '预生产环境', value: 'stg' },
  { label: '灾备环境', value: 'dr' }
]
const deviceTypeOptions = [
  { label: '核心交换机', value: 'core_switch' },
  { label: '接入交换机', value: 'access_switch' },
  { label: '无线AC', value: 'access_controllers' },
  { label: '无线AP', value: 'access_points' },
  { label: '路由器', value: 'router' },
  { label: '防火墙', value: 'firewall' },
  { label: '安全设备', value: 'security_device' },
  { label: '其他', value: 'other' }
]
const vendorOptions = [
  { label: 'CheckPoint', value: 'checkpoint' },
  { label: 'Cisco', value: 'cisco' },
  { label: '华为', value: 'huawei' },
  { label: 'H3C', value: 'h3c' },
  { label: 'Ruijie', value: 'ruijie' }
]
const poeSupportOptions = [
  { label: 'PoE(802.3af)', value: 'poe_af' },
  { label: 'PoE+(802.3at)', value: 'poe_at' },
  { label: 'PoE++(802.3bt)', value: 'poe_bt' },
  { label: 'noPOE', value: 'no_poe' }
]
const connectionMethodOptions = [
  { label: 'HTTP', value: 'http' },
  { label: 'HTTPS', value: 'https' },
  { label: 'SSH', value: 'ssh' },
  { label: 'TELNET', value: 'telnet' }
]
const interfaceSpeedOptions = [
  { label: '千兆', value: '1g' },
  { label: '万兆', value: '10g' }
]
const statusOptions = [
  { label: '使用中', value: 'in_use' },
  { label: '关机', value: 'shutdown' },
  { label: '下线', value: 'offline' },
  { label: '备用', value: 'standby' }
]

const fetchData = async () => {
  listLoading.value = true
  try {
    const params = { page: currentPage.value, pageSize: pageSize.value, search: searchQuery.value }
    const res = await listProjectNetworkDevice(params)
    const payload = res.data || res
    const listData = payload.results || payload.list || payload.data || []
    networkDeviceList.value = listData
    total.value = payload.count || payload.total || listData.length
    calculateStats(listData)
  } catch (err) {
    console.error(err)
    ElMessage.error('数据加载失败')
    networkDeviceList.value = []
  } finally {
    listLoading.value = false
    tableKey.value++
  }
}

const calculateStats = (list) => {
  stats.value.total = total.value
  stats.value.expiring_soon = list.filter(item => {
    if (!item.warranty_expire) return false
    const daysLeft = Math.ceil((new Date(item.warranty_expire) - new Date()) / (1000 * 3600 * 24))
    return daysLeft > 0 && daysLeft <= 90
  }).length
  stats.value.expired = list.filter(item => {
    if (!item.warranty_expire) return false
    const today = new Date(); today.setHours(0, 0, 0, 0)
    return new Date(item.warranty_expire) < today
  }).length
  stats.value.core_devices = list.filter(item => item.device_type === 'core_switch' || item.device_type === 'router').length
}

const getEnvLabel = (val) => environmentOptions.find(e => e.value === val)?.label || val
const getEnvTagType = (env) => ({ prod: 'danger', test: 'warning', dev: 'success', uat: 'primary', stg: 'info', dr: 'danger' }[env] || 'info')
const getDeviceTypeLabel = (val) => deviceTypeOptions.find(e => e.value === val)?.label || val
const getDeviceTypeTagType = (type) => ({ core_switch: 'danger', access_switch: 'primary', router: 'success', firewall: 'warning', security_device: 'info' }[type] || 'info')
const getVendorLabel = (val) => vendorOptions.find(e => e.value === val)?.label || val
const getPoeLabel = (val) => poeSupportOptions.find(e => e.value === val)?.label || val
const getPoeTagType = (val) => ({ poe_af: 'success', poe_at: 'warning', poe_bt: 'danger', no_poe: 'info' }[val] || 'info')
const getStatusLabel = (val) => statusOptions.find(e => e.value === val)?.label || val
const getStatusTagType = (val) => ({ in_use: 'success', shutdown: 'warning', offline: 'info', standby: 'primary' }[val] || 'info')

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  try { return new Date(dateStr).toISOString().split('T')[0] } catch { return dateStr }
}
const isExpiring = (dateStr) => {
  if (!dateStr) return false
  const daysLeft = Math.ceil((new Date(dateStr) - Date.now()) / (1000 * 3600 * 24))
  return daysLeft > 0 && daysLeft <= 30
}

const handleSearch = () => { currentPage.value = 1; fetchData() }
const handleSizeChange = (val) => { pageSize.value = val; fetchData() }
const handleCurrentChange = (val) => { currentPage.value = val; fetchData() }

const openDialog = (item) => {
  editedItem.value = item ? { ...item } : {
    id: null, hostname: '', management_ip: '', project: '', environment: 'prod', owner: '',
    os_info: '', device_type: '', vendor: '', model: '', serial_number: '', software_version: '',
    poe_support: '', connection_method: '', connection_port: '', location: '', port_count: 0,
    interface_speed: '', uplink_device: '', mac_address: '', asset_tag: '', purchase_date: null,
    status: '', warranty_expire: null, description: ''
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
        await updateProjectNetworkDevice(editedItem.value.id, editedItem.value)
        ElMessage.success('更新成功')
      } else {
        await createProjectNetworkDevice(editedItem.value)
        ElMessage.success('创建成功')
      }
      closeDialog()
      fetchData()
    } catch (err) {
      ElMessage.error(err?.response?.data?.detail || '操作失败')
    }
  })
}

const showDetail = (item) => { currentDevice.value = { ...item }; detailVisible.value = true }
const deleteItem = (item) => { deleteItemData.value = { ...item }; deleteDialogVisible.value = true }

const confirmDelete = async () => {
  try {
    await deleteProjectNetworkDevice(deleteItemData.value.id)
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
.networkdevice-container { padding: 20px; background-color: #f5f7fa; }
.search-bar { display: flex; align-items: center; margin-bottom: 10px; }
.card-icon { font-size: 20px; margin-right: 8px; }
.stat-card { border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); transition: all 0.3s; }
.stat-card:hover { transform: translateY(-5px); box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15); }
.card-header { display: flex; align-items: center; margin-bottom: 10px; color: #606266; }
.card-body { text-align: center; }
.display-4 { font-size: 24px; font-weight: bold; color: #409EFF; }
.text-warning { color: #e6a23c; }
.text-danger { color: #f56c6c; }
.text-primary { color: #409EFF; }
.table-card { border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); }
.pagination-container { margin-top: 20px; display: flex; justify-content: flex-end; }

.apple-detail-container { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #333; }
.apple-header { display: flex; align-items: center; padding: 20px 0; border-bottom: 1px solid #e0e0e0; margin-bottom: 20px; }
.avatar-placeholder { width: 80px; height: 80px; border-radius: 50%; background-color: #f5f5f7; display: flex; align-items: center; justify-content: center; margin-right: 20px; }
.avatar-placeholder .el-icon { font-size: 40px; color: #409EFF; }
.header-info { flex: 1; }
.device-name { font-size: 24px; font-weight: 600; margin: 0 0 5px 0; color: #000; }
.device-ip { font-size: 16px; color: #86868b; margin: 0; }
.apple-detail-section { margin-bottom: 25px; }
.section-title { font-size: 18px; font-weight: 600; margin: 0 0 15px 0; padding-bottom: 8px; border-bottom: 1px solid #f0f0f0; color: #000; }
.detail-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px 20px; }
.detail-item { display: flex; flex-direction: column; }
.item-label { font-size: 14px; color: #86868b; margin-bottom: 5px; }
.item-value { font-size: 16px; font-weight: 500; color: #000; }
.remark-content { font-size: 15px; line-height: 1.6; color: #333; padding: 10px; background-color: #f9f9f9; border-radius: 8px; }
</style>
