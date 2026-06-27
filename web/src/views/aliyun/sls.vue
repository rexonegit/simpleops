<template>
  <div class="sls-container">
    <!-- ====================== 列表页 ====================== -->
    <div v-if="!selectedProject" class="list-view">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="left">
          <span class="title">阿里云 SLS 日志服务</span>
        </div>
        <div class="right">
          <el-input
            v-model="listQuery.search"
            placeholder="搜索 Project / 描述"
            clearable
            style="width: 300px; margin-right: 10px;"
            @keyup.enter="handleFilter"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="success" :icon="RefreshLeft" :loading="syncing" @click="syncSLS">
            {{ syncing ? '同步中...' : '同步 SLS' }}
          </el-button>
        </div>
      </div>

      <!-- 表格 -->
      <el-table
        v-loading="listLoading"
        :data="tableData"
        stripe
        border
        style="width: 100%; margin-top: 20px;"
      >
        <el-table-column prop="project_name" label="Project 名称" min-width="200" fixed="left">
          <template #default="{ row }">
            <el-link type="primary" @click="gotoDetail(row)">{{ row.project_name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="所属项目" prop="project" min-width="150" sortable />
        <el-table-column label="环境" prop="environment" width="100" sortable>
          <template #default="{ row }">
            <el-tag :type="getEnvTagType(row.environment)" size="small" v-if="row.environment">
              {{ getEnvLabel(row.environment) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="负责人" prop="owner" width="120" sortable />
        <el-table-column label="说明" prop="remark" min-width="150" show-overflow-tooltip />
        <el-table-column prop="account_name" label="所属账号" width="140" />
        <el-table-column prop="region_id" label="地域" width="120" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <!-- 修正状态判断 -->
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'Normal' ? 'success' : 'danger'">
              {{ row.status === 'Normal' ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="LogStore 数量" width="130">
          <template #default="{ row }">
            {{ row.logstores?.length || 0 }} 个
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="create_time" width="170" />
        <el-table-column label="更新时间" prop="updated_at" width="170" />
      </el-table>

      <!-- 分页 -->
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
        <el-button :icon="Back" @click="backToList">返回列表</el-button>
        <span class="header-title">{{ selectedProject.project_name }}</span>

      </div>


      <!-- 修改 tabs 配置，添加 lazy 属性并使用 v-if -->
      <el-tabs v-model="activeTab" @tab-click="handleTabClick">
  <!-- 基础信息标签页 -->
  <el-tab-pane label="基础信息" name="basic" :lazy="true">
    <el-card shadow="never" class="info-card">
      <template #header>
        <div class="card-header">基本信息</div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="Project 名称">{{ selectedProject.project_name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="selectedProject.status === 'Normal' ? 'success' : 'danger'">
            {{ selectedProject.status === 'Normal' ? '正常' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="所属账号">{{ selectedProject.account_name }}</el-descriptions-item>
        <el-descriptions-item label="地域">{{ selectedProject.region_id }}</el-descriptions-item>
        <el-descriptions-item label="数据冗余类型">
          {{ selectedProject.data_redundancy_type === 'ZRS' ? '同城冗余(ZRS)' : '本地冗余(LRS)' }}
        </el-descriptions-item>
        <el-descriptions-item label="回收站">
          <el-tag :type="selectedProject.recycle_bin_enabled ? 'success' : 'info'">
            {{ selectedProject.recycle_bin_enabled ? '已开启' : '未开启' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="描述">{{ selectedProject.description || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(selectedProject.create_time) }}</el-descriptions-item>
        <el-descriptions-item label="最后修改时间">{{ formatTime(selectedProject.last_modify_time) }}</el-descriptions-item>
        <el-descriptions-item label="同步时间">{{ formatTime(selectedProject.updated_at) }}</el-descriptions-item>
        <el-descriptions-item label="公网域名">{{ `${selectedProject.region_id}.log.aliyuncs.com` }}</el-descriptions-item>
        <el-descriptions-item label="私网域名">{{ `${selectedProject.region_id}-intranet.log.aliyuncs.com` }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </el-tab-pane>

  <!-- LogStore列表标签页 -->
  <el-tab-pane label="LogStore列表" name="logstores" :lazy="true">
    <el-card shadow="never" style="margin-top: 0;">
      <template #header>
        <div class="card-header">LogStore 列表（{{ selectedProject.logstores?.length || 0 }} 个）</div>
      </template>

      <!-- LogStore 详细表格 -->
      <el-table
        :data="selectedProject.logstores || []"
        border stripe
        v-loading="detailLoading"
        @row-click="(row) => { currentLogStore = row; showLogStoreDetail = true }"
        style="cursor: pointer;"
      >
        <el-table-column prop="logstore_name" label="LogStore 名称" min-width="180" fixed="left" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.mode === 'standard' ? '' : 'info'">
              {{ row.mode === 'standard' ? '标准型' : '查询型' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="存储配置" width="220">
          <template #default="{ row }">
            <div>TTL: {{ row.ttl }} 天</div>
            <div v-if="row.hot_ttl">热层: {{ row.hot_ttl }} 天</div>
            <div v-if="row.infrequent_access_ttl">低频: {{ row.infrequent_access_ttl }} 天</div>
          </template>
        </el-table-column>
        <el-table-column label="分片配置" width="180">
          <template #default="{ row }">
            <div>分片数: {{ row.shard_count }}</div>
            <div v-if="row.auto_split">自动分裂: 是 (最大 {{ row.max_split_shard }})</div>
            <div v-else>自动分裂: 否</div>
          </template>
        </el-table-column>
        <el-table-column label="功能开关" width="180">
          <template #default="{ row }">
            <div>WebTracking: {{ row.enable_tracking ? '开' : '关' }}</div>
            <div>记录外网IP: {{ row.append_meta ? '开' : '关' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="telemetry_type" label="日志类型" width="100" />
        <el-table-column prop="product_type" label="产品类型" width="120" />
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ formatTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="viewLogStoreDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- LogStore 详细信息面板 -->
      <el-collapse-transition>
        <div v-if="showLogStoreDetail && currentLogStore" style="margin-top: 20px;">
          <el-card shadow="never" class="detail-card">
            <template #header>
              <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                <span>LogStore 详情: {{ currentLogStore.logstore_name }}</span>
                <el-button type="info" link @click="showLogStoreDetail = false">收起</el-button>
              </div>
            </template>

            <el-descriptions :column="2" border>
              <!-- 基础信息 -->
              <el-descriptions-item label="LogStore名称">{{ currentLogStore.logstore_name }}</el-descriptions-item>
              <el-descriptions-item label="所属Project">{{ selectedProject.project_name }}</el-descriptions-item>
              <el-descriptions-item label="所属账号">{{ currentLogStore.account_name }}</el-descriptions-item>
              <el-descriptions-item label="类型">
                <el-tag :type="currentLogStore.mode === 'standard' ? '' : 'info'">
                  {{ currentLogStore.mode === 'standard' ? '标准型' : '查询型' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="日志类型">{{ currentLogStore.telemetry_type }}</el-descriptions-item>
              <el-descriptions-item label="产品类型">{{ currentLogStore.product_type || '-' }}</el-descriptions-item>

              <!-- 存储配置 -->
              <el-descriptions-item label="TTL">{{ currentLogStore.ttl }} 天</el-descriptions-item>
              <el-descriptions-item label="热存储层TTL" v-if="currentLogStore.hot_ttl">
                {{ currentLogStore.hot_ttl }} 天
              </el-descriptions-item>
              <el-descriptions-item label="低频存储TTL" v-if="currentLogStore.infrequent_access_ttl">
                {{ currentLogStore.infrequent_access_ttl }} 天
              </el-descriptions-item>
              <el-descriptions-item label="加密配置">
                <pre v-if="currentLogStore.encrypt_conf">{{ JSON.stringify(currentLogStore.encrypt_conf, null, 2) }}</pre>
                <span v-else>-</span>
              </el-descriptions-item>

              <!-- 分片配置 -->
              <el-descriptions-item label="分片数">{{ currentLogStore.shard_count }}</el-descriptions-item>
              <el-descriptions-item label="自动分裂Shard">
                <el-tag :type="currentLogStore.auto_split ? 'success' : 'info'">
                  {{ currentLogStore.auto_split ? '已启用' : '未启用' }}
                </el-tag>
                <span v-if="currentLogStore.auto_split"> (最大: {{ currentLogStore.max_split_shard }})</span>
              </el-descriptions-item>
              <el-descriptions-item label="分片策略">
                <pre v-if="currentLogStore.sharding_policy">{{ JSON.stringify(currentLogStore.sharding_policy, null, 2) }}</pre>
                <span v-else>-</span>
              </el-descriptions-item>

              <!-- 功能开关 -->
              <el-descriptions-item label="WebTracking">
                <el-tag :type="currentLogStore.enable_tracking ? 'success' : 'info'">
                  {{ currentLogStore.enable_tracking ? '已启用' : '未启用' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="记录外网IP">
                <el-tag :type="currentLogStore.append_meta ? 'success' : 'info'">
                  {{ currentLogStore.append_meta ? '已启用' : '未启用' }}
                </el-tag>
              </el-descriptions-item>

              <!-- 高级配置 -->
              <el-descriptions-item label="IngestProcessor ID" v-if="currentLogStore.processor_id">
                {{ currentLogStore.processor_id }}
              </el-descriptions-item>

              <!-- 时间信息 -->
              <el-descriptions-item label="创建时间">{{ formatTime(currentLogStore.create_time) }}</el-descriptions-item>
              <el-descriptions-item label="最后修改时间">{{ formatTime(currentLogStore.last_modify_time) }}</el-descriptions-item>
              <el-descriptions-item label="同步时间">{{ formatTime(currentLogStore.updated_at) }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </div>
      </el-collapse-transition>
    </el-card>
  </el-tab-pane>
</el-tabs>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, RefreshLeft, Back } from '@element-plus/icons-vue'
import { fetchSLSList, syncSLSapi } from '@/api/aliyun/sls' // 暂时移除 fetchSLSDetail

const listLoading = ref(false)
const detailLoading = ref(false)
const syncing = ref(false)
const tableData = ref([])
const selectedProject = ref(null) // 控制详情页显示
const activeTab = ref('basic')
const showLogStoreDetail = ref(false) // 控制 LogStore 详情面板显示
const currentLogStore = ref(null) // 当前选中的 LogStore

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

// 查看 LogStore 详情
const viewLogStoreDetail = (row) => {
  currentLogStore.value = row
  showLogStoreDetail.value = true
}

// 搜索和分页参数
const listQuery = ref({
  search: '', // 对应后端的 search_fields
})
const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0
})

// 加载列表数据
const loadData = async () => {
  listLoading.value = true
  try {
    const params = {
      ...listQuery.value,
      page: pagination.value.current,
      page_size: pagination.value.pageSize
    }
    const res = await fetchSLSList(params)
    if (res.code === 200) {
      const d = res.data || {}
      tableData.value = d.results || d.data || [] // 兼容不同后端响应格式
      pagination.value.total = d.count || d.total || 0
    } else {
      ElMessage.error(res.msg || '获取列表失败')
      tableData.value = []
      pagination.value.total = 0
    }
  } catch (err) {
    ElMessage.error('获取SLS列表失败')
    console.error(err)
    tableData.value = []
    pagination.value.total = 0
  } finally {
    listLoading.value = false
  }
}

const handleFilter = () => {
  pagination.value.current = 1
  loadData()
}
const handlePageChange = (val) => {
  pagination.value.current = val
  loadData()
}
const handleSizeChange = (val) => {
  pagination.value.pageSize = val
  loadData()
}

const syncSLS = async () => {
  syncing.value = true
  try {
    const res = await syncSLSapi()
    if (res.status === 'success' || res.status === 'partial') {
      ElMessage.success(`同步成功，共 ${res.projects} 个 Project，${res.logstores} 个 LogStore`)
      loadData() // 同步后刷新列表
    } else {
      ElMessage.error(res.message || 'SLS 同步失败')
    }
  } catch (err) {
    ElMessage.error('SLS 同步请求失败')
  } finally {
    syncing.value = false
  }
}

// 进入详情页
const gotoDetail = (row) => {
  selectedProject.value = row // 设置选中项目，触发 v-else 渲染详情页
  // 暂时直接使用行数据，后续可在此处调用独立的详情接口
}

const backToList = () => {
  selectedProject.value = null
  activeTab.value = 'basic'
}

const formatTime = (time) => {
  if (!time) return '-'
  try {
    return new Date(time).toLocaleString('zh-CN', { hour12: false })
  } catch {
    return time
  }
}

// 添加 Tab 点击处理方法
const handleTabClick = (tab) => {
  // 使用 nextTick 延迟表格渲染，避免尺寸计算冲突
  nextTick(() => {
    if (tab.paneName === 'logstores') {
      // 可以在这里添加表格重新布局的逻辑
      setTimeout(() => {
        // 如果有表格实例，可以调用 doLayout
        // logStoreTableRef.value?.doLayout?.();
      }, 100);
    }
  });
}


onMounted(() => {
  loadData()
})
</script>

<style scoped>
.sls-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 84px);
}

/* 列表页样式 */
.list-view {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 详情页样式 */
.detail-view {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e4e7ed;
}

.header-title {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.info-card {
  margin-top: 20px;
}

.card-header {
  font-weight: bold;
  color: #303133;
}
</style>
