<template>
  <div class="vmware-container">
    <!-- 搜索框 -->
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="请输入搜索关键词"
        clearable
        style="width: 200px; margin-right: 10px;"
        @keyup.enter="handleSearch"
        @input="onInputChange"
      />
      <el-button type="primary" @click="handleSearch">
        <el-icon style="margin-right: 4px;"><Search /></el-icon>搜索
      </el-button>
      <el-button type="success" :loading="syncing" @click="handleSync" style="margin-left: 8px;">
        <el-icon style="margin-right: 4px;"><RefreshRight /></el-icon>同步vCenter
      </el-button>
      <span style="margin-left: 10px; color: #888; font-size: 13px;">可以搜索 主机名、项目、负责人、IP地址</span>
    </div>

    <!-- 统一的统计区域 -->
<el-card shadow="never" style="margin-top: 20px;">

  <!-- 统计卡片 -->
  <el-row :gutter="20">
    <el-col :span="6">
      <el-statistic :value="stats.total" title="虚拟机总数">
        <template #prefix>
          <el-icon color="#409eff" style="margin-right: 8px;"><Monitor /></el-icon>
        </template>
      </el-statistic>
    </el-col>

    <el-col :span="6">
      <el-statistic :value="stats.powered_on" title="运行中">
        <template #suffix>
          <el-tag type="success" size="small" style="margin-left: 8px;">台</el-tag>
        </template>
      </el-statistic>
    </el-col>

    <el-col :span="6">
      <el-statistic :value="stats.powered_off" title="已关闭">
        <template #suffix>
          <el-tag type="info" size="small" style="margin-left: 8px;">台</el-tag>
        </template>
      </el-statistic>
    </el-col>

    <el-col :span="6">
      <div style="display: flex; flex-direction: column;">
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
          <el-icon color="#909399" style="margin-right: 8px;"><Clock /></el-icon>
          <span style="color: #909399; font-size: 14px;">最后同步</span>
        </div>
        <span style="font-size: 16px; color: #606266;">{{ lastSyncTime }}</span>
      </div>
    </el-col>
  </el-row>

  <!-- 环境分布 - 分隔线之上 -->
  <div style="margin-top: 24px; padding-top: 20px; border-top: 1px solid #ebeef5;">
    <span style="font-size: 14px; color: #909399; margin-right: 15px;">环境分布：</span>
    <el-space wrap :size="12">
      <el-tag
        v-for="(count, env) in stats.env_counts"
        :key="env"
        :type="envTagType(env)"
        effect="plain"
        size="default"
      >
        {{ getEnvLabel(env) }}: <strong>{{ count }}</strong>
      </el-tag>
    </el-space>
  </div>
