<template>
  <div class="app-container">
    <el-card shadow="never">
      <div class="filter-container">
        <h3 style="margin: 0 0 20px 0">登录日志</h3>
        <el-input
          v-model="queryForm.username"
          placeholder="搜索用户名"
          style="width: 200px"
          clearable
        />
        <el-button type="primary" @click="fetchData" style="margin-left: 10px">
          查询
        </el-button>
      </div>

      <el-table :data="list" v-loading="loading" style="width: 100%">
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="ip" label="IP地址" width="150" />
        <el-table-column prop="user_agent" label="浏览器" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '成功' ? 'success' : 'danger'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="登录时间" width="180" />
      </el-table>

      <!-- 原生分页组件 -->
      <div class="pagination-container">
        <el-pagination
          background
          :current-page="page"
          :page-size="size"
          :page-sizes="[10, 20, 50, 100]"
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
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getLoginLogList } from '@/api/logs'

const list = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const loading = ref(false)
const queryForm = ref({ username: '' })

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getLoginLogList({
      page: page.value,
      size: size.value,
      username: queryForm.value.username
    })
    list.value = res.data.list || []
    total.value = res.data.total || 0
  } catch (error) {
    ElMessage.error('获取登录日志失败')
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (val) => {
  size.value = val
  fetchData()
}

const handleCurrentChange = (val) => {
  page.value = val
  fetchData()
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.app-container {
  padding: 20px;
}
.filter-container {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.pagination-container {
  margin-top: 20px;
  text-align: center;
}
</style>
