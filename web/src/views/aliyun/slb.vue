<template>
  <div class="slb-container">
    <!-- 列表页 -->
    <div v-if="!selectedSLB" class="list-view">
      <div class="filter-container">
        <el-input
          v-model="searchQuery"
          placeholder="搜索ID/名称/地址"
          style="width: 300px; margin-right: 10px;"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
        <el-button type="primary" :icon="Refresh" @click="refreshData">刷新</el-button>
        <el-button type="success" :icon="RefreshLeft" :loading="syncing" @click="syncSLBData">
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
        <el-table-column label="ID" prop="load_balancer_id" min-width="180" fixed="left">
          <template #default="{ row }">
            <el-link type="primary" @click="gotoDetail(row)">{{ row.load_balancer_id }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="名称" prop="load_balancer_name" min-width="150" />
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
        <el-table-column label="地址" prop="address" width="140" />
        <el-table-column label="地域" prop="region_id" width="120" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.address_type === 'internet' ? '公网' : '内网' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
              {{ row.status === 'active' ? '运行中' : '已停止' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="监听端口" width="150">
          <template #default="{ row }">
            <el-tag v-for="port in row.listener_ports" :key="port" style="margin: 2px;" size="small">
              {{ port }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="后端服务器" width="100">
          <template #default="{ row }">
            {{ row.backend_servers ? row.backend_servers.length : 0 }} 台
          </template>
        </el-table-column>
        <el-table-column label="带宽" prop="bandwidth" width="120">
          <template #default="{ row }">
            {{ row.bandwidth }} Mbps
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="creation_time" width="180" sortable="custom" />
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
        <span class="header-title">{{ selectedSLB.load_balancer_name }} ({{ selectedSLB.load_balancer_id }})</span>
      </div>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="概览" name="overview">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-card shadow="never" class="info-card">
                <template #header>
                  <div class="card-header">基本信息</div>
                </template>
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="ID">{{ selectedSLB.load_balancer_id || '-' }}</el-descriptions-item>
                  <el-descriptions-item label="名称">{{ selectedSLB.load_balancer_name || '-' }}</el-descriptions-item>
                  <el-descriptions-item label="地域">{{ selectedSLB.region_id || '-' }}</el-descriptions-item>
                  <el-descriptions-item label="地址">{{ selectedSLB.address || '-' }}</el-descriptions-item>
                  <el-descriptions-item label="类型">
                    <el-tag size="small">{{ selectedSLB.address_type === 'internet' ? '公网' : '内网' }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="状态">
                    <el-tag size="small" :type="selectedSLB.status === 'active' ? 'success' : 'danger'">
                      {{ selectedSLB.status === 'active' ? '运行中' : '已停止' }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="创建时间">{{ selectedSLB.creation_time || '-' }}</el-descriptions-item>
                </el-descriptions>
              </el-card>
            </el-col>

            <el-col :span="16">
              <el-card shadow="never" class="info-card">
                <template #header>
                  <div class="card-header">监控信息</div>
                </template>
                <el-row :gutter="20">
                  <el-col :span="12">
                    <div class="stat-card">
                      <div class="stat-title">当月流量</div>
                      <div class="stat-value">{{ selectedSLB.monthly_flow || 0 }}</div>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div class="stat-card">
                      <div class="stat-title">当月请求数</div>
                      <div class="stat-value">{{ selectedSLB.monthly_requests || 0 }}</div>
                    </div>
                  </el-col>
                </el-row>
              </el-card>

              <el-card shadow="never" style="margin-top: 20px;">
                <template #header>
                  <div class="card-header">后端服务器</div>
                </template>
                <el-table :data="selectedSLB.backend_servers" border stripe>
                  <el-table-column label="实例ID" prop="server_id" />
                  <el-table-column label="权重" prop="weight" />
                  <el-table-column label="健康状态">
                    <template #default="{ row }">
                      <el-tag :type="row.health_status === 'normal' ? 'success' : 'danger'">
                        {{ row.health_status === 'normal' ? '正常' : '异常' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="监听配置" name="listeners">
          <!-- 监听器配置详情 -->
           <div style="padding: 20px; text-align: center; color: #909399;">暂无详细监听配置信息</div>
        </el-tab-pane>

        <el-tab-pane label="标签" name="tags">
          <el-table :data="tagsData" border stripe>
            <el-table-column label="标签键" prop="key" />
            <el-table-column label="标签值" prop="value" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, RefreshLeft, Back } from '@element-plus/icons-vue'
import { fetchSLBList, fetchSLBDetail, syncSLB } from '@/api/aliyun/slb'

const list = ref([])
const listLoading = ref(true)
const syncing = ref(false)
const selectedSLB = ref(null)
const activeTab = ref('overview')
const searchQuery = ref('')

const pagination = ref({ total: 0, current: 1, pageSize: 20 })
const listQuery = ref({ sort: '-updated_at' })

const regionOptions = [
  { label: '华东1 (杭州)', value: 'cn-hangzhou' },
  { label: '华东2 (上海)', value: 'cn-shanghai' },
  { label: '华北1 (青岛)', value: 'cn-qingdao' },
  { label: '华北2 (北京)', value: 'cn-beijing' },
  { label: '华南1 (深圳)', value: 'cn-shenzhen' }
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

const tagsData = computed(() => {
  if (!selectedSLB.value || !selectedSLB.value.tags) return []
  return Object.entries(selectedSLB.value.tags).map(([key, value]) => ({ key, value }))
})

const getList = async () => {
  listLoading.value = true
  try {
    const params = {
      ...listQuery.value,
      search: searchQuery.value,
      page: pagination.value.current,
      page_size: pagination.value.pageSize
    }

    const res = await fetchSLBList(params)

    // 关键修复：兼容你现在的返回结构（和 RDS/WAF 完全一致）
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
    ElMessage.error('获取SLB列表失败')
    list.value = []
    pagination.value.total = 0
  } finally {
    listLoading.value = false
  }
}

const handleSearch = () => { pagination.value.current = 1; getList() }
const handlePageChange = (val) => { pagination.value.current = val; getList() }
const handleSizeChange = (val) => { pagination.value.pageSize = val; getList() }
const sortChange = ({ prop, order }) => {
  listQuery.value.sort = order === 'ascending' ? `+${prop}` : (order === 'descending' ? `-${prop}` : undefined)
  handleSearch()
}

const refreshData = () => {
  searchQuery.value = ''
  listQuery.value = { sort: '-updated_at' }
  handleSearch()
}

const syncSLBData = async () => {
  syncing.value = true
  try {
    await syncSLB()
    ElMessage.success('同步成功')
    getList()
  } catch (err) {
    ElMessage.error('同步失败')
  } finally {
    syncing.value = false
  }
}

const gotoDetail = async (row) => {
  selectedSLB.value = row
  try {
    const res = await fetchSLBDetail(row.load_balancer_id)

    // 万能兼容：不管返回什么结构，都能拿到数据
    selectedSLB.value = res?.data?.data || res?.data || res || {}
  } catch (err) {
    console.error('获取SLB详情失败', err)
    ElMessage.error('获取详情失败')
    selectedSLB.value = {}
  }
}
const backToList = () => { selectedSLB.value = null }

onMounted(() => { getList() })
</script>

<style scoped>
.slb-container { padding: 20px; background-color: #f5f7fa; min-height: calc(100vh - 84px); }
.filter-container { display: flex; flex-wrap: wrap; align-items: center; margin-bottom: 20px; background: #fff; padding: 15px; border-radius: 4px; }
.pagination-container { margin-top: 20px; display: flex; justify-content: flex-end; background: #fff; padding: 10px; border-radius: 4px; }
.detail-header { display: flex; align-items: center; margin-bottom: 20px; background: #fff; padding: 15px; border-radius: 4px; }
.header-title { font-size: 18px; font-weight: bold; margin-left: 20px; }
.info-card { margin-bottom: 20px; }
.card-header { font-weight: bold; }
.stat-card { border: 1px solid #ebeef5; border-radius: 4px; padding: 20px; text-align: center; background: #fff; }
.stat-title { font-size: 14px; color: #909399; margin-bottom: 10px; }
.stat-value { font-size: 24px; font-weight: bold; color: #303133; }
</style>
