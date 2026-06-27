<template>
  <div class="waf-container">
    <!-- 列表页 -->
    <div v-if="!selectedWAF" class="list-view">
      <div class="filter-container">
        <el-input
          v-model="listQuery.instanceId"
          placeholder="实例ID"
          style="width: 200px; margin-right: 10px;"
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
          v-model="listQuery.instanceType"
          placeholder="付费类型"
          clearable
          style="width: 130px; margin-right: 10px;"
        >
          <el-option v-for="item in instanceTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="handleFilter">搜索</el-button>
        <el-button type="primary" :icon="Refresh" @click="refreshData">刷新</el-button>
        <el-button type="success" :icon="RefreshLeft" :loading="syncing" @click="syncWAFData">
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
        <el-table-column label="实例ID" prop="instance_id" sortable="custom" min-width="280" fixed="left">
          <template #default="{ row }">
            <el-link type="primary" @click="gotoDetail(row)">{{ row.instance_id }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="状态" prop="status" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusDisplay(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="域名数量" prop="domain_count" width="100" />
        <el-table-column label="基础QPS" prop="qps" width="100" />
        <el-table-column label="弹性QPS" prop="elastic_qps" width="100" />
        <el-table-column label="流量套餐" prop="traffic_package" width="150" />
        <el-table-column label="开始时间" prop="start_time" width="160" sortable="custom" />
        <el-table-column label="到期时间" prop="end_time" width="160" sortable="custom" />
        <el-table-column label="更新时间" prop="updated_at" width="160" sortable="custom" />
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
        <span class="header-title">WAF 实例详情</span>
      </div>

      <el-card shadow="never" class="info-card">
        <template #header>
          <div class="card-header">基本信息</div>
        </template>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="实例ID">{{ wafDetail.instance_id }}</el-descriptions-item>
          <el-descriptions-item label="所属账号">{{ wafDetail.account_name }}</el-descriptions-item>
          <el-descriptions-item label="地域">{{ wafDetail.region_id }}</el-descriptions-item>
          <el-descriptions-item label="付费类型">
            <el-tag :type="wafDetail.pay_type === 'PREPAY' ? 'success' : 'warning'">
              {{ wafDetail.pay_type_display }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="WAF版本">{{ wafDetail.edition }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(wafDetail.status)">{{ wafDetail.status_display }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ wafDetail.start_time }}</el-descriptions-item>
          <el-descriptions-item label="到期时间">{{ wafDetail.end_time }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card shadow="never" class="info-card" style="margin-top: 20px;">
        <template #header>
          <div class="card-header">能力支持</div>
        </template>
        <el-row :gutter="20">
          <el-col v-for="(cap, index) in wafDetail.capabilities" :key="index" :span="4" style="margin-bottom: 10px;">
            <el-tag type="success" effect="plain"><el-icon><Select /></el-icon> {{ cap }}</el-tag>
          </el-col>
          <el-col v-if="!wafDetail.capabilities || !wafDetail.capabilities.length" :span="24">
            <span style="color: #909399;">暂无高级能力</span>
          </el-col>
        </el-row>
      </el-card>

      <el-card shadow="never" class="info-card" style="margin-top: 20px;">
        <template #header>
          <div class="card-header">规格详情</div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="域名数量">{{ wafDetail.details?.domain_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="基础QPS">{{ wafDetail.details?.qps || 0 }}</el-descriptions-item>
          <el-descriptions-item label="弹性QPS">{{ wafDetail.details?.elastic_qps || 0 }}</el-descriptions-item>
          <el-descriptions-item label="流量套餐">{{ wafDetail.details?.traffic_package || '无' }}</el-descriptions-item>
          <el-descriptions-item label="日志存储">{{ wafDetail.details?.log_storage || 0 }} GB</el-descriptions-item>
          <el-descriptions-item label="带宽">{{ wafDetail.details?.bandwidth || 0 }} Mbps</el-descriptions-item>
          <el-descriptions-item label="HTTP端口">{{ wafDetail.details?.HttpPorts || '80,8080' }}</el-descriptions-item>
          <el-descriptions-item label="HTTPS端口">{{ wafDetail.details?.HttpsPorts || '443,8443' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, RefreshLeft, Back, Select } from '@element-plus/icons-vue'
import { fetchWAFList, fetchWAFDetail, syncWAF } from '@/api/aliyun/waf'

const list = ref([])
const listLoading = ref(true)
const syncing = ref(false)
const selectedWAF = ref(null)
const wafDetail = ref({})

const pagination = ref({ total: 0, current: 1, pageSize: 20 })
const listQuery = ref({
  instanceId: undefined,
  instanceName: undefined,
  status: undefined,
  instanceType: undefined,
  sort: '+end_time'
})

const statusOptions = [
  { value: 1, label: '正常' },
  { value: 0, label: '过期' },
  { value: -1, label: '释放' }
]

const instanceTypeOptions = [
  { value: 'PREPAY', label: '包年包月' },
  { value: 'POSTPAY', label: '按量付费' }
]

const getList = async () => {
  listLoading.value = true
  try {
    const params = {
      ...listQuery.value,
      page: pagination.value.current,
      page_size: pagination.value.pageSize
    }

    const res = await fetchWAFList(params)

    // 关键修复：兼容你现在的返回结构
    if (res.code === 200) {
      const backendData = res.data || {}
      list.value = backendData.data || []        // 注意这里是 data.data！
      pagination.value.total = backendData.total || 0
    } else {
      ElMessage.error(res.msg || '获取列表失败')
      list.value = []
      pagination.value.total = 0
    }
  } catch (err) {
    console.error(err)
    ElMessage.error('获取WAF列表失败')
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
    listQuery.value.sort = '+end_time'
  }
  handleFilter()
}

const refreshData = () => {
  listQuery.value = {
    instanceId: undefined,
    instanceName: undefined,
    status: undefined,
    instanceType: undefined,
    sort: '+end_time'
  }
  handleFilter()
}

const syncWAFData = async () => {
  syncing.value = true
  try {
    const res = await syncWAF()        // 关键：拿到返回值

    // 直接把后端原样返回的内容展示给用户！清晰明了！
    if (res.status === 'success') {
      ElMessage.success(`WAF 同步成功！共 ${res.count} 条${res.failed_accounts?.length ? `（跳过 ${res.failed_accounts.length} 个无权限账号）` : ''}`)
    } else {
      // 即使不是 success，也把真实内容显示出来
      ElMessage.warning(`WAF 同步完成：${JSON.stringify(res)}`)
    }
    getList()
  } catch (err) {
    // 啥都不管，直接把原始返回甩给用户
    ElMessage.info(`WAF 同步结果：${JSON.stringify(err.response?.data || err)}`)
    console.log('原始返回:', err.response?.data)
  } finally {
    syncing.value = false
  }
}

const gotoDetail = async (row) => {
  selectedWAF.value = row
  listLoading.value = true
  try {
    const res = await fetchWAFDetail(row.instance_id)

    // 兼容所有可能的返回结构
    wafDetail.value = res?.data?.data || res?.data || res || {}

  } catch (err) {
    console.error('WAF 详情请求异常', err)
    ElMessage.error('获取详情失败')
    wafDetail.value = {}
  } finally {
    listLoading.value = false
  }
}

const backToList = () => {
  selectedWAF.value = null
  wafDetail.value = {}
}

const getStatusType = (status) => {
  const map = { 1: 'success', 0: 'warning', '-1': 'danger' }
  return map[status] || 'info'
}

const getStatusDisplay = (status) => {
  const map = { 1: '正常', 0: '过期', '-1': '释放' }
  return map[status] || status
}

onMounted(() => { getList() })
</script>

<style scoped>
.waf-container { padding: 20px; background-color: #f5f7fa; min-height: calc(100vh - 84px); }
.filter-container { display: flex; flex-wrap: wrap; align-items: center; margin-bottom: 20px; background: #fff; padding: 15px; border-radius: 4px; }
.pagination-container { margin-top: 20px; display: flex; justify-content: flex-end; background: #fff; padding: 10px; border-radius: 4px; }
.detail-header { display: flex; align-items: center; margin-bottom: 20px; background: #fff; padding: 15px; border-radius: 4px; }
.header-title { font-size: 18px; font-weight: bold; margin-left: 20px; }
.info-card { margin-bottom: 20px; }
.card-header { font-weight: bold; }
</style>
