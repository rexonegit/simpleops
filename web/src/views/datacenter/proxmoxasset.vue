<template>
  <div class="proxmox-container">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索 VMID、主机名、项目、负责人、IP"
        clearable
        style="width: 300px; margin-right: 10px;"
        @keyup.enter="handleSearch"
        @input="onInputChange"
      />
      <el-button type="primary" @click="handleSearch">
        <el-icon style="margin-right: 4px;"><Search /></el-icon>搜索
      </el-button>
      <el-button @click="handleReset">
        <el-icon style="margin-right: 4px;"><RefreshLeft /></el-icon>重置
      </el-button>
      <el-button type="success" :loading="syncing" @click="handleSync" style="margin-left: 8px;">
        <el-icon style="margin-right: 4px;"><RefreshRight /></el-icon>同步 Proxmox
      </el-button>

            <!-- 最后同步时间 - 右侧 -->
      <div class="sync-time-display">
        最后同步: {{ lastSyncTime }}
      </div>

      <!-- 导出 -->
      <el-button type="primary" link class="export-btn">
        <el-icon><Upload /></el-icon>导出
      </el-button>
    </div>

    <!-- 环境类型统计卡片 -->
    <div class="env-stat-row">
      <!-- 虚拟机总数 -->
      <div class="env-stat-card" :class="{ active: activeEnvFilter === 'all' }" @click="filterByEnv('all')">
        <el-icon class="env-icon"><Monitor /></el-icon>
        <span class="env-label">虚拟机总数</span>
        <span class="env-count">{{ stats.total }}</span>
      </div>

      <!-- 分隔线 -->
      <div class="divider"></div>

      <!-- 运行中 -->
      <div class="env-stat-card status-card" :class="{ active: activeStatusFilter === 'running' }" @click="filterByStatus('running')">
        <el-icon class="env-icon running"><VideoCamera /></el-icon>
        <span class="env-label">运行中</span>
        <span class="env-count running">{{ stats.running || 0 }}</span>
      </div>

      <!-- 已停止 -->
      <div class="env-stat-card status-card" :class="{ active: activeStatusFilter === 'stopped' }" @click="filterByStatus('stopped')">
        <el-icon class="env-icon stopped"><CircleClose /></el-icon>
        <span class="env-label">已停止</span>
        <span class="env-count stopped">{{ stats.stopped || 0 }}</span>
      </div>

      <!-- 分隔线 -->
      <div class="divider"></div>

      <!-- 测试环境 -->
      <div class="env-stat-card" :class="{ active: activeEnvFilter === 'test' }" @click="filterByEnv('test')">
        <el-icon class="env-icon test"><VideoPlay /></el-icon>
        <span class="env-label">测试环境</span>
        <span class="env-count test">{{ stats.env_test || 0 }}</span>
      </div>
      <!-- 生产环境 -->
      <div class="env-stat-card" :class="{ active: activeEnvFilter === 'prod' }" @click="filterByEnv('prod')">
        <el-icon class="env-icon prod"><SwitchButton /></el-icon>
        <span class="env-label">生产环境</span>
        <span class="env-count prod">{{ stats.env_prod || 0 }}</span>
      </div>
      <!-- 开发环境 -->
      <div class="env-stat-card" :class="{ active: activeEnvFilter === 'dev' }" @click="filterByEnv('dev')">
        <el-icon class="env-icon dev"><Connection /></el-icon>
        <span class="env-label">开发环境</span>
        <span class="env-count dev">{{ stats.env_dev || 0 }}</span>
      </div>
      <!-- 其他 -->
      <div class="env-stat-card" :class="{ active: activeEnvFilter === 'other' }" @click="filterByEnv('other')">
        <el-icon class="env-icon other"><Warning /></el-icon>
        <span class="env-label">其他</span>
        <span class="env-count other">{{ stats.env_other || 0 }}</span>
      </div>
      <!-- 用户验收环境 -->
      <div class="env-stat-card" :class="{ active: activeEnvFilter === 'uat' }" @click="filterByEnv('uat')">
        <el-icon class="env-icon uat"><Clock /></el-icon>
        <span class="env-label">用户验收环境</span>
        <span class="env-count uat">{{ stats.env_uat || 0 }}</span>
      </div>

      <!-- 分隔线 -->
      <div class="divider"></div>

      <!-- 已备份 -->
      <div class="env-stat-card backup-card" :class="{ active: activeBackupFilter === 'backed_up' }" @click="filterByBackup('backed_up')">
        <el-icon class="env-icon backed-up"><DocumentChecked /></el-icon>
        <span class="env-label">已备份</span>
        <span class="env-count backed-up">{{ stats.backed_up || 0 }}</span>
      </div>

      <!-- 未备份 -->
      <div class="env-stat-card backup-card" :class="{ active: activeBackupFilter === 'no_backup' }" @click="filterByBackup('no_backup')">
        <el-icon class="env-icon no-backup"><DocumentDelete /></el-icon>
        <span class="env-label">未备份</span>
        <span class="env-count no-backup">{{ stats.no_backup || 0 }}</span>
      </div>


    </div>

    <!-- 虚拟机列表 -->
    <el-card class="table-card">
      <el-table
        v-loading="listLoading"
        :data="vmList"
        style="width: 100%"
        stripe
        border
        :key="tableKey"
      >
        <el-table-column prop="name" label="主机名" min-width="100" fixed="left" sortable>
          <template #default="{ row }">
            <span class="host-link" @click="openDetailDialog(row)">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="vmid" label="VMID" width="85" sortable />
        <el-table-column prop="project_name" label="项目" min-width="140">
          <template #header>
            <el-select v-model="filters.project_name" clearable placeholder="项目" size="small" @change="handleFilterChange">
              <el-option v-for="item in projectOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="environment_type" label="环境类型" width="100">
          <template #header>
            <el-select v-model="filters.environment_type" clearable placeholder="环境" size="small" @change="handleFilterChange">
              <el-option v-for="item in environmentOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </template>
          <template #default="{ row }">
            <el-tag :type="envTagType(row.environment_type)" size="small">{{ getEnvLabel(row.environment_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" min-width="80">
          <template #header>
            <el-select v-model="filters.owner" clearable placeholder="负责人" size="small" @change="handleFilterChange">
              <el-option v-for="item in ownerOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #header>
            <el-select v-model="filters.status" clearable placeholder="状态" size="small" @change="handleFilterChange">
              <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </template>
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP地址" min-width="120" sortable />
        <el-table-column label="储存信息" min-width="140" align="left">
          <template #default="{ row }">
            <div class="storage-cell">
              <div class="storage-total">共计: {{ row.total_disk_gb ? row.total_disk_gb.toFixed(0) : 0 }}GB</div>
              <el-popover
                v-if="row.disk_info && row.disk_info.length > 0"
                placement="bottom-start"
                :width="260"
                trigger="click"
              >
                <template #reference>
                  <span class="disk-detail-link">
                    <el-icon><Files /></el-icon>磁盘详情
                  </span>
                </template>
                <div class="disk-popover">
                  <div v-for="(disk, index) in row.disk_info" :key="index" class="disk-popover-item">
                    <div class="disk-row">
                      <span class="disk-name">{{ formatDiskDevice(disk.device) }}</span>
                      <span class="disk-size">{{ disk.size_gb ? disk.size_gb.toFixed(0) : 0 }} GB</span>
                    </div>
                    <div class="disk-storage">{{ disk.storage }}</div>
                  </div>
                </div>
              </el-popover>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="node" label="节点" min-width="110">
          <template #header>
            <el-select v-model="filters.node" clearable placeholder="节点" size="small" @change="handleFilterChange">
              <el-option v-for="item in nodeOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="Agent" width="70">
          <template #default="{ row }">
            <el-tag v-if="row.agent_running" type="success" size="small">运行</el-tag>
            <el-tag v-else-if="row.agent_enabled" type="info" size="small">启用</el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="formatted_uptime" label="运行时间" min-width="90" />
        <el-table-column prop="last_backup" label="最后备份时间" min-width="140" sortable>
          <template #default="{ row }">
            <span v-if="row.last_backup">{{ formatDate(row.last_backup) }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openEditDialog(row)">
              <el-icon style="margin-right: 2px;"><Edit /></el-icon>编辑
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">
              <el-icon style="margin-right: 2px;"><Delete /></el-icon>删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100, 200]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editDialogVisible" title="编辑虚拟机" width="600px" destroy-on-close>
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="主机名">
          <el-input v-model="editForm.name" disabled />
        </el-form-item>
        <el-form-item label="VMID">
          <el-input v-model="editForm.vmid" disabled />
        </el-form-item>
        <el-form-item label="项目">
          <el-input v-model="editForm.project_name" />
        </el-form-item>
        <el-form-item label="环境类型">
          <el-select v-model="editForm.environment_type" placeholder="选择环境类型" style="width: 100%;">
            <el-option v-for="item in environmentOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="editForm.owner" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" title="虚拟机详情" width="900px" top="5vh" destroy-on-close class="detail-dialog">
      <div class="detail-container" v-if="detailData">
        <!-- 基本信息 -->
        <el-descriptions :column="3" border class="detail-section">
          <template #title>
            <div class="section-header"><el-icon><InfoFilled /></el-icon><span>基本信息</span></div>
          </template>
          <el-descriptions-item label="VMID">
            <div class="copyable">
              <span>{{ detailData.vmid }}</span>
              <el-icon @click="copyToClipboard(detailData.vmid)"><CopyDocument /></el-icon>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="名称">{{ detailData.name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType(detailData.status)">{{ statusLabel(detailData.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="所属项目">{{ detailData.project_name }}</el-descriptions-item>
          <el-descriptions-item label="环境类型">
            <el-tag :type="envTagType(detailData.environment_type)" size="small">
              {{ getEnvLabel(detailData.environment_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="负责人">{{ detailData.owner }}</el-descriptions-item>
        </el-descriptions>

        <!-- 集群信息 -->
        <el-descriptions :column="3" border class="detail-section">
          <template #title>
            <div class="section-header"><el-icon><Grid /></el-icon><span>集群信息</span></div>
          </template>
          <el-descriptions-item label="节点">{{ detailData.node }}</el-descriptions-item>
          <el-descriptions-item label="集群">{{ detailData.cluster }}</el-descriptions-item>
          <el-descriptions-item label="资源池">{{ detailData.pool || '-' }}</el-descriptions-item>
        </el-descriptions>

        <!-- 硬件配置 -->
        <el-descriptions :column="3" border class="detail-section">
          <template #title>
            <div class="section-header"><el-icon><Cpu /></el-icon><span>硬件配置</span></div>
          </template>
          <el-descriptions-item label="CPU">{{ detailData.cpu_sockets }}插槽 × {{ detailData.cpu_cores }}核</el-descriptions-item>
          <el-descriptions-item label="内存">{{ (detailData.memory_mb / 1024).toFixed(1) }} GB</el-descriptions-item>
          <el-descriptions-item label="BIOS类型">
            <el-tag size="small">{{ detailData.bios_type === 'ovmf' ? 'UEFI(OVMF)' : 'SeaBIOS' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="操作系统">{{ detailData.os_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="运行时间">{{ detailData.formatted_uptime }}</el-descriptions-item>
        </el-descriptions>

        <!-- 存储信息 -->
        <el-descriptions :column="1" border class="detail-section">
          <template #title>
            <div class="section-header"><el-icon><Files /></el-icon><span>存储信息</span></div>
          </template>
          <el-descriptions-item label="总磁盘">{{ detailData.total_disk_gb }} GB</el-descriptions-item>
          <el-descriptions-item label="引导磁盘">{{ detailData.boot_disk_gb }} GB</el-descriptions-item>
          <el-descriptions-item label="主存储池">{{ detailData.storage }}</el-descriptions-item>
        </el-descriptions>

        <!-- 磁盘详情 -->
        <div class="disk-detail-section" v-if="detailData.disk_info && detailData.disk_info.length > 0">
          <div class="section-header" style="margin-bottom: 12px;">
            <el-icon><Files /></el-icon><span>磁盘详情</span>
          </div>
          <el-row :gutter="12">
            <el-col :span="8" v-for="(disk, index) in detailData.disk_info" :key="index">
              <div class="disk-card">
                <div class="disk-card-header">
                  <span class="disk-name">{{ formatDiskDevice(disk.device) }}</span>
                  <el-tag size="small" type="info">{{ disk.storage }}</el-tag>
                </div>
                <div class="disk-card-body">
                  <span class="disk-size-big">{{ disk.size_gb.toFixed(0) }} GB</span>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 网络信息 -->
        <el-descriptions :column="2" border class="detail-section">
          <template #title>
            <div class="section-header"><el-icon><Connection /></el-icon><span>网络信息</span></div>
          </template>
          <el-descriptions-item label="IP地址">
            <div class="copyable" v-if="detailData.ip_address">
              <span>{{ detailData.ip_address }}</span>
              <el-icon @click="copyToClipboard(detailData.ip_address)"><CopyDocument /></el-icon>
            </div>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="MAC地址">{{ detailData.mac_address || '-' }}</el-descriptions-item>
        </el-descriptions>

        <!-- 高可用与代理 -->
        <el-descriptions :column="3" border class="detail-section">
          <template #title>
            <div class="section-header"><el-icon><Lock /></el-icon><span>高可用与代理</span></div>
          </template>
          <el-descriptions-item label="高可用状态">
            <el-tag :type="haStateType(detailData.ha_state)">{{ detailData.ha_state || '未启用' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="高可用组">{{ detailData.ha_group || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Guest Agent">
            <el-tag :type="detailData.agent_running ? 'success' : 'info'">
              {{ detailData.agent_enabled ? (detailData.agent_running ? '运行中' : '已启用') : '未启用' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 备份信息（仅当有备份时显示） -->
        <el-descriptions :column="3" border class="detail-section" v-if="detailData.last_backup">
          <template #title>
            <div class="section-header"><el-icon><Timer /></el-icon><span>备份信息</span></div>
          </template>
          <el-descriptions-item label="备份存储">
            {{ detailData.backup_storage || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="最后备份时间">
            {{ formatDate(detailData.last_backup) || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="备份大小">
            {{ detailData.last_backup_size ? (detailData.last_backup_size / 1024**3).toFixed(2) : 0 }} GB
          </el-descriptions-item>
          <el-descriptions-item label="备份数量">
            {{ detailData.backup_count || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="验证状态">
            <el-tag :type="detailData.last_backup_status === 'ok' ? 'success' : (detailData.last_backup_status === 'failed' ? 'danger' : 'info')">
              {{ detailData.last_backup_status || '未知' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="备份格式">
            {{ detailData.last_backup_format || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="最后备份卷ID" :span="3">
            <div class="copyable">
              <span class="ellipsis">{{ detailData.last_backup_volid || '-' }}</span>
              <el-icon @click="copyToClipboard(detailData.last_backup_volid)" v-if="detailData.last_backup_volid">
                <CopyDocument />
              </el-icon>
            </div>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 元数据 -->
        <el-descriptions :column="2" border class="detail-section">
          <template #title>
            <div class="section-header"><el-icon><Clock /></el-icon><span>元数据</span></div>
          </template>
          <el-descriptions-item label="最后同步">{{ formatDate(detailData.last_sync) }}</el-descriptions-item>

        </el-descriptions>




        <!-- 描述 -->
        <el-descriptions :column="1" border class="detail-section" v-if="detailData.description">
          <template #title>
            <div class="section-header"><el-icon><Memo /></el-icon><span>描述信息</span></div>
          </template>
          <el-descriptions-item>{{ detailData.description }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search, RefreshRight, RefreshLeft, Monitor, VideoPlay, SwitchButton, Connection, Warning, Clock,
  View, InfoFilled, CopyDocument, Grid, Cpu, Lock, Memo, Files, Edit, Delete, Upload,
  VideoCamera, CircleClose, DocumentChecked, DocumentDelete
} from '@element-plus/icons-vue'
import { getProxmoxList, syncProxmox, getProxmoxStats, updateProxmoxVM, deleteProxmoxVM } from '@/api/datacenter/proxmox'

// 状态变量
const tableKey = ref(0)
const listLoading = ref(true)
const syncing = ref(false)
const vmList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const lastSyncTime = ref('')
const activeEnvFilter = ref('all')
const activeStatusFilter = ref('')  // 新增：状态筛选
const activeBackupFilter = ref('')  // 新增：备份状态筛选

// 统计数据 - 新增 backed_up 字段
const stats = ref({
  total: 0, running: 0, stopped: 0, ha_enabled: 0, no_backup: 0, backed_up: 0,
  env_prod: 0, env_stg: 0, env_uat: 0, env_test: 0, env_dev: 0, env_other: 0
})

// 筛选器 - 新增 backup_status 字段
const filters = ref({
  node: '', status: '', project_name: '', environment_type: '', owner: '', backup_status: ''
})

// 选项
const nodeOptions = ref([])
const projectOptions = ref([])
const ownerOptions = ref([])

const statusOptions = [
  { value: 'running', label: '运行中' },
  { value: 'stopped', label: '已停止' },
  { value: 'paused', label: '已暂停' }
]

// 环境选项 - 按顺序: prod, stg, uat, test, dev, other
const environmentOptions = [
  { value: 'prod', label: '生产环境' },
  { value: 'stg', label: '预生产环境' },
  { value: 'uat', label: '用户验收环境' },
  { value: 'test', label: '测试环境' },
  { value: 'dev', label: '开发环境' },
  { value: 'dr', label: '灾备环境' },
  { value: 'other', label: '其他' }
]

// 详情弹窗
const detailDialogVisible = ref(false)
const detailData = ref(null)

// 编辑弹窗
const editDialogVisible = ref(false)
const editForm = ref({
  id: null,
  name: '',
  vmid: '',
  project_name: '',
  environment_type: '',
  owner: '',
  description: ''
})

// 获取数据
const fetchData = async () => {
  listLoading.value = true
  try {
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value,
      search: searchQuery.value,
      ...Object.fromEntries(Object.entries(filters.value).filter(([_, v]) => v))
    }

    const response = await getProxmoxList(params)
    const payload = response.data || response

    vmList.value = payload.results || payload.list || payload.data || []
    total.value = payload.count || payload.total || vmList.value.length

    updateOptions()

    if (vmList.value.length > 0) {
      const syncTimes = vmList.value
        .filter(vm => vm.last_sync)
        .map(vm => new Date(vm.last_sync))
      if (syncTimes.length > 0) {
        const lastSync = new Date(Math.max(...syncTimes))
        lastSyncTime.value = formatDateTime(lastSync)
      }
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败')
    vmList.value = []
    total.value = 0
  } finally {
    listLoading.value = false
    tableKey.value++
  }
}

// 获取统计数据
const fetchStats = async () => {
  try {
    // 如果希望统计不受列表筛选影响，可以移除 params 或调用无参接口
    const params = Object.fromEntries(Object.entries(filters.value).filter(([_, v]) => v))
    const response = await getProxmoxStats(params)  // 如果 params 不应传递，可改为 ()
    const data = response.data || response

    // 从 env_counts 中提取环境统计，默认空对象
    const env = data.env_counts || {}

    stats.value = {
      total: data.total || 0,
      running: data.running || 0,
      stopped: data.stopped || 0,
      ha_enabled: data.ha_enabled || 0,
      no_backup: data.no_backup || 0,
      backed_up: data.backed_up || (data.total - data.no_backup) || 0,  // 计算已备份数量
      // 从 env 对象中取值，不存在的环境默认为 0
      env_prod: env.prod || 0,
      env_stg: env.stg || 0,        // 后端可能未返回，默认 0
      env_uat: env.uat || 0,
      env_test: env.test || 0,
      env_dev: env.dev || 0,
      env_dr: env.dr || 0,          // 如有需要可添加
      env_other: env.other || 0
    }

    // 最后同步时间（从 last_sync_time 字段获取）
    if (data.last_sync_time) {
      lastSyncTime.value = formatDateTime(new Date(data.last_sync_time))
    } else {
      lastSyncTime.value = ''
    }
  } catch (error) {
    console.error('获取统计失败:', error)
  }
}

// 更新选项列表
const updateOptions = () => {
  nodeOptions.value = [...new Set(vmList.value.map(vm => vm.node).filter(Boolean))]
  projectOptions.value = [...new Set(vmList.value.map(vm => vm.project_name).filter(Boolean))]
  ownerOptions.value = [...new Set(vmList.value.map(vm => vm.owner).filter(Boolean))]
}

// 按环境类型过滤
const filterByEnv = (envType) => {
  activeEnvFilter.value = envType
  activeStatusFilter.value = ''  // 清除状态筛选
  activeBackupFilter.value = ''  // 清除备份筛选

  if (envType === 'all') {
    filters.value.environment_type = ''
  } else {
    filters.value.environment_type = envType
  }
  // 清除其他筛选
  filters.value.status = ''
  filters.value.backup_status = ''

  currentPage.value = 1
  fetchData()
  fetchStats()
}

// 新增：按状态过滤
const filterByStatus = (status) => {
  activeStatusFilter.value = status
  activeEnvFilter.value = 'all'  // 清除环境筛选
  activeBackupFilter.value = ''  // 清除备份筛选

  filters.value.status = status
  filters.value.environment_type = ''
  filters.value.backup_status = ''

  currentPage.value = 1
  fetchData()
  fetchStats()
}

// 新增：按备份状态过滤
const filterByBackup = (backupStatus) => {
  activeBackupFilter.value = backupStatus
  activeEnvFilter.value = 'all'  // 清除环境筛选
  activeStatusFilter.value = ''  // 清除状态筛选

  filters.value.backup_status = backupStatus
  filters.value.environment_type = ''
  filters.value.status = ''

  currentPage.value = 1
  fetchData()
  fetchStats()
}

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1
  activeEnvFilter.value = 'all'
  activeStatusFilter.value = ''
  activeBackupFilter.value = ''
  filters.value.environment_type = ''
  filters.value.status = ''
  filters.value.backup_status = ''
  fetchData()
  fetchStats()
}

// 重置
const handleReset = () => {
  searchQuery.value = ''
  filters.value = { node: '', status: '', project_name: '', environment_type: '', owner: '', backup_status: '' }
  activeEnvFilter.value = 'all'
  activeStatusFilter.value = ''
  activeBackupFilter.value = ''
  currentPage.value = 1
  fetchData()
  fetchStats()
}

const onInputChange = () => {
  if (!searchQuery.value.trim()) {
    fetchData()
    fetchStats()
  }
}

// 筛选处理
const handleFilterChange = () => {
  currentPage.value = 1
  activeEnvFilter.value = 'all'
  activeStatusFilter.value = ''
  activeBackupFilter.value = ''
  fetchData()
  fetchStats()
}

// 分页处理
const handleSizeChange = (val) => {
  pageSize.value = val
  fetchData()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchData()
}

// 同步Proxmox
const handleSync = async () => {
  syncing.value = true
  try {
    const res = await syncProxmox()
    const data = res.data || res
    ElMessage.success(data.msg || `同步完成，共计 ${data.total || 0} 台虚拟机`)
    fetchData()
    fetchStats()
  } catch (err) {
    console.error('同步失败:', err)
    ElMessage.error('同步失败，请检查 Proxmox VE 连接配置')
  } finally {
    syncing.value = false
  }
}

// 打开编辑弹窗
const openEditDialog = (row) => {
  editForm.value = {
    id: row.id,
    name: row.name,
    vmid: row.vmid,
    project_name: row.project_name || '',
    environment_type: row.environment_type || '',
    owner: row.owner || '',
    description: row.description || ''
  }
  editDialogVisible.value = true
}

// 保存编辑
const handleSaveEdit = async () => {
  try {
    await updateProxmoxVM(editForm.value.id, {
      project_name: editForm.value.project_name,
      environment_type: editForm.value.environment_type,
      owner: editForm.value.owner,
      description: editForm.value.description
    })
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    fetchData()
    fetchStats()
  } catch (err) {
    console.error('保存失败:', err)
    ElMessage.error('保存失败')
  }
}

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除虚拟机 ${row.name} 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteProxmoxVM(row.id)
    ElMessage.success('删除成功')
    fetchData()
    fetchStats()
  } catch (err) {
    if (err !== 'cancel') {
      console.error('删除失败:', err)
      ElMessage.error('删除失败')
    }
  }
}

// 打开详情弹窗
const openDetailDialog = (row) => {
  detailData.value = { ...row }
  detailDialogVisible.value = true
}

// 复制到剪贴板
const copyToClipboard = async (text) => {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch (err) {
    const textarea = document.createElement('textarea')
    textarea.value = text
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success('已复制到剪贴板')
  }
}

// 格式化函数
const formatDateTime = (date) => {
  return date.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  if (isNaN(date)) return dateStr
  return formatDateTime(date)
}

// 格式化磁盘设备名: scsi0 -> SCSI 0, sata1 -> SATA 1
const formatDiskDevice = (device) => {
  if (!device) return '-'
  const match = device.match(/^([a-zA-Z]+)(\d+)$/)
  if (match) {
    return `${match[1].toUpperCase()} ${match[2]}`
  }
  return device.toUpperCase()
}

const statusLabel = (status) => {
  const map = { running: '运行中', stopped: '已停止', paused: '已暂停' }
  return map[status] || status
}

const statusTagType = (status) => {
  const map = { running: 'success', stopped: 'danger', paused: 'warning' }
  return map[status] || 'info'
}

const getEnvLabel = (value) => {
  const env = environmentOptions.find(e => e.value === value)
  return env ? env.label : value || '未分类'
}

const envTagType = (envCode) => {
  const map = { prod: 'danger', stg: 'warning', dr: 'warning', uat: 'primary', test: 'primary', dev: 'success', other: 'info' }
  return map[envCode] || 'info'
}

const haStateType = (state) => {
  const map = { started: 'success', stopped: 'info', error: 'danger', disabled: 'warning' }
  return map[state] || 'info'
}

onMounted(() => {
  fetchData()
  fetchStats()
})
</script>

<style lang="scss" scoped>
.proxmox-container {
  padding: 16px;
  background-color: #f5f7fa;
  min-height: 100%;

  .search-bar {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;

    .export-btn {
      margin-left: auto;
    }
  }

  // 环境类型统计卡片行
  .env-stat-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: #fff;
    border-radius: 8px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    flex-wrap: wrap;

    .divider {
      width: 1px;
      height: 32px;
      background: #e4e7ed;
      margin: 0 4px;
    }

    .env-stat-card {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 10px 16px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;
      background: #f5f7fa;
      border: 1px solid transparent;

      &:hover {
        background: #ecf5ff;
        border-color: #c6e2ff;
      }

      &.active {
        background: #ecf5ff;
        border-color: #409EFF;
      }

      // 状态卡片特殊样式
      &.status-card {
        background: #f0f9ff;

        &:hover {
          background: #e6f7ff;
          border-color: #91d5ff;
        }

        &.active {
          background: #e6f7ff;
          border-color: #1890ff;
        }
      }

      // 备份卡片特殊样式
      &.backup-card {
        background: #f6ffed;

        &:hover {
          background: #d9f7be;
          border-color: #b7eb8f;
        }

        &.active {
          background: #d9f7be;
          border-color: #52c41a;
        }
      }

      .env-icon {
        font-size: 16px;
        color: #409EFF;

        &.test { color: #409EFF; }
        &.prod { color: #F56C6C; }
        &.dev { color: #67C23A; }
        &.other { color: #E6A23C; }
        &.uat { color: #909399; }

        // 状态图标颜色
        &.running { color: #67C23A; }
        &.stopped { color: #F56C6C; }

        // 备份图标颜色
        &.backed-up { color: #52c41a; }
        &.no-backup { color: #ff4d4f; }
      }

      .env-label {
        font-size: 14px;
        color: #606266;
      }

      .env-count {
        font-size: 14px;
        font-weight: 600;
        color: #409EFF;

        &.test { color: #409EFF; }
        &.prod { color: #F56C6C; }
        &.dev { color: #67C23A; }
        &.other { color: #E6A23C; }
        &.uat { color: #909399; }

        // 状态数字颜色
        &.running { color: #67C23A; }
        &.stopped { color: #F56C6C; }

        // 备份数字颜色
        &.backed-up { color: #52c41a; }
        &.no-backup { color: #ff4d4f; }
      }
    }

    .sync-time-display {
      margin-left: auto;
      font-size: 13px;
      color: #606266;
      white-space: nowrap;
    }
  }

  .host-link {
    color: #409EFF;
    cursor: pointer;

    &:hover {
      text-decoration: underline;
    }
  }

  // 存储信息样式
  .storage-cell {
    .storage-total {
      font-weight: 600;
      color: #303133;
      font-size: 13px;
      margin-bottom: 4px;
    }

    .disk-detail-link {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      color: #409EFF;
      font-size: 12px;
      cursor: pointer;

      &:hover {
        text-decoration: underline;
      }
    }
  }

  .disk-popover {
    .disk-popover-item {
      padding: 10px;
      background: #f8f9fa;
      border-radius: 6px;
      margin-bottom: 8px;

      &:last-child {
        margin-bottom: 0;
      }

      .disk-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;

        .disk-name {
          font-weight: 600;
          color: #303133;
          font-size: 13px;
        }

        .disk-size {
          color: #409EFF;
          font-weight: 600;
          font-size: 13px;
        }
      }

      .disk-storage {
        font-size: 12px;
        color: #909399;
      }
    }
  }

  .text-muted { color: #909399; }

  .table-card {
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  }

  .pagination-container {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
}

.detail-dialog {
  .detail-container {
    max-height: 70vh;
    overflow-y: auto;
  }

  .detail-section {
    margin-bottom: 20px;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: #303133;
  }

  .copyable {
    display: flex;
    align-items: center;
    gap: 8px;

    .el-icon {
      cursor: pointer;
      color: #409EFF;

      &:hover {
        color: #66b1ff;
      }
    }
  }

  .disk-detail-section {
    margin-bottom: 20px;
    padding: 16px;
    background: #fafafa;
    border-radius: 8px;

    .disk-card {
      background: #fff;
      border: 1px solid #ebeef5;
      border-radius: 6px;
      padding: 12px;
      margin-bottom: 8px;

      .disk-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;

        .disk-name {
          font-weight: 600;
          color: #303133;
        }
      }

      .disk-card-body {
        text-align: center;

        .disk-size-big {
          font-size: 20px;
          font-weight: bold;
          color: #409EFF;
        }
      }
    }
  }
}
</style>
