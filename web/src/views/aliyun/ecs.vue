<template>
  <div class="ecs-instance-list">
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <el-input v-model="searchQuery" placeholder="搜索主机名/项目/负责人/IP" clearable style="width: 300px;" @keyup.enter="handleSearch" />
        <el-button type="primary" icon="el-icon-search" @click="handleSearch">搜索</el-button>
      </div>

      <!-- 同步按钮 -->
      <el-button type="success" icon="el-icon-refresh" @click="syncEcsData" :loading="listLoading">
        同步阿里云ECS
      </el-button>
    </div>

    <span style="color: #888; font-size: 13px;">可搜索：主机名、项目、负责人、公网IP、私网IP</span>

    <!-- 表格部分保持你原来的完整表格代码不变 -->
    <el-table v-loading="listLoading" :data="displayedData" border style="margin-top: 20px;">
      <!-- 主机名 -->
      <el-table-column label="主机名" min-width="150" align="center" fixed="left">
        <template #default="{ row }">
          {{ row.hostname || '-' }}
        </template>
      </el-table-column>

      <!-- 项目信息 -->
      <el-table-column align="center" label="项目信息" min-width="120">
        <template #default="{ row }">
          {{ row.project || '-' }}
        </template>
      </el-table-column>

      <!-- 环境类型 -->
      <el-table-column prop="environment" label="环境类型" width="120">
        <template #default="{ row }">
          <el-tag :type="envTagType(row.environment)" size="small">
            {{ getEnvLabel(row.environment) }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 负责人 -->
      <el-table-column align="center" label="负责人" min-width="100">
        <template #default="{ row }">
          {{ row.owner || '未分配' }}
        </template>
      </el-table-column>

      <!-- 操作系统 -->
      <el-table-column label="操作系统" min-width="180" align="center">
        <template #default="{ row }">
          {{ row.osname || '-' }}
        </template>
      </el-table-column>

      <!-- 状态 -->
      <el-table-column class-name="status-col" label="状态" min-width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusFilter(row.status)" effect="dark">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- IP信息 -->
      <el-table-column
        prop="private_ip"
        label="私网IP"
        min-width="140"
        align="center"
        sortable
      >
        <template #default="{ row }">
          {{ row.private_ip || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="公网IP" min-width="140" align="center">
        <template #default="{ row }">
          {{ row.public_ip || '-' }}
        </template>
      </el-table-column>



      <!-- 配置信息 -->
      <el-table-column label="CPU" min-width="80" align="center">
        <template #default="{ row }">
          {{ row.cpu }}核
        </template>
      </el-table-column>

      <el-table-column label="内存" min-width="100" align="center">
        <template #default="{ row }">
          {{ (row.memory / 1024).toFixed(1) }}GB
        </template>
      </el-table-column>

      <!-- 实例信息 -->
      <el-table-column label="实例规格" min-width="150" align="center">
        <template #default="{ row }">
          {{ row.instance_type || '-' }}
        </template>
      </el-table-column>

      <el-table-column label="实例规格族" min-width="120" align="center">
        <template #default="{ row }">
          {{ row.instance_family || '-' }}
        </template>
      </el-table-column>

      <!-- 磁盘信息 -->
      <el-table-column label="系统盘" min-width="300" align="left">
        <template #default="{ row }">
          <div v-if="row.system_disk">
            {{ row.system_disk.category === 'cloud_essd' ? 'ESSD云盘' :
              row.system_disk.category === 'cloud_ssd' ? 'SSD云盘' :
              row.system_disk.category === 'cloud_efficiency' ? '高效云盘' : '普通云盘' }}
            {{ row.system_disk.performance_level || 'PL0' }}
            {{ row.system_disk.size }}
            ({{ row.system_disk.iops }} IOPS)
          </div>
          <span v-else>-</span>
        </template>
      </el-table-column>

      <el-table-column label="数据盘" min-width="300" align="left">
        <template #default="{ row }">
          <div v-if="row.data_disks && row.data_disks.length">
            <div v-for="(disk, index) in row.data_disks" :key="index">
              {{ disk.device }}：
              {{ disk.category === 'cloud_essd' ? 'ESSD云盘' :
                disk.category === 'cloud_ssd' ? 'SSD云盘' :
                disk.category === 'cloud_efficiency' ? '高效云盘' : '普通云盘' }}
              {{ disk.performance_level || 'PL0' }}
              {{ disk.size }}
              ({{ disk.iops }} IOPS)
            </div>
          </div>
          <span v-else>-</span>
        </template>
      </el-table-column>

      <!-- 其他信息 -->
      <el-table-column label="停机模式" min-width="120" align="center">
        <template #default="{ row }">
          <span v-if="row.stopped_mode === 'KeepCharging'" style="color: red;">
            普通停机模式
          </span>
          <span v-else-if="row.stopped_mode === 'StopCharging'" style="color: green;">
            节省停机模式
          </span>
          <span v-else-if="row.stopped_mode === 'Not-applicable'" style="color: lightgray;">
            /
          </span>
          <span v-else>{{ row.stopped_mode || '-' }}</span>
        </template>
      </el-table-column>

      <el-table-column label="GPU类型" min-width="120" align="center">
        <template #default="{ row }">
          {{ row.gpu_type || '-' }}
        </template>
      </el-table-column>

      <el-table-column label="GPU数量" min-width="100" align="center">
        <template #default="{ row }">
          {{ row.gpu_count || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="带宽" min-width="100" align="center">
        <template #default="{ row }">
          {{ row.bandwidth ? `${row.bandwidth}Mbps` : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="弹性IP" min-width="140" align="center">
        <template #default="{ row }">
          {{ row.eip || '-' }}
        </template>
      </el-table-column>
      <!-- 所在可用区 -->
      <el-table-column align="center" label="所在可用区" min-width="120">
        <template #default="{ row }">
          {{ row.zone || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="所属账号" min-width="120" align="center">
      <template #default="{ row }">
        <el-tag type="primary" size="small">
          {{ row.account_name || '未知账号' }}
        </el-tag>
      </template>
    </el-table-column>

    <!-- 创建时间 -->
    <el-table-column align="center" label="创建时间" width="180">
      <template #default="{ row }">
        <i class="el-icon-time" />
        <span>{{ parseTime(row.creation_time) }}</span>
      </template>
    </el-table-column>

    <!-- 到期时间 -->
    <el-table-column align="center" label="到期时间" width="180">
      <template #default="{ row }">
        <i class="el-icon-time" />
        <span>{{ parseTime(row.expire_time) }}</span>
      </template>
    </el-table-column>

    <el-table-column label="镜像ID" min-width="180" align="center">
        <template #default="{ row }">
          <el-tooltip effect="dark" :content="row.image_id" placement="top">
            <span>{{ row.image_id  }}</span>
          </el-tooltip>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="queryParams.page"
      v-model:page-size="queryParams.pageSize"
      :page-sizes="[10,20,30,50,100,200]"
      layout="->, total, sizes, prev, pager, next, jumper"
      :total="total"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
  </div>
</template>


<script setup>
import { reactive, ref, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ecslist, syncecs } from '@/api/aliyun/ecs'

const searchQuery = ref('')

// ==================== 工具函数 ====================
const truncate = (str, len = 30) => !str ? '-' : str.length > len ? str.substring(0, len) + '...' : str

const statusFilter = (status) => {
  const map = { Running: 'success', Stopped: 'danger', Starting: 'warning', Stopping: 'warning' }
  return map[status] || 'info'
}

const parseTime = (time) => {
  if (!time) return '-'
  try {
    return new Date(time).toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    }).replace(/\//g, '-')
  } catch (e) {
    return '-'
  }
}

const formatDisk = (disk) => {
  if (!disk) return '-'
  const typeMap = { 'cloud_essd': 'ESSD云盘', 'cloud_ssd': 'SSD云盘', 'cloud_efficiency': '高效云盘' }
  return `${typeMap[disk.category] || disk.category} ${disk.performance_level || 'PL0'} ${disk.size} (${disk.iops} IOPS)`
}

const getEnvLabel = (val) => {
  const map = { prod: '生产环境', test: '测试环境', dev: '开发环境', uat: '用户验收环境', stg: '预生产环境', dr: '灾备环境', other: '其他' }
  return map[val] || val
}

const envTagType = (code) => {
  const map = { prod: 'danger', stg: 'warning', dr: 'warning', uat: 'primary', test: 'primary', dev: 'success', other: 'info' }
  return map[code] || 'info'
}

// ==================== 状态 ====================
const listLoading = ref(true)
const displayedData = ref([])
const total = ref(0)

// 统一参数（推荐方案）
const queryParams = reactive({
  page: 1,
  pageSize: 10,
  search: ''
})

// ==================== 必须先定义 fetchData！====================
const fetchData = async () => {
  listLoading.value = true
  try {
    const res = await ecslist({
      page: queryParams.page,
      pageSize: queryParams.pageSize,
      search: queryParams.search || undefined
    })

    const p = res.data
    displayedData.value = p.data || []
    total.value = p.total || 0

  } catch (err) {
    console.error('加载失败:', err)
    ElMessage.error('加载失败')
    displayedData.value = []
    total.value = 0
  } finally {
    listLoading.value = false
  }
}

const handleSizeChange = (val) => {
  queryParams.pageSize = val
  queryParams.page = 1
  fetchData()
}

const handleCurrentChange = (val) => {
  queryParams.page = val
  fetchData()
}

// ==================== 现在才能安全使用 fetchData ====================
// 监听参数变化自动刷新
watch(queryParams, () => {
  fetchData()
}, { deep: true })

// 搜索
const handleSearch = () => {
  queryParams.page = 1
  queryParams.search = searchQuery.value?.trim() || ''
  // watch 会自动触发 fetchData
}

// 同步
const syncEcsData = async () => {
  try {
    await ElMessageBox.confirm('确定要立即同步所有阿里云ECS信息吗？', '同步确认', { type: 'warning' })
    ElMessage.info('正在同步，请稍候...')
    await syncecs()
    ElMessage.success('同步任务已启动，3秒后自动刷新')
    setTimeout(fetchData, 3000)
  } catch (err) {
    ElMessage.error('同步失败')
  }
}

// 初始化
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.ecs-instance-list {
  padding: 20px;
}

.spec-info {
  display: flex;
  justify-content: center;
  gap: 10px;
}
.cpu, .memory {
  padding: 2px 6px;
  background-color: #f5f7fa;
  border-radius: 4px;
}
</style>
