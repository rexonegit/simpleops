<template>
  <div class="nas-container">
    <!-- 列表页 -->
    <div v-if="!selectedNAS" class="list-view">
      <div class="filter-container">
        <el-input
          v-model="searchQuery"
          placeholder="搜索文件系统ID/描述"
          clearable
          style="width: 300px; margin-right: 10px;"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
        <el-button type="primary" :icon="Refresh" @click="refreshData">刷新</el-button>
        <el-button type="success" :icon="RefreshLeft" :loading="syncing" @click="syncNASData">
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
        <el-table-column label="文件系统ID" prop="file_system_id" sortable="custom" min-width="160" fixed="left">
          <template #default="{ row }">
            <el-link type="primary" @click="gotoDetail(row)">{{ row.file_system_id }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="文件系统名称 " prop="description" min-width="150" show-overflow-tooltip />
        <el-table-column label="所属项目" prop="project" min-width="150" sortable="custom" />
        <el-table-column label="环境" prop="environment" width="100" sortable="custom">
          <template #default="{ row }">
            <el-tag :type="getEnvTagType(row.environment)" size="small" v-if="row.environment">
              {{ getEnvLabel(row.environment) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="负责人" prop="owner" width="120" sortable="custom" />
        <el-table-column label="说明" prop="remark" min-width="150" show-overflow-tooltip />
        <el-table-column label="协议类型" prop="protocol_type" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.protocol_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="存储类型" prop="storage_type" width="120">
          <template #default="{ row }">
            <el-tag :type="getStorageTypeTag(row.storage_type)">
              {{ getStorageTypeLabel(row.storage_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" prop="status" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="地域" prop="region_id" width="120" />
        <el-table-column label="可用区" prop="zone_id" width="120" />
        <el-table-column label="容量(GB)" prop="capacity" width="100" />
        <el-table-column label="创建时间" prop="create_time" width="180" sortable="custom" />
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

    <!-- 详情页 -->
    <div v-else class="detail-view">
      <div class="detail-header">
        <el-button :icon="Back" @click="backToList">返回列表</el-button>
        <span class="header-title">{{ selectedNAS.file_system_id }}</span>
      </div>

      <el-card shadow="never" class="info-card">
        <template #header>
          <div class="card-header">基本信息</div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="文件系统ID">{{ nasDetail.file_system_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ nasDetail.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="协议类型">{{ nasDetail.protocol_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="存储类型">
            <el-tag :type="getStorageTypeTag(nasDetail.storage_type)">
              {{ getStorageTypeLabel(nasDetail.storage_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(nasDetail.status)">{{ nasDetail.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="地域">{{ nasDetail.region_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="可用区">{{ nasDetail.zone_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="容量">{{ nasDetail.capacity || 0 }} GB</el-descriptions-item>
          <el-descriptions-item label="带宽">{{ nasDetail.bandwidth || 0 }} MB/s</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ nasDetail.create_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="付费类型">{{ nasDetail.charge_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="过期时间">{{ nasDetail.expired_time || '-' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card shadow="never" class="info-card" style="margin-top: 20px;">
        <template #header>
          <div class="card-header">挂载点信息</div>
        </template>
        <el-table :data="nasDetail.mount_targets || []" border stripe>
          <el-table-column label="挂载点地址" prop="mount_target_domain" />
          <el-table-column label="网络类型" prop="network_type" />
          <el-table-column label="VPC ID" prop="vpc_id" />
          <el-table-column label="交换机ID" prop="vswitch_id" />
          <el-table-column label="状态" prop="status">
             <template #default="{ row }">
               <el-tag :type="row.status === 'Active' ? 'success' : 'warning'">{{ row.status }}</el-tag>
             </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="never" class="info-card" style="margin-top: 20px;">
        <template #header>
          <div class="card-header">标签</div>
        </template>
        <el-table :data="formatTags(nasDetail.tags)" border stripe>
          <el-table-column label="标签键" prop="key" align="center" />
          <el-table-column label="标签值" prop="value" align="center" />
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, RefreshLeft, Back } from '@element-plus/icons-vue'
import { fetchNASList, fetchNASDetail, syncNAS } from '@/api/aliyun/nas'

const list = ref([])
const listLoading = ref(true)
const syncing = ref(false)
const selectedNAS = ref(null)
const nasDetail = ref({})
const searchQuery = ref('')

const pagination = ref({ total: 0, current: 1, pageSize: 20 })
const listQuery = ref({
  sort: '+create_time'
})

const protocolTypeOptions = [
  { value: 'NFS', label: 'NFS' },
  { value: 'SMB', label: 'SMB' },
  { value: 'cpfs', label: 'CPFS' }
]

const storageTypeOptions = [
  { value: 'Capacity', label: '容量型' },
  { value: 'Performance', label: '性能型' },
  { value: 'standard', label: '标准型' },
  { value: 'advance', label: '高级型' }
]

const environmentOptions = [
  { label: '生产环境', value: 'prod' },
  { label: '测试环境', value: 'test' },
  { label: '开发环境', value: 'dev' },
  { label: '用户验收环境', value: 'uat' },
  { label: '预生产环境', value: 'stg' },
  { label: '灾备环境', value: 'dr' },
  { label: '其他', value: 'other' }
]

const getEnvLabel = (val) => {
  const item = environmentOptions.find(opt => opt.value === val)
  return item ? item.label : val
}

const getEnvTagType = (val) => {
  const map = { prod: 'danger', stg: 'warning', dr: 'warning', uat: 'primary', test: 'primary', dev: 'success', other: 'info' }
  return map[val] || 'info'
}

const getList = async () => {
  listLoading.value = true
  try {
    const params = {
      ...listQuery.value,
      search: searchQuery.value,
      page: pagination.value.current,
      page_size: pagination.value.pageSize
    }

    const res = await fetchNASList(params)

    if (res.code === 200) {
      const d = res.data || {}
      list.value = d.data || []
      pagination.value.total = d.total || 0
    } else {
      ElMessage.error(res.msg || '获取数据失败')
      list.value = []
      pagination.value.total = 0
    }
  } catch (err) {
    ElMessage.error('获取NAS列表失败')
    list.value = []
    pagination.value.total = 0
  } finally {
    listLoading.value = false
  }
}

const syncNASData = async () => {
  syncing.value = true
  try {
    const res = await syncNAS()

    if (res.status === 'success') {
      const failed = res.failed_accounts || []
      if (failed.length) {
        ElMessage.warning(`NAS 同步完成，成功 ${res.count} 条（跳过 ${failed.length} 个无权限账号）`)
      } else {
        ElMessage.success(`NAS 同步成功，共 ${res.count} 条`)
      }
    } else {
      ElMessage.warning(`NAS 同步完成：${JSON.stringify(res)}`)
    }
    getList()
  } catch (err) {
    ElMessage.info(`NAS 同步结果：${JSON.stringify(err.response?.data || err)}`)
  } finally {
    syncing.value = false
  }
}

const gotoDetail = async (row) => {
  selectedNAS.value = row
  listLoading.value = true
  try {
    const res = await fetchNASDetail(row.file_system_id)
    nasDetail.value = res?.data?.data || res?.data || res || {}
  } catch (err) {
    ElMessage.error('获取详情失败')
    nasDetail.value = {}
  } finally {
    listLoading.value = false
  }
}

const handleSearch = () => { pagination.value.current = 1; getList() }
const handlePageChange = (val) => { pagination.value.current = val; getList() }
const handleSizeChange = (val) => { pagination.value.pageSize = val; getList() }

const sortChange = ({ prop, order }) => {
  if (order === 'ascending') {
    listQuery.value.sort = `+${prop}`
  } else if (order === 'descending') {
    listQuery.value.sort = `-${prop}`
  } else {
    listQuery.value.sort = '+create_time'
  }
  handleSearch()
}

const refreshData = () => {
  searchQuery.value = ''
  listQuery.value = {
    sort: '+create_time'
  }
  handleSearch()
}



const backToList = () => {
  selectedNAS.value = null
  nasDetail.value = {}
}

const getStatusType = (status) => {
  const map = { 'Running': 'success', 'Pending': 'warning', 'Stopped': 'danger', 'Deleting': 'info' }
  return map[status] || 'info'
}

const getStorageTypeLabel = (type) => {
  const map = { 'Performance': '性能型', 'Capacity': '容量型', 'standard': '标准型', 'advance': '高级型' }
  return map[type] || type
}

const getStorageTypeTag = (type) => {
  const map = { 'Performance': 'success', 'Capacity': 'info', 'standard': 'warning', 'advance': 'danger' }
  return map[type] || 'info'
}

const formatTags = (tags) => {
  if (!tags) return []
  if (typeof tags === 'string') return []
  return Object.keys(tags).map(key => ({ key, value: tags[key] }))
}

onMounted(() => { getList() })
</script>

<style scoped>
.nas-container { padding: 20px; background-color: #f5f7fa; min-height: calc(100vh - 84px); }
.filter-container { display: flex; flex-wrap: wrap; align-items: center; margin-bottom: 20px; background: #fff; padding: 15px; border-radius: 4px; }
.pagination-container { margin-top: 20px; display: flex; justify-content: flex-end; background: #fff; padding: 10px; border-radius: 4px; }
.detail-header { display: flex; align-items: center; margin-bottom: 20px; background: #fff; padding: 15px; border-radius: 4px; }
.header-title { font-size: 18px; font-weight: bold; margin-left: 20px; }
.info-card { margin-bottom: 20px; }
.card-header { font-weight: bold; }
</style>
