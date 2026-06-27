<template>
  <div class="eip-container">
    <!-- 列表页 -->
    <div v-if="!selectedEIP" class="list-view">
      <div class="filter-container">
        <el-input
          v-model="listQuery.search"
          placeholder="搜索IP地址/EIP ID/名称/绑定实例"
          style="width: 300px; margin-right: 10px;"
          clearable
          @keyup.enter="handleFilter"
        />
        <el-select
          v-model="listQuery.status"
          placeholder="状态"
          clearable
          style="width: 120px; margin-right: 10px;"
        >
          <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select
          v-model="listQuery.internetChargeType"
          placeholder="计费方式"
          clearable
          style="width: 130px; margin-right: 10px;"
        >
          <el-option v-for="item in chargeTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="handleFilter">搜索</el-button>
        <el-button type="primary" :icon="Refresh" @click="refreshData">刷新</el-button>
        <el-button type="success" :icon="RefreshLeft" :loading="syncing" @click="syncEIPData">
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
        <el-table-column label="IP地址" prop="ip_address" sortable="custom" min-width="140" fixed="left">
          <template #default="{ row }">
            <el-link type="primary" @click="gotoDetail(row)">{{ row.ip_address }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="EIP ID" prop="allocation_id" width="180" />
        <el-table-column label="名称" prop="name" width="120" />
        <el-table-column label="状态" prop="status" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="带宽峰值(Mbps)" prop="bandwidth" width="140" />
        <el-table-column label="计费方式" prop="internet_charge_type" width="120">
          <template #default="{ row }">
            <el-tag :type="row.internet_charge_type === 'PayByTraffic' ? 'success' : 'warning'">
              {{ getChargeTypeDisplay(row.internet_charge_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="绑定的实例" prop="instance_id" width="180" />
        <el-table-column label="实例类型" prop="instance_type" width="120" />
        <el-table-column label="地域" prop="region_id" width="120" />
        <el-table-column label="创建时间" prop="allocation_time" width="180" sortable="custom" />
        <el-table-column label="过期时间" prop="expired_time" width="180" sortable="custom" />
        <el-table-column label="当月流量(GB)" prop="monthly_flow" width="120" />
        <el-table-column label="当月请求数" prop="monthly_requests" width="120" />
        <el-table-column label="更新时间" prop="updated_at" width="180" sortable="custom" />
        <el-table-column label="所属账号" prop="account_name" width="180" sortable="custom" />
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
        <span class="header-title">{{ selectedEIP.ip_address }}</span>
      </div>

      <el-card shadow="never" class="info-card">
        <template #header>
          <div class="card-header">基本信息</div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="EIP ID">{{ eipDetail.allocation_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="名称">{{ eipDetail.name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(eipDetail.status)">{{ eipDetail.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="IP地址">{{ eipDetail.ip_address || '-' }}</el-descriptions-item>
          <el-descriptions-item label="带宽峰值(Mbps)">{{ eipDetail.bandwidth || '-' }}</el-descriptions-item>
          <el-descriptions-item label="计费方式">
            <el-tag :type="eipDetail.internet_charge_type === 'PayByTraffic' ? 'success' : 'warning'">
              {{ getChargeTypeDisplay(eipDetail.internet_charge_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="地域">{{ eipDetail.region_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ eipDetail.allocation_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="过期时间">{{ eipDetail.expired_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ eipDetail.updated_at || '-' }}</el-descriptions-item>
          <el-descriptions-item label="绑定的实例ID">{{ eipDetail.instance_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="实例类型">{{ eipDetail.instance_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="当月流量(GB)">{{ eipDetail.monthly_flow || '-' }}</el-descriptions-item>
          <el-descriptions-item label="当月请求数">{{ eipDetail.monthly_requests || '-' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card shadow="never" class="info-card" style="margin-top: 20px;">
        <template #header>
          <div class="card-header">标签</div>
        </template>
        <el-table :data="formatTags(eipDetail.tags)" border stripe>
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
import { fetchEIPList, fetchEIPDetail, syncEIPs } from '@/api/aliyun/eip'

const list = ref([])
const listLoading = ref(true)
const syncing = ref(false)
const selectedEIP = ref(null)
const eipDetail = ref({})

const pagination = ref({ total: 0, current: 1, pageSize: 20 })
const listQuery = ref({
  search: undefined,
  status: undefined,
  internetChargeType: undefined,
  sort: '+updated_at'
})

const statusOptions = [
  { value: 'Available', label: '可用' },
  { value: 'InUse', label: '已绑定' },
  { value: 'Associating', label: '绑定中' },
  { value: 'Unassociating', label: '解绑中' }
]

const chargeTypeOptions = [
  { value: 'PayByBandwidth', label: '按带宽计费' },
  { value: 'PayByTraffic', label: '按流量计费' }
]

const getList = async () => {
  listLoading.value = true
  try {
    const params = {
      ...listQuery.value,
      page: pagination.value.current,
      page_size: pagination.value.pageSize
    }
    const res = await fetchEIPList(params)

    // 关键修复：根据你的真实接口结构来取数据
    const resData = res.data || res  // 兼容 axios 和直接返回的情况

    // 正确路径：resData.data.data 是列表，resData.data.total 是总数
    const listData = resData.data?.data || resData.data || []
    const totalCount = resData.data?.total || resData.data?.count || 0

    list.value = listData
    pagination.value.total = totalCount

    // 可选：如果你后端还返回了当前页和页大小，也可以同步一下
    if (resData.data?.page) pagination.value.current = resData.data.page
    if (resData.data?.pageSize) pagination.value.pageSize = resData.data.pageSize

  } catch (err) {
    console.error(err)
    ElMessage.error('获取EIP列表失败')
    list.value = []
    pagination.value.total = 0
  } finally {
    listLoading.value = false
  }
}

const handleFilter = () => { pagination.value.current = 1; getList() }
const handlePageChange = (val) => { pagination.value.current = val; getList() }
const handleSizeChange = (val) => { pagination.value.pageSize = val; getList() }

const sortChange = ({ prop, order }) => {
  if (order === 'ascending') {
    listQuery.value.sort = `+${prop}`
  } else if (order === 'descending') {
    listQuery.value.sort = `-${prop}`
  } else {
    listQuery.value.sort = '+updated_at'
  }
  handleFilter()
}

const refreshData = () => {
  listQuery.value = {
    search: undefined,
    status: undefined,
    internetChargeType: undefined,
    sort: '+updated_at'
  }
  handleFilter()
}

const syncEIPData = async () => {
  syncing.value = true
  try {
    await syncEIPs()
    ElMessage.success('同步EIP数据成功')
    getList()
  } catch (err) {
    ElMessage.error('同步EIP数据失败')
  } finally {
    syncing.value = false
  }
}

const gotoDetail = async (row) => {
  selectedEIP.value = row
  listLoading.value = true
  try {
    const res = await fetchEIPDetail(row.allocation_id)
    eipDetail.value = res.data || res
  } catch (err) {
    ElMessage.error('获取详情失败')
  } finally {
    listLoading.value = false
  }
}

const backToList = () => {
  selectedEIP.value = null
  eipDetail.value = {}
}

const getStatusType = (status) => {
  const map = { 'Available': 'success', 'InUse': 'primary', 'Associating': 'warning', 'Unassociating': 'info' }
  return map[status] || 'info'
}

const getChargeTypeDisplay = (type) => {
  const map = { 'PayByBandwidth': '按带宽计费', 'PayByTraffic': '按流量计费' }
  return map[type] || type
}

const formatTags = (tags) => {
  if (!tags) return []
  if (typeof tags === 'string') return []
  return Object.keys(tags).map(key => ({ key, value: tags[key] }))
}

onMounted(() => { getList() })
</script>

<style scoped>
.eip-container { padding: 20px; background-color: #f5f7fa; min-height: calc(100vh - 84px); }
.filter-container { display: flex; flex-wrap: wrap; align-items: center; margin-bottom: 20px; background: #fff; padding: 15px; border-radius: 4px; }
.pagination-container { margin-top: 20px; display: flex; justify-content: flex-end; background: #fff; padding: 10px; border-radius: 4px; }
.detail-header { display: flex; align-items: center; margin-bottom: 20px; background: #fff; padding: 15px; border-radius: 4px; }
.header-title { font-size: 18px; font-weight: bold; margin-left: 20px; }
.info-card { margin-bottom: 20px; }
.card-header { font-weight: bold; }
</style>
