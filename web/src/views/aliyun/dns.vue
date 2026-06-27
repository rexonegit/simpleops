<template>
  <div class="dns-container">
    <div class="header">
      <h2>阿里云 DNS 解析记录</h2>
      <div class="actions">
        <el-button type="success" :loading="syncLoading" @click="handleSync">
          <el-icon><Refresh /></el-icon>
          {{ syncLoading ? '同步中...' : '同步域名和DNS记录' }}
        </el-button>
      </div>
    </div>

    <div class="filter-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索完整域名 / 项目 / 负责人 / 记录值"
        clearable
        style="width: 400px; margin-right: 12px;"
        @keyup.enter="refreshList"
      />
      <el-button type="primary" :icon="Search" @click="refreshList">搜索</el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="list"
      border
      stripe
      style="width: 100%; margin-top: 20px;"
    >
      <!-- 完整域名 -->
      <el-table-column label="完整域名" min-width="280" fixed="left">
        <template #default="{ row }">
          <span class="domain-link">{{ row.complete_domain }}</span>
          <el-tag v-if="row.rr === '@'" size="small" type="info" style="margin-left: 6px;">主域名</el-tag>
        </template>
      </el-table-column>

      <!-- 所属域名 -->
      <el-table-column label="所属域名" width="150" prop="domain_name" />

      <!-- 所属项目 -->
      <el-table-column label="项目" width="140" prop="project">
        <template #default="{ row }">
          <el-tag v-if="row.project" size="small">{{ row.project }}</el-tag>
          <span v-else style="color: #999;">未分配</span>
        </template>
      </el-table-column>

      <!-- 环境类型 -->
      <el-table-column label="环境" width="100">
        <template #default="{ row }">
          <el-tag :type="envTagType(row.environment)">
            {{ envLabel(row.environment) }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 负责人 -->
      <el-table-column label="负责人" width="100" prop="owner" />

      <!-- 记录ID -->
      <el-table-column label="记录ID" width="120" prop="record_id" />

      <!-- 记录类型 -->
      <el-table-column label="类型" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="typeTagMap[row.type] || 'info'">{{ row.type }}</el-tag>
        </template>
      </el-table-column>

      <!-- 主机记录 -->
      <el-table-column label="主机记录" width="120" prop="rr" />

      <!-- 记录值 -->
      <el-table-column label="记录值" min-width="220">
        <template #default="{ row }">
          <div style="word-break: break-all; font-family: Consolas, monospace;">
            {{ row.value }}
          </div>
          <el-tag v-if="row.line !== 'default'" size="small" type="warning" style="margin-top: 4px;">
            {{ row.line }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- TTL -->
      <el-table-column label="TTL" width="90" align="center">
        <template #default="{ row }">
          {{ row.ttl }}秒
        </template>
      </el-table-column>

      <!-- 状态 -->
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 'ENABLE' ? 'success' : 'danger'">
            {{ row.status === 'ENABLE' ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 锁定状态 -->
      <el-table-column label="锁定" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.locked ? 'danger' : 'success'">
            {{ row.locked ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 权重 -->
      <el-table-column label="权重" width="80" align="center" prop="weight" />

      <!-- 创建时间 -->
      <el-table-column label="创建时间" width="160" align="center">
        <template #default="{ row }">
          {{ formatDate(row.create_timestamp) }}
        </template>
      </el-table-column>

      <!-- 更新时间 -->
      <el-table-column label="更新时间" width="170" align="center">
        <template #default="{ row }">
          {{ formatDate(row.update_timestamp) }}
        </template>
      </el-table-column>

      <!-- 所属账号 -->
      <el-table-column label="所属账号" width="120" align="center" prop="account_name" />

      <!-- 备注 -->
      <el-table-column label="备注" min-width="150" prop="remark" />

      <!-- 空数据提示 -->
      <template #empty>
        <div v-if="loading" class="empty-tip">加载中...</div>
        <div v-else class="empty-tip">
          <el-empty description="暂无数据" />
        </div>
      </template>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :page-sizes="[10,20,30,50,100]"
      layout="total, sizes, prev, pager, next, jumper"
      :total="total"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
      style="margin-top: 20px; justify-content: flex-end;"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getDNSRecordList, syncDNSRecords } from '@/api/aliyun/dns'

const list = ref([])
const loading = ref(false)
const syncLoading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const handleSizeChange = (val) => {
  page.value = 1
  fetchList()
}


const handleCurrentChange = (val) => {
  fetchList()
}

const searchQuery = ref('')

const typeTagMap = {
  A: 'success',
  CNAME: 'warning',
  MX: 'danger',
  TXT: 'info',
  NS: 'primary',
  AAAA: 'purple'
}

const envTagType = (env) => {
  const map = { prod: 'danger', uat: 'success', test: 'warning', dev: 'info', stage: 'primary' }
  return map[env] || 'info'
}
const envLabel = (env) => {
  const map = { prod: '生产', uat: 'UAT', test: '测试', dev: '开发', stage: '预发布' }
  return map[env] || env || '未分类'
}

const formatDate = (timeStr) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-')
}

const fetchList = async () => {
  loading.value = true
  try {
    const res = await getDNSRecordList({
      page: page.value,
      page_size: pageSize.value,
      search: searchQuery.value || undefined
    })
    list.value = res.data.results || res.data.data || []
    total.value = res.data.count || res.data.total || 0
  } catch (err) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const handleSync = async () => {
  syncLoading.value = true
  try {
    await syncDNSRecords()
    ElMessage.success('同步成功！')
    fetchList()
  } catch (err) {
    ElMessage.error('同步失败：' + (err.response?.data?.message || err.message))
  } finally {
    syncLoading.value = false
  }
}

const refreshList = () => {
  page.value = 1
  fetchList()
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.dns-container {
  padding: 20px;
  background: #fff;
  min-height: calc(100vh - 84px);
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}
.filter-bar {
  margin-bottom: 20px;
}
.domain-link {
  color: #409eff;
  font-weight: 500;
  font-family: Consolas, monospace;
}
.pagination {
  margin-top: 20px;
  text-align: right;
}
</style>
