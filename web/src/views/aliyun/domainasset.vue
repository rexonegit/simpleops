<template>
  <div class="dns-container">
    <!-- 搜索框 -->
    <el-input
      v-model="searchQuery"
      placeholder="请输入搜索关键词"
      clearable
      style="width: 300px; margin-right: 10px;"
      @keyup.enter="handleSearch"
      @input="onInputChange"
    />
    <el-button type="primary" :icon="Search" @click="handleSearch">
      搜索
    </el-button>
    <span style="margin-left: 10px; color: #888; font-size: 13px;">
      可搜索 完整域名、项目、负责人、记录值
    </span>

    <el-table
      v-loading="listLoading"
      :data="list"
      border
      stripe
      style="width: 100%; margin-top: 20px;"
    >
      <!-- 完整域名 -->
      <el-table-column label="完整域名" min-width="250" fixed="left">
        <template #default="{ row }">
          <span class="domain-text">{{ row.complete_domain }}</span>
          <el-tag
            v-if="row.rr === '@'"
            size="small"
            type="info"
            style="margin-left: 5px"
          >
            主域名
          </el-tag>
        </template>
      </el-table-column>

      <!-- 所属域名 -->
      <el-table-column label="所属域名" width="150" prop="domain_name" />

      <!-- 所属项目 -->
      <el-table-column label="项目" width="120" prop="project" />

      <!-- 环境类型 -->
      <el-table-column label="环境" width="100">
        <template #default="{ row }">
          <el-tag :type="envTagMap[row.environment]">
            {{ envDisplay(row.environment) }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 负责人 -->
      <el-table-column label="负责人" width="100" prop="owner" />

      <!-- 记录ID -->
      <el-table-column label="记录ID" width="120" prop="record_id" />

      <!-- 记录类型 -->
      <el-table-column label="类型" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="typeTagMap[row.type] || 'primary'">
            {{ row.type }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 主机记录 -->
      <el-table-column label="主机记录" width="100" prop="rr" />

      <!-- 记录值 -->
      <el-table-column label="记录值" min-width="180">
        <template #default="{ row }">
          <div class="record-value">
            {{ row.value }}
            <el-tag
              v-if="row.line !== 'default'"
              size="small"
              style="margin-left: 5px"
            >
              {{ row.line }}
            </el-tag>
          </div>
        </template>
      </el-table-column>

      <!-- TTL -->
      <el-table-column label="TTL" width="100" align="center">
        <template #default="{ row }">
          {{ row.ttl }}秒
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

      <!-- 状态 -->
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 'ENABLE' ? 'success' : 'danger'">
            {{ row.status === 'ENABLE' ? '已启用' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 创建时间 -->
      <el-table-column label="创建时间" width="160" align="center">
        <template #default="{ row }">
          {{ parseTime(row.create_timestamp) }}
        </template>
      </el-table-column>

      <!-- 更新时间 -->
      <el-table-column label="更新时间" width="160" align="center">
        <template #default="{ row }">
          {{ parseTime(row.update_timestamp) }}
        </template>
      </el-table-column>



      <!-- 备注 -->
      <el-table-column label="备注" min-width="150" prop="remark" />
    </el-table>

    <!-- 空状态 -->
    <el-empty v-if="!listLoading && list.length === 0" description="暂无数据" />

    <!-- 分页 -->
    <div class="pagination-container">
      <span class="pagination-total">共 {{ total }} 条记录</span>
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getDNSRecordList } from '@/api/aliyun/domainasset'

// ---------- 响应式数据 ----------
const list = ref([])
const listLoading = ref(true)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
let searchTimer = null // 防抖用

// ---------- 常量 ----------
const typeTagMap = {
  A: 'success',
  CNAME: 'warning',
  MX: 'danger',
  TXT: 'info',
  NS: 'primary'
}

const envTagMap = {
  prod: 'danger',
  test: 'warning',
  uat: 'success',
  stage: 'primary',
  dev: 'info'
}

// ---------- 工具函数 ----------
const parseTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).replace(/\//g, '-')
}

const envDisplay = (env) => {
  const map = {
    prod: '生产环境',
    test: '测试环境',
    uat: 'UAT环境',
    stage: 'Stage环境',
    dev: '开发环境'
  }
  return map[env] || '未分类'
}

// ---------- 请求数据 ----------
const fetchData = async () => {
  listLoading.value = true
  try {
    const res = await getDNSRecordList({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchQuery.value.trim() || undefined
    })

    const data = res.data || res

    // 根据你实际接口返回结构修改下面两行（常见两种写法已兼容）
    list.value = data.results || data.data || []
    total.value = data.count || data.total || 0

    // 可选：统一补全空字段，保持展示友好
    list.value = list.value.map(item => ({
      ...item,
      environment: item.environment || '未分类',
      project: item.project || '未分配',
      owner: item.owner || '系统管理员',
      remark: item.remark || '无备注'
    }))
  } catch (err) {
    console.error(err)
    ElMessage.error('加载 DNS 记录失败')
    list.value = []
    total.value = 0
  } finally {
    listLoading.value = false
  }
}

// ---------- 交互事件 ----------
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  fetchData()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchData()
}

const handleSearch = () => {
  currentPage.value = 1
  fetchData()
}

const onInputChange = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    handleSearch()
  }, 500)
}

// ---------- 生命周期 ----------
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.dns-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 84px);
}

.domain-text {
  font-weight: 500;
  color: #409eff;
}

.record-value {
  display: flex;
  align-items: center;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-top: 20px;
  padding: 10px 0;
  background: #fff;
  border-radius: 4px;
}

.pagination-total {
  line-height: 32px;
  margin-right: 20px;
  color: #606266;
  font-size: 14px;
}
</style>
