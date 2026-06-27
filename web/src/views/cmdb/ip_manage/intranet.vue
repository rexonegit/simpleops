<template>
  <div class="ip-manage-container">
    <!-- 网段统计卡片 -->
    <div class="segment-stat-row">
      <!-- 全部网段 -->
      <div class="segment-stat-card" :class="{ active: activeSegmentFilter === '' }" @click="filterBySegment('')">
        <span class="segment-label">全部网段</span>
        <span class="segment-count all">{{ total }}</span>
      </div>

      <!-- 分隔线 -->
      <div class="divider"></div>

      <!-- 动态网段卡片 -->
      <template v-for="(count, segment) in segmentStats" :key="segment">
        <div class="segment-stat-card" :class="{ active: activeSegmentFilter === segment }" @click="filterBySegment(segment)">

          <span class="segment-label">{{ segment }}</span>
          <span class="segment-count">{{ count }}</span>
        </div>
      </template>
    </div>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">内网IP地址管理 (Intranet)</span>
          <div class="header-actions">
            <el-button type="primary" :loading="syncLoading" @click="handleSync">
              <el-icon class="el-icon--left"><Refresh /></el-icon>同步IP数据
            </el-button>
            <el-button type="success" @click="handleAdd">
              <el-icon class="el-icon--left"><Plus /></el-icon>新增IP
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选区域 -->
      <div class="filter-container">
        <el-form :inline="true" :model="queryForm" class="demo-form-inline">
          <el-form-item label="搜索">
            <el-input v-model="queryForm.search" placeholder="IP/主机/负责人" clearable @keyup.enter="handleQuery" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="queryForm.status" placeholder="全部状态" clearable style="width: 120px" @change="handleQuery">
              <el-option label="使用中" value="used" />
              <el-option label="空闲" value="available" />
              <el-option label="保留" value="reserved" />
              <el-option label="废弃" value="deprecated" />
            </el-select>
          </el-form-item>
           <el-form-item label="来源">
            <el-select v-model="queryForm.source" placeholder="全部来源" clearable style="width: 120px" @change="handleQuery">
              <el-option label="手动" value="manual" />
              <el-option label="阿里云" value="aliyun" />
              <el-option label="机房" value="datacenter" />
            </el-select>
          </el-form-item>
          <!-- 当前网段过滤显示 -->
          <el-form-item v-if="activeSegmentFilter">
            <el-tag closable type="warning" @close="filterBySegment('')">
              网段: {{ activeSegmentFilter }}
            </el-tag>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleQuery">查询</el-button>
          </el-form-item>
        </el-form>
      </div>

      <ip-table :loading="listLoading" :data="tableData" @edit="handleEdit" @delete="handleDelete" @detail="handleDetail" />

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="queryForm.page"
          v-model:page-size="queryForm.pageSize"
          :page-sizes="[20, 50, 100, 200, 500, 800, 1000]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 编辑框 -->
    <el-dialog :title="dialogTitle" v-model="dialogVisible" width="600px" @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="IP地址" prop="ip_address">
          <el-input v-model="form.ip_address" :disabled="isEdit" placeholder="例如: 192.168.1.100" />
        </el-form-item>
         <el-form-item label="状态" prop="status">
            <el-select v-model="form.status">
            <el-option label="使用中" value="used" />
            <el-option label="空闲" value="available" />
            <el-option label="保留" value="reserved" />
            <el-option label="废弃" value="deprecated" />
            </el-select>
        </el-form-item>
        <el-form-item label="主机名" prop="hostname">
            <el-input v-model="form.hostname" />
        </el-form-item>
        <el-form-item label="负责人" prop="owner">
            <el-input v-model="form.owner" />
        </el-form-item>
        <el-form-item label="MAC" prop="mac_address">
            <el-input v-model="form.mac_address" />
        </el-form-item>
        <el-form-item label="备注" prop="description">
            <el-input v-model="form.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="submitForm">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <IPDetail v-model="detailVisible" :detail="currentDetail" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Plus } from '@element-plus/icons-vue'
import { getIPAddressList, syncIPAddress, createIPAddress, updateIPAddress, deleteIPAddress } from '@/api/cmdb/ip_manage'
import IpTable from './components/IpTable.vue'
import IPDetail from './components/IPDetail.vue'

const listLoading = ref(false)
const syncLoading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

// 🔥 网段统计相关
const segmentStats = ref({})  // 网段统计对象 { '10.164.9.0': 15, '10.164.10.0': 23 }
const activeSegmentFilter = ref('')  // 当前激活的网段过滤
const allData = ref([])  // 存储所有原始数据用于网段统计

// Detail
const detailVisible = ref(false)
const currentDetail = ref({})

const queryForm = reactive({
  page: 1,
  pageSize: 20,
  search: '',
  status: '',
  source: '',
  type: 'intranet'
})

const form = reactive({
  id: '',
  ip_address: '',
  type: 'intranet',
  status: 'used',
  hostname: '',
  mac_address: '',
  owner: '',
  description: ''
})