</el-card>

    <!-- 虚拟机列表 -->
    <el-card class="table-card" style="margin-top: 20px;">
      <el-table
        v-loading="listLoading"
        :data="vmList"
        style="width: 100%"
        stripe
        border
        :key="tableKey"
      >
        <el-table-column fixed="left" prop="name" label="主机名" min-width="120" sortable />
        <el-table-column prop="project_name" label="项目" min-width="120">
          <template #header>
            <el-select
              v-model="filters.project_name"
              clearable
              placeholder="项目"
              size="small"
              @change="handleFilterChange"
            >
              <el-option v-for="item in projectOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="environment_type" label="环境" min-width="100">
          <template #header>
            <el-select
              v-model="filters.environment_type"
              clearable
              placeholder="环境"
              size="small"
              @change="handleFilterChange"
            >
              <el-option
                v-for="item in environmentOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </template>
          <template #default="{ row }">
            <el-tag :type="envTagType(row.environment_type)" size="small">
              {{ getEnvLabel(row.environment_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" min-width="100">
          <template #header>
            <el-select
              v-model="filters.owner"
              clearable
              placeholder="负责人"
              size="small"
              @change="handleFilterChange"
            >
              <el-option v-for="item in ownerOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="status_display" label="状态" min-width="100">
          <template #header>
            <el-select
              v-model="filters.status"
              clearable
              placeholder="状态"
              size="small"
              @change="handleFilterChange"
            >
              <el-option
                v-for="item in statusOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </template>
          <template #default="{ row }">
            <el-tag :type="row.status === 'poweredOn' ? 'success' : 'info'">
              {{ row.status_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP地址" min-width="120" />
        <el-table-column prop="os_name" label="操作系统" min-width="120" />
        <el-table-column label="CPU" min-width="80">
          <template #default="{ row }">
            {{ row.cpu_cores }}核
          </template>
        </el-table-column>
        <el-table-column label="内存" min-width="80">
          <template #default="{ row }">
            {{ row.memory_gb }}GB
          </template>
        </el-table-column>
        <el-table-column label="存储信息" min-width="260" align="left">
          <template #default="{ row }">
            <!-- 总置备空间 -->
            <div class="storage-item">
              <span class="label">总置备空间：</span>
              <span class="value">{{ totalProvisioned(row.data_disks || []) }} GB</span>
            </div>

            <!-- 已用空间 -->
            <div class="storage-item">
              <span class="label">已用空间：</span>
              <span class="value">{{ totalUsed(row.data_disks || []) }} GB</span>
              <span class="ratio">
                (利用率 {{ storageEfficiency(row.data_disks || []) }}%)
              </span>
            </div>

            <!-- 磁盘详情 -->
            <div class="disk-details" v-if="row.data_disks && row.data_disks.length > 0">
              <el-collapse>
                <el-collapse-item title="磁盘详情">
                  <div
                    v-for="(disk, index) in row.data_disks"
                    :key="disk.disk_id"
                    class="disk-item"
                  >
                    <div class="disk-header">
                      <span class="disk-seq">磁盘 {{ index + 1 }}</span>
                      <span class="disk-id">(ID: {{ disk.disk_id }})</span>
                      <el-tag :type="diskTypeStyle(disk.disk_type)" size="small">
                        {{ formatDiskType(disk.disk_type) }}
                      </el-tag>
                    </div>
                    <div class="disk-progress">
                      <el-progress
                        :percentage="Number(diskUsage(disk))"
                        :color="diskUsageColor(disk)"
                        :show-text="false"
                        :stroke-width="12"
                      />
                      <span class="disk-usage">
                        {{ disk.used_gb }}GB / {{ disk.provisioned_gb }}GB
                      </span>
                    </div>
                    <div class="disk-meta">
                      <span class="datastore">
                        <el-icon><Files /></el-icon>
                        {{ disk.datastore || '未知存储' }}
                      </span>
                    </div>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </div>
            <div v-else class="no-disk">
              <el-icon><Warning /></el-icon>
              暂无磁盘信息
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="formatted_uptime" label="运行时间" min-width="100" />
        <el-table-column label="Tools状态" min-width="200">
          <template #default="{ row }">
            <div class="tools-status">
              <el-tag :type="getToolsStatusType(row.tools_status)" size="small">
                {{ row.tools_status }}
              </el-tag>
              <el-tag
                :type="getToolsRunningStatusType(row.tools_running_status)"
                size="small"
                style="margin-left: 5px"
              >
                {{ row.tools_running_status_display }}
              </el-tag>
              <el-tag type="info" size="small" style="margin-left: 5px">
                Tools版本: {{ row.tools_version }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="vcenter_host" label="vCenter" min-width="120">
          <template #header>
            <el-select
              v-model="filters.vcenter_host"
              clearable
              placeholder="选择vCenter"
              size="small"
              @change="handleFilterChange"
            >
              <el-option v-for="item in vcenterOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="creation_date" label="创建时间" min-width="100" :formatter="formatCreationDate" />
        <el-table-column label="备份信息" min-width="200">
          <template #default="{ row }">
            <div>
              <el-tag
                :type="row.is_backup_healthy ? 'success' : 'danger'"
                size="small"
                style="margin-bottom: 5px"
              >
                {{ row.backup_policy ? formatBackupTime(row.last_backup) : '未备份' }}
              </el-tag>
              <div v-if="row.backup_policy" class="backup-policy">
                <el-icon><Document /></el-icon>
                {{ row.backup_policy }}
              </div>
              <div v-if="row.backup_policy" class="backup-age">
                <el-icon><Clock /></el-icon>
                最后一次备份 {{ formatBackupTime(row.last_backup) }}
              </div>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100, 200, 300]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search,
  RefreshRight,
  Monitor,
  VideoPlay,
  SwitchButton,
  Clock,
  Files,
  Warning,
  Document
} from '@element-plus/icons-vue'
import { getVMwareList, syncVMware } from '@/api/datacenter/vmware'

// 状态变量
const tableKey = ref(0)
const listLoading = ref(true)
const syncing = ref(false)
const vmList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
const lastSyncTime = ref('')

// 统计数据
const stats = ref({
  total: 0,
  powered_on: 0,
  powered_off: 0,
  env_counts: {}
})

// 筛选器
const filters = ref({
  project_name: '',
  environment_type: '',
  owner: '',
  status: '',
  vcenter_host: '',
  backup_status: ''
})

// 选项列表
const projectOptions = ref([])
const ownerOptions = ref([])
const vcenterOptions = ref([])

const environmentOptions = [
  { value: 'prod', label: '生产环境' },
  { value: 'test', label: '测试环境' },
  { value: 'dev', label: '开发环境' },
  { value: 'uat', label: '用户验收环境' },
  { value: 'stg', label: '预生产环境' },
  { value: 'dr', label: '灾备环境' },
  { value: 'other', label: '其他' }
]

const statusOptions = [
  { value: 'poweredOn', label: '运行中' },
  { value: 'poweredOff', label: '已关闭' }
]

// 获取数据
const fetchData = async () => {
  listLoading.value = true
  try {
    const response = await getVMwareList({
      page: currentPage.value,
      pageSize: pageSize.value,
      search: searchQuery.value,
      ...filters.value
    })

    const payload = response.data || response

    if (Array.isArray(payload)) {
      vmList.value = payload
      total.value = payload.length
    } else {
      vmList.value = payload.results || payload.list || payload.data || []
      total.value = payload.count || payload.total || vmList.value.length
    }

    // 计算统计
    stats.value = {
      total: total.value,
      powered_on: vmList.value.filter(vm => vm.status === 'poweredOn').length,
      powered_off: vmList.value.filter(vm => vm.status === 'poweredOff').length,
      env_counts: calculateEnvCounts(vmList.value)
    }

    // 获取最后同步时间
    if (vmList.value.length > 0) {
      const syncTimes = vmList.value
        .filter(vm => vm.last_sync)
        .map(vm => new Date(vm.last_sync))
      if (syncTimes.length > 0) {
        const lastSync = new Date(Math.max(...syncTimes))
        lastSyncTime.value = formatDateTime(lastSync)
      }
    }

    // 更新选项列表
    updateOptions()
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

// 更新筛选选项
const updateOptions = () => {
  projectOptions.value = [...new Set(vmList.value.map(vm => vm.project_name).filter(Boolean))]
  ownerOptions.value = [...new Set(vmList.value.map(vm => vm.owner).filter(Boolean))]
  vcenterOptions.value = [...new Set(vmList.value.map(vm => vm.vcenter_host).filter(Boolean))]
}

// 环境统计
const calculateEnvCounts = (vmListData) => {
  const counts = {}
  vmListData.forEach(vm => {
    const env = vm.environment_type || '未分类'
    counts[env] = (counts[env] || 0) + 1
  })
  return counts
}

// 环境标签
const getEnvLabel = (value) => {
  const env = environmentOptions.find(e => e.value === value)
  return env ? env.label : value
}

// 环境标签颜色
const envTagType = (envCode) => {
  const map = {
    'prod': 'danger',
    'stg': 'warning',
    'dr': 'warning',
    'uat': 'primary',
    'test': 'primary',
    'dev': 'success',
    'other': 'info'
  }
  return map[envCode] || 'info'
}

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1
  fetchData()
}

const onInputChange = () => {
  if (!searchQuery.value.trim()) {
    fetchData()
  }
}

// 筛选处理
const handleFilterChange = () => {
  currentPage.value = 1
  fetchData()
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

// 同步vCenter
const handleSync = async () => {
  syncing.value = true
  try {
    const res = await syncVMware()
    const data = res.data || res
    ElMessage.success(data.msg || `同步完成，共计 ${data.total || 0} 台虚拟机`)
    fetchData()
  } catch (err) {
    console.error('同步失败:', err)
    ElMessage.error('同步失败，请检查 vCenter 连接配置')
  } finally {
    syncing.value = false
  }
}

// 日期格式化
const formatDateTime = (date) => {
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatCreationDate = (row, column, cellValue) => {
  if (!cellValue) return '-'
  const date = new Date(cellValue)
  if (isNaN(date)) return '-'
  return formatDateTime(date)
}

const formatBackupTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

// Tools状态
const getToolsStatusType = (status) => {
  const typeMap = {
    toolsOk: 'success',
    toolsNotRunning: 'danger'
  }
  return typeMap[status] || 'info'
}

const getToolsRunningStatusType = (status) => {
  const typeMap = {
    'guestToolsNotRunning': 'danger',
    'guestToolsExecutingScripts': 'info',
    'guestToolsRunning': 'success'
  }
  return typeMap[status] || 'info'
}

// 存储计算
const totalProvisioned = (disks) => {
  if (!disks || !Array.isArray(disks)) return 0
  return disks.reduce((sum, disk) =>
    sum + (Number(disk.provisioned_gb) || 0), 0
  ).toLocaleString()
}

const totalUsed = (disks) => {
  if (!disks || !Array.isArray(disks)) return 0
  return disks.reduce((sum, disk) =>
    sum + (Number(disk.used_gb) || 0), 0
  ).toLocaleString()
}

const storageEfficiency = (disks) => {
  if (!disks || !Array.isArray(disks)) return 0
  const provisioned = disks.reduce((sum, d) =>
    sum + (Number(d.provisioned_gb) || 0), 0
  )
  const used = disks.reduce((sum, d) =>
    sum + (Number(d.used_gb) || 0), 0
  )
  return provisioned > 0
    ? ((used / provisioned) * 100).toFixed(1)
    : 0
}

const diskUsage = (disk) => {
  const used = Number(disk.used_gb) || 0
  const total = Number(disk.provisioned_gb) || 1
  return (used / total * 100).toFixed(1)
}

const diskTypeStyle = (type) => {
  return {
    'thin': 'success',
    'thick': 'warning',
    'eagerZeroedThick': 'danger'
  }[type] || 'info'
}

const diskUsageColor = (disk) => {
  const usage = Number(diskUsage(disk))
  return usage > 90 ? '#f56c6c'
    : usage > 70 ? '#e6a23c'
      : '#67c23a'
}

const formatDiskType = (type) => {
  const typeMap = {
    'thin': '精简置备',
    'thick': '厚置备延迟置零',
    'eagerZeroedThick': '厚置备快速置零'
  }
  return typeMap[type] || '未知类型'
}

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.vmware-container {
  padding: 20px;
  background-color: #f5f7fa;

  .search-bar {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
  }

  .stat-card {
    border-radius: 8px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    transition: all 0.3s;

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15);
    }
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: bold;
    color: #606266;
  }

  .card-icon {
    font-size: 20px;
  }

  .card-body {
    padding: 10px 0;
    text-align: center;

    .display-4 {
      font-size: 28px;
      font-weight: bold;
      color: #409EFF;
    }

    .text-success {
      color: #67C23A;
    }

    .text-danger {
      color: #F56C6C;
    }

    .text-info {
      font-size: 14px;
      color: #909399;
    }
  }

  .env-item {
    padding: 10px;
    background: #fff;
    border-radius: 4px;
    text-align: center;

    span {
      display: block;
      margin-bottom: 5px;
    }

    .text-muted {
      color: #909399;
      font-size: 12px;
    }

    .text-success {
      color: #67C23A;
      font-size: 18px;
      font-weight: bold;
    }
  }

  .table-card {
    border-radius: 8px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  }

  .tools-status {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
  }

  .backup-policy {
    font-size: 12px;
    color: #606266;
    margin-top: 5px;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .backup-age {
    font-size: 12px;
    color: #909399;
    margin-top: 2px;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .storage-item {
    margin: 8px 0;
    display: flex;
    align-items: baseline;

    .label {
      color: #909399;
      min-width: 90px;
      font-size: 13px;
    }

    .value {
      color: #303133;
      font-weight: 600;
      margin-right: 8px;
      font-size: 14px;
    }

    .ratio {
      color: #67C23A;
      font-size: 12px;
    }
  }

  .disk-details {
    margin-top: 12px;

    .disk-item {
      padding: 12px;
      background: #f8f9fa;
      border-radius: 4px;
      margin-bottom: 8px;

      .disk-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;

        .disk-seq {
          font-weight: 500;
          color: #303133;
        }

        .disk-id {
          font-size: 12px;
          color: #909399;
        }
      }

      .disk-progress {
        display: flex;
        align-items: center;

        .el-progress {
          flex: 1;
          margin-right: 12px;
        }

        .disk-usage {
          color: #606266;
          font-size: 12px;
          white-space: nowrap;
        }
      }

      .disk-meta {
        margin-top: 6px;
        font-size: 12px;
        color: #909399;

        .datastore {
          display: inline-flex;
          align-items: center;
          gap: 4px;
        }
      }
    }
  }

  .no-disk {
    text-align: center;
    color: #c0c4cc;
    padding: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
  }
}
</style>
