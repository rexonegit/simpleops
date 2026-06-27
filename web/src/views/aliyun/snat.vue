<template>
  <div class="app-container">
    <el-card shadow="always">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="搜索">
          <el-input
            v-model="queryParams.search"
            placeholder="支持搜索：主机名 / 源网段 / 公网IP"
            clearable
            style="width: 300px"
            @keyup.enter="handleQuery"
          />
        </el-form-item>
        <el-form-item label="地域">
          <el-select v-model="queryParams.region_id" clearable>
            <el-option v-for="r in regions" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button type="success" @click="handleSync">
            <el-icon><RefreshRight /></el-icon>同步
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="mt-10">
      <template #header>
        <div class="card-header">
          <span>SNAT 网关条目</span>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="hostname" label="主机名" width="160">
          <template #default="{ row }">
            {{ row.hostname || '未匹配' }}
          </template>
        </el-table-column>
        <el-table-column prop="source_cidr" label="源网段" width="160" />
        <el-table-column prop="snat_ip" label="公网IP" width="160" />
        <el-table-column prop="snat_entry_name" label="条目名称" />
        <el-table-column prop="nat_gateway_id" label="NAT网关ID"  />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'Available' ? 'success' : 'danger'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="region_id" label="地域" />
        <el-table-column prop="account_name" label="所属账号" width="120" />
      </el-table>

      <el-pagination
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.pageSize"
        :total="total"
        layout="->, total, sizes, prev, pager, next"
        @current-change="getList"
        @size-change="handleSizeChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listSNATEntries, syncSNATEntries } from '@/api/aliyun/snat'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const regions = ['cn-hangzhou', 'cn-shanghai', 'cn-beijing', 'cn-shenzhen']

const queryParams = ref({
  page: 1,
  pageSize: 20,
  search: '',
  region_id: ''
})

const getList = async () => {
  loading.value = true
  try {
    const params = { ...queryParams.value }
    if (!params.search) delete params.search
    const res = await listSNATEntries(params)
    if (res.code === 200) {
      tableData.value = res.data.data
      total.value = res.data.total
    }
  } catch (e) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const handleQuery = () => {
  queryParams.value.page = 1
  getList()
}

const handleSizeChange = (size) => {
  queryParams.value.pageSize = size
  getList()
}

const handleSync = async () => {
  loading.value = true
  try {
    await syncSNATEntries()
    ElMessage.success('同步成功')
    getList()
  } catch {
    ElMessage.error('同步失败')
  } finally {
    loading.value = false
  }
}

onMounted(getList)
</script>

<style scoped>
.text-grey { color: #999; font-style: italic; }
.mr-5 { margin-right: 5px; margin-bottom: 4px; }
</style>

