<template>
  <div class="rds-container">
    <!-- ====================== 列表页 ====================== -->
    <div v-if="!selectedInstance" class="list-view">
      <div class="filter-container">
        <el-input
          v-model="listQuery.instanceId"
          placeholder="实例ID"
          clearable
          style="width: 200px; margin-right: 10px;"
          @keyup.enter="handleFilter"
        />
        <el-input
          v-model="listQuery.instanceName"
          placeholder="实例名称"
          clearable
          style="width: 200px; margin-right: 10px;"
          @keyup.enter="handleFilter"
        />
        <el-select
          v-model="listQuery.engine"
          placeholder="数据库引擎"
          clearable
          style="width: 180px; margin-right: 10px;"
        >
          <el-option v-for="item in engineOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select
          v-model="listQuery.status"
          placeholder="状态"
          clearable
          style="width: 140px; margin-right: 10px;"
        >
          <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>

        <el-button type="primary" :icon="Search" @click="handleFilter">搜索</el-button>
        <el-button :icon="Refresh" @click="refreshData">刷新</el-button>
        <el-button type="success" :icon="RefreshLeft" :loading="syncing" @click="syncRDSData">
          {{ syncing ? '同步中...' : '同步数据' }}
        </el-button>
      </div>

      <el-table
        v-loading="listLoading"
        :data="list"
        border
        stripe
        style="width: 100%; margin-top: 20px;"
        @sort-change="sortChange"
      >
        <el-table-column label="实例名称" prop="instance_name" min-width="200" fixed="left">
          <template #default="{ row }">
            <el-link type="primary" @click="gotoDetail(row)">{{ row.instance_name || '-' }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="所属项目" prop="project" min-width="150">
          <template #default="{ row }">
            <span>{{ row.project || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="环境类型" prop="environment" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.environment" :type="getEnvTagType(row.environment)" size="small">
              {{ getEnvLabel(row.environment) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="负责人" prop="owner" width="100">
          <template #default="{ row }">
            <span>{{ row.owner || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="说明" prop="description" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.description || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="实例ID" prop="instance_id" width="180" />
        <el-table-column label="引擎" width="160">
          <template #default="{ row }">
            <el-tag>{{ row.engine }} {{ row.engine_version }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="规格" prop="instance_class" width="180" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="连接地址" prop="connection_string" width="240" show-overflow-tooltip />
        <el-table-column label="端口" prop="port" width="90" />
        <el-table-column label="地域" prop="region_id" width="110" />
        <el-table-column label="可用区" prop="zone_id" width="110" />
        <el-table-column label="存储(GB)" prop="storage" width="100" />
        <el-table-column label="内存(GB)" prop="memory" width="100" />
        <el-table-column label="CPU(核)" prop="cpu" width="100" />
        <el-table-column label="付费类型" width="110">
          <template #default="{ row }">
            <el-tag :type="row.pay_type === 'Prepaid' ? 'success' : 'warning'">
              {{ row.pay_type === 'Prepaid' ? '包年包月' : '按量付费' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="creation_time" width="170" sortable="custom" />
        <el-table-column label="过期时间" prop="expire_time" width="170" sortable="custom" />
        <el-table-column label="更新时间" prop="updated_at" width="170" sortable="custom" />
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- ====================== 详情页 ====================== -->
    <div v-else class="detail-view">
      <div class="detail-header">
        <span class="header-title">{{ selectedInstance.instance_name }}</span>
        <el-button type="primary" :icon="Back" @click="backToList">
          返回列表
        </el-button>
      </div>

      <el-tabs v-model="activeTab">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="basic">
          <el-card shadow="never" class="info-card">
            <template #header><div class="card-header">基础信息</div></template>
            <el-descriptions :column="3" border>
              <el-descriptions-item label="实例ID">{{ instanceDetail.instance_id || '-' }}</el-descriptions-item>
              <el-descriptions-item label="实例名称">{{ instanceDetail.instance_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="引擎">{{ instanceDetail.engine }} {{ instanceDetail.engine_version }}</el-descriptions-item>
              <el-descriptions-item label="实例类型">{{ instanceDetail.instance_type || '-' }}</el-descriptions-item>
              <el-descriptions-item label="规格">{{ instanceDetail.instance_class || '-' }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(instanceDetail.status)">{{ instanceDetail.status || '-' }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="地域/可用区">{{ instanceDetail.region_id }} / {{ instanceDetail.zone_id }}</el-descriptions-item>
              <el-descriptions-item label="付费类型">
                <el-tag :type="instanceDetail.pay_type === 'Prepaid' ? 'success' : 'warning'">
                  {{ instanceDetail.pay_type === 'Prepaid' ? '包年包月' : '按量付费' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ formatTime(instanceDetail.creation_time) }}</el-descriptions-item>
              <el-descriptions-item label="过期时间">{{ formatTime(instanceDetail.expire_time) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ formatTime(instanceDetail.updated_at) }}</el-descriptions-item>
            </el-descriptions>
          </el-card>

          <el-card shadow="never" class="info-card" style="margin-top: 20px;">
            <template #header><div class="card-header">连接信息</div></template>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="内网地址">{{ instanceDetail.connection_string || '-' }}</el-descriptions-item>
              <el-descriptions-item label="端口">{{ instanceDetail.port || '-' }}</el-descriptions-item>
              <el-descriptions-item label="VPC ID">{{ instanceDetail.vpc_id || '-' }}</el-descriptions-item>
              <el-descriptions-item label="交换机ID">{{ instanceDetail.vswitch_id || '-' }}</el-descriptions-item>
              <el-descriptions-item label="白名单" :span="2">
                <el-tag v-for="ip in (instanceDetail.security_ips || '').split(',').filter(Boolean)" :key="ip" size="small" style="margin: 2px;">
                  {{ ip }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <el-card shadow="never" class="info-card" style="margin-top: 20px;">
            <template #header><div class="card-header">资源规格</div></template>
            <el-row :gutter="20">
              <el-col :span="6"><div class="stat-card"><div class="stat-title">存储(GB)</div><div class="stat-value">{{ instanceDetail.storage }}</div></div></el-col>
              <el-col :span="6"><div class="stat-card"><div class="stat-title">内存(GB)</div><div class="stat-value">{{ instanceDetail.memory }}</div></div></el-col>
              <el-col :span="6"><div class="stat-card"><div class="stat-title">CPU(核)</div><div class="stat-value">{{ instanceDetail.cpu }}</div></div></el-col>
            </el-row>
          </el-card>
        </el-tab-pane>

        <!-- 只读实例 -->
        <el-tab-pane
          v-if="instanceDetail.read_only_instances && instanceDetail.read_only_instances.length"
          label="只读实例"
          name="readonly"
        >
          <el-table :data="instanceDetail.read_only_instances" border stripe>
            <el-table-column label="实例ID" prop="id" width="180" />
            <el-table-column label="名称" prop="name" />
            <el-table-column label="状态">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="引擎" width="160">
              <template #default="{ row }">
                {{ row.engine }} {{ row.engine_version }}
              </template>
            </el-table-column>
            <el-table-column label="规格" prop="class" />
          </el-table>
        </el-tab-pane>

        <!-- 标签 -->
        <el-tab-pane label="标签" name="tags">
          <el-table :data="formatTags(instanceDetail.tags)" border stripe empty-text="暂无标签">
            <el-table-column label="标签键" prop="key" />
            <el-table-column label="标签值" prop="value" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, RefreshLeft, Back } from '@element-plus/icons-vue'
import { fetchRDSList, fetchRDSDetail, syncRDSInstances } from '@/api/aliyun/rds'

const list = ref([])
const listLoading = ref(false)
const syncing = ref(false)
const selectedInstance = ref(null)
const instanceDetail = ref({})
const activeTab = ref('basic')

const pagination = ref({
  total: 0,
  current: 1,
  pageSize: 20
})

const listQuery = ref({
  instanceId: '',
  instanceName: '',
  engine: '',
  status: '',
  sort: '-updated_at'
})

// 关键：加上 ref！
const engineOptions = ref([
  { label: 'MySQL', value: 'MySQL' },
  { label: 'SQLServer', value: 'SQLServer' },
  { label: 'PostgreSQL', value: 'PostgreSQL' },
  { label: 'MariaDB', value: 'MariaDB' },
  { label: 'PPAS', value: 'PPAS' }
])

const statusOptions = ref([
  { label: '运行中', value: 'Running' },
  { label: '创建中', value: 'Creating' },
  { label: '删除中', value: 'Deleting' },
  { label: '重启中', value: 'Rebooting' },
  { label: '升降级中', value: 'DBInstanceClassChanging' },
  { label: '迁移中', value: 'TRANSING' },
  { label: '版本升级中', value: 'EngineVersionUpgrading' }
])

// 关键：手动处理后端返回的 { code, data: { results, count } } 结构
const getList = async () => {
  listLoading.value = true
  try {
    const params = {
      ...listQuery.value,
      page: pagination.value.current,
      page_size: pagination.value.pageSize
    }

    // 注意：这里返回的是 { code: 200, data: { results, count, total, page, pageSize } }
    const response = await fetchRDSList(params)

    // 关键兼容代码：统一转成 el-table + el-pagination 能识别的格式
    if (response.code === 200) {
      const backendData = response.data || {}

      // 兼容两种字段：count 或 total
      list.value = backendData.results || backendData.data || []
      pagination.value.total = backendData.count || backendData.total || 0
    } else {
      ElMessage.error(response.msg || '获取数据失败')
      list.value = []
      pagination.value.total = 0
    }
  } catch (err) {
    console.error(err)
    ElMessage.error('请求异常')
    list.value = []
    pagination.value.total = 0
  } finally {
    listLoading.value = false
  }
}

const gotoDetail = (row) => {
  selectedInstance.value = row
  getRDSDetail(row.instance_id)
}

const getRDSDetail = async (instanceId) => {
  listLoading.value = true
  try {
    const res = await fetchRDSDetail(instanceId)
    if (res.code === 200) {
      instanceDetail.value = res.data
    } else {
      ElMessage.error(res.msg || '获取详情失败')
    }
  } catch (err) {
    ElMessage.error('获取实例详情失败')
    console.error('RDS 详情请求异常:', err)
  } finally {
    listLoading.value = false
  }
}

// 同步也一样
const syncRDSData = async () => {
  syncing.value = true
  try {
    const response = await syncRDSInstances()
    if (response.code === 200) {
      ElMessage.success(response.msg || '同步成功')
      getList()
    } else {
      ElMessage.error(response.msg || '同步失败')
    }
  } catch (err) {
    ElMessage.error('同步异常')
  } finally {
    syncing.value = false
  }
}

// 其他代码保持不变...
const handleFilter = () => {
  pagination.value.current = 1
  getList()
}

const handlePageChange = (val) => {
  pagination.value.current = val
  getList()
}

const handleSizeChange = (val) => {
  pagination.value.pageSize = val
  getList()
}

const sortChange = ({ prop, order }) => {
  listQuery.value.sort = order === 'ascending' ? `+${prop}` : order === 'descending' ? `-${prop}` : '-updated_at'
  handleFilter()
}

const refreshData = () => {
  listQuery.value = { instanceId: '', instanceName: '', engine: '', status: '', sort: '-updated_at' }
  pagination.value.current = 1
  getList()
}


const backToList = () => {
  selectedInstance.value = null
  instanceDetail.value = {}
}

// ====================== 工具函数 ======================
const getStatusType = (status) => {
  const map = {
    Running: 'success',
    Creating: 'primary',
    Deleting: 'danger',
    Rebooting: 'warning',
    DBInstanceClassChanging: 'warning',
    TRANSING: 'info',
    EngineVersionUpgrading: 'info'
  }
  return map[status] || 'info'
}

// 环境类型帮助函数
const envLabelMap = {
  prod: '生产环境',
  test: '测试环境',
  dev: '开发环境',
  uat: '用户验收环境',
  stg: '预生产环境',
  dr: '灾备环境',
  other: '其他'
}

const getEnvLabel = (envCode) => {
  return envLabelMap[envCode] || envCode || '-'
}

const getEnvTagType = (envCode) => {
  const map = { prod: 'danger', stg: 'warning', dr: 'warning', uat: 'primary', test: 'primary', dev: 'success', other: 'info' }
  return map[envCode] || 'info'
}

const formatTime = (time) => {
  if (!time) return '-'
  const d = new Date(time)
  return isNaN(d.getTime()) ? time : d.toLocaleString('zh-CN', { hour12: false })
}

const formatTags = (tags) => {
  if (!tags || typeof tags !== 'object') return []
  return Object.entries(tags).map(([key, value]) => ({ key, value }))
}

onMounted(() => {
  getList()
})
</script>

<style scoped>
.rds-container { padding: 20px; background: #f5f7fa; min-height: calc(100vh - 84px); }
.filter-container { display: flex; flex-wrap: wrap; gap: 10px; background: #fff; padding: 15px; border-radius: 6px; margin-bottom: 20px; }
.pagination-container { margin-top: 20px; display: flex; justify-content: flex-end; background: #fff; padding: 10px; border-radius: 6px; }
.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(0,0,0,.04);
}

.header-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}
.info-card { margin-bottom: 20px; }
.card-header { font-weight: bold; color: #303133; }
.stat-card { background: #fff; border: 1px solid #ebeef5; border-radius: 6px; padding: 20px; text-align: center; }
.stat-title { font-size: 14px; color: #909399; margin-bottom: 8px; }
.stat-value { font-size: 28px; font-weight: bold; color: #303133; }
</style>
