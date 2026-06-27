<template>
  <div class="ip-manage-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">公网IP地址管理 (Internet)</span>
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
          <el-input v-model="form.ip_address" :disabled="isEdit" placeholder="例如: 8.8.8.8" />
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
import { ref, reactive, onMounted, computed } from 'vue'
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

// Detail
const detailVisible = ref(false)
const currentDetail = ref({})

const queryForm = reactive({
  page: 1,
  pageSize: 20,
  search: '',
  status: '',
  source: '',
  type: 'internet' 
})

const form = reactive({
  id: '',
  ip_address: '',
  type: 'internet',
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

const dialogTitle = computed(() => isEdit.value ? '编辑公网IP' : '新增公网IP')

const fetchData = async () => {
  listLoading.value = true
  try {
    const res = await getIPAddressList(queryForm)
    const payload = res.data || res
    // CustomPagination 返回格式: { code, msg, data: { page, total, pageSize, data: [...] } }
    if (payload.data) {
      tableData.value = payload.data
      total.value = payload.total || 0
    } else if (payload.results) {
      tableData.value = payload.results
      total.value = payload.count || 0
    } else {
      tableData.value = []
      total.value = 0
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
    form.type = 'internet'
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
    await ElMessageBox.confirm('Confirm delete?')
    await deleteIPAddress(row.id)
    fetchData()
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
    if(formRef.value) formRef.value.resetFields()
    Object.assign(form, { id: '', ip_address: '', type: 'internet', status: 'used', hostname: '', mac_address: '', owner: '', description: '' })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.ip-manage-container { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.title { font-weight: bold; }
.filter-container { margin-bottom: 20px; }
.pagination-container { margin-top: 20px; display: flex; justify-content: flex-end; }
</style>
