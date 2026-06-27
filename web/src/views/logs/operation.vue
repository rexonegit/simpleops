<template>
  <div class="app-container">
    <el-card shadow="never">
      <h3 style="margin: 0 0 20px 0">操作日志</h3>

      <el-table :data="list" v-loading="loading" style="width: 100%">
        <el-table-column prop="username" label="操作人" width="150" />
        <el-table-column prop="ip" label="IP" width="130" />
        <el-table-column label="方法" width="80">
          <template #default="{ row }">
            <el-tag :type="row.method === 'GET' ? 'info' : 'warning'">
              {{ row.method }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="请求路径" show-overflow-tooltip />
        <el-table-column prop="action" label="操作类型" width="120" />
        <el-table-column prop="status_code" label="状态码" width="100" />
        <el-table-column prop="duration" label="耗时(ms)" width="100" />
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>

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
import {getOperationLogList} from "@/api/logs";

const list = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const loading = ref(false)

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getOperationLogList({
      page: page.value,
      size: size.value,
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
.pagination-container {
  margin-top: 20px;
  text-align: center;
}
</style>