const rules = {
  ip_address: [{ required: true, message: '请输入IP地址', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑内网IP' : '新增内网IP')

// 🔥 提取网段函数 (如 10.164.9.100 -> 10.164.9.0)
const extractSegment = (ip) => {
  if (!ip) return ''
  const parts = ip.split('.')
  if (parts.length !== 4) return ''
  return `${parts[0]}.${parts[1]}.${parts[2]}.0`
}

// 🔥 网段排序函数 - 按 IP 数值逐段排序
const sortSegmentsByIP = (segments) => {
  return segments.sort((a, b) => {
    const aParts = a.split('.').map(Number)
    const bParts = b.split('.').map(Number)
    for (let i = 0; i < 4; i++) {
      if (aParts[i] !== bParts[i]) return aParts[i] - bParts[i]
    }
    return 0
  })
}

// 🔥 计算网段统计 - 按 IP 数值排序
const calculateSegmentStats = (data) => {
  const stats = {}
  data.forEach(item => {
    const segment = extractSegment(item.ip_address)
    if (segment) {
      stats[segment] = (stats[segment] || 0) + 1
    }
  })

  // 按网段 IP 数值排序
  const sortedKeys = sortSegmentsByIP(Object.keys(stats))
  const sortedStats = {}
  sortedKeys.forEach(key => {
    sortedStats[key] = stats[key]
  })
  return sortedStats
}

// 🔥 网段过滤点击事件
const filterBySegment = (segment) => {
  activeSegmentFilter.value = activeSegmentFilter.value === segment ? '' : segment
  queryForm.page = 1
  fetchData()
}

const fetchData = async () => {
  listLoading.value = true
  try {
    const res = await getIPAddressList(queryForm)
    const payload = res.data || res

    let data = []
    if (payload.data) {
      data = payload.data
    } else if (payload.results) {
      data = payload.results
    }

    // 保存所有原始数据用于网段统计 (只在第一页或没有网段过滤时更新统计)
    if (queryForm.page === 1 && !activeSegmentFilter.value && !queryForm.search && !queryForm.status && !queryForm.source) {
      allData.value = [...data]
      segmentStats.value = calculateSegmentStats(allData.value)
    }

    // 🔥 应用网段过滤 (前端过滤)
    if (activeSegmentFilter.value) {
      const segmentPrefix = activeSegmentFilter.value.replace('.0', '')
      data = data.filter(item => {
        const itemSegment = extractSegment(item.ip_address)
        return itemSegment === activeSegmentFilter.value
      })
    }

    // 🔥 按 IP 数值排序（关键代码）
    const sortByIP = (a, b) => {
      const aParts = a.ip_address.split('.').map(Number)
      const bParts = b.ip_address.split('.').map(Number)
      for (let i = 0; i < 4; i++) {
        if (aParts[i] !== bParts[i]) return aParts[i] - bParts[i]
      }
      return 0
    }

    tableData.value = data.sort(sortByIP)

    // 如果有过滤条件，total 显示过滤后的数量，否则显示后端返回的总数
    if (activeSegmentFilter.value) {
      total.value = data.length
    } else {
      total.value = payload.total || payload.count || 0
    }

  } catch (error) {
    console.error(error)
  } finally {
    listLoading.value = false
  }
}

const handleQuery = () => {
  queryForm.page = 1
  fetchData()
}

const handleSync = async () => {
  try {
     syncLoading.value = true
     await syncIPAddress()
     ElMessage.success('同步指令已通过')
     setTimeout(fetchData, 2000)
  } catch (err) {
      console.error(err)
  } finally {
      syncLoading.value = false
  }
}

const handleAdd = () => {
    isEdit.value = false; dialogVisible.value = true;
    form.type = 'intranet'
}

const handleEdit = (row) => {
    isEdit.value = true; dialogVisible.value = true;
    Object.assign(form, row)
}

const handleDetail = (row) => {
    currentDetail.value = row
    detailVisible.value = true
}

const handleDelete = async (row) => {
    try {
        await ElMessageBox.confirm('确定要删除吗？')
        await deleteIPAddress(row.id)
        fetchData()
    } catch(e) {}
}

const submitForm = async () => {
    await formRef.value.validate()
    if (isEdit.value) await updateIPAddress(form.id, form)
    else await createIPAddress(form)
    dialogVisible.value = false
    fetchData()
}

const handleSizeChange = (val) => { queryForm.pageSize = val; fetchData() }
const handleCurrentChange = (val) => { queryForm.page = val; fetchData() }

const resetForm = () => {
    if (formRef.value) formRef.value.resetFields()
    Object.assign(form, { id: '', ip_address: '', type: 'intranet', status: 'used', hostname: '', mac_address: '', owner: '', description: '' })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.ip-manage-container { padding: 20px; }

/* 🔥 网段统计卡片样式 - 简洁版 */
.segment-stat-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  flex-wrap: wrap;
}

.segment-stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 100px;
  padding: 12px 16px;
  background: #ffffff;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid #dcdfe6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.segment-stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

.segment-stat-card.active {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.segment-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
  font-weight: 500;
}

.segment-count {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.segment-stat-card.active .segment-count {
  color: #409eff;
}

.divider {
  width: 1px;
  height: 40px;
  background: #dcdfe6;
  margin: 0 4px;
}

.card-header { display: flex; justify-content: space-between; align-items: center; }
.title { font-weight: bold; }
.filter-container { margin-bottom: 20px; }
.pagination-container { margin-top: 20px; display: flex; justify-content: flex-end; }

@media (max-width: 768px) {
  .segment-stat-row {
    overflow-x: auto;
    flex-wrap: nowrap;
    padding: 12px;
  }
  .segment-stat-card { min-width: 90px; padding: 10px 12px; }
  .divider { height: 35px; }
}
</style>
