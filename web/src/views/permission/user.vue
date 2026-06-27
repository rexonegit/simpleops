<template>
  <div class="user-management-container">
    <div class="query-container">
      <div class="left-panel">
        <el-button type="primary" icon="Plus" @click="handleAdd">添加用户</el-button>
        <el-button type="danger" icon="Delete" @click="handleBulkDelete" :disabled="selectRows.length === 0">
          批量删除
        </el-button>
      </div>
      <div class="right-panel">
        <el-form :inline="true" :model="queryForm" @submit.prevent>
          <el-form-item>
            <el-input v-model="queryForm.username" placeholder="请输入用户名" clearable />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" icon="Search" @click="fetchData">查询</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
    <el-table
      v-loading="listLoading"
      :data="list"
      border
      @selection-change="setSelectRows"
    >
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column prop="id" label="ID" width="80" align="center" />
      <el-table-column prop="username" label="用户名" align="center" />
      <el-table-column prop="phone" label="手机号" align="center" />
      <el-table-column label="角色" align="center">
        <template #default="{ row }">
          <el-tag v-for="(role, index) in row.roles" :key="index" style="margin-right: 5px">
            {{ role }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="date_joined" label="创建时间" align="center" width="180" />
      <el-table-column label="操作" width="200" align="center" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
          <el-button type="warning" link @click="handleResetPwd(row)">重置密码</el-button>
          <el-button type="danger" link @click="handleDelete(row)" :disabled="row.is_superuser">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="queryForm.page"
      v-model:page-size="queryForm.size"
      :total="total"
      layout="total, prev, pager, next, sizes"
      @size-change="fetchData"
      @current-change="fetchData"
      class="pagination-container"
    />

    <el-dialog
      :title="title"
      v-model="dialogFormVisible"
      width="500px"
      @close="closeDialog"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="角色" prop="roles">
          <el-select v-model="form.roles" multiple placeholder="请选择角色" style="width: 100%">
            <el-option
              v-for="item in roleOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeDialog">取 消</el-button>
        <el-button type="primary" @click="saveData">确 定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getUserList, createUser, updateUser, deleteUser, resetPassword, getRoleSelect } from '@/api/userManage'
import { ElMessage, ElMessageBox } from 'element-plus'

defineOptions({ name: 'UserManagement' })

const list = ref([])
const listLoading = ref(true)
const total = ref(0)
const selectRows = ref([])
const roleOptions = ref([])
const dialogFormVisible = ref(false)
const title = ref('')
const isEdit = ref(false)
const formRef = ref(null)

const queryForm = reactive({
  page: 1,
  size: 20,
  username: '',
})

const form = reactive({
  id: '',
  username: '',
  password: '',
  phone: '',
  roles: [],
  is_active: true,
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '至少6位', trigger: 'blur' }],
  roles: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

const fetchData = async () => {
  listLoading.value = true
  try {
    const { data } = await getUserList(queryForm)
    list.value = data.list
    total.value = data.total
  } finally {
    listLoading.value = false
  }
}

const fetchRoles = async () => {
  const { data } = await getRoleSelect()
  roleOptions.value = data
}

const handleAdd = () => {
  title.value = '添加用户'
  isEdit.value = false
  Object.assign(form, { id: '', username: '', password: '', phone: '', roles: [], is_active: true })
  dialogFormVisible.value = true
}

const handleEdit = (row) => {
  title.value = '编辑用户'
  isEdit.value = true
  const roleIds = []
  row.roles.forEach(roleName => {
    const found = roleOptions.value.find(opt => opt.label === roleName)
    if (found) roleIds.push(found.value)
  })

  Object.assign(form, {
    id: row.id,
    username: row.username,
    phone: row.phone,
    roles: roleIds,
    is_active: row.is_active
  })
  dialogFormVisible.value = true
}

const handleResetPwd = async (row) => {
  ElMessageBox.confirm('确定要重置该用户的密码为 123456 吗？', '提示', { type: 'warning' }).then(async () => {
    await resetPassword({ id: row.id })
    ElMessage.success('重置成功')
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该用户吗？', '提示', { type: 'warning' }).then(async () => {
    await deleteUser({ ids: [row.id] })
    ElMessage.success('删除成功')
    fetchData()
  })
}

const handleBulkDelete = () => {
  if (!selectRows.value.length) return
  const ids = selectRows.value.map(item => item.id)
  ElMessageBox.confirm(`确定删除选中的 ${ids.length} 个用户吗？`, '提示', { type: 'warning' }).then(async () => {
    await deleteUser({ ids })
    ElMessage.success('删除成功')
    fetchData()
  })
}

const saveData = () => {
  formRef.value.validate(async (valid) => {
    if (valid) {
      if (isEdit.value) {
        await updateUser(form)
      } else {
        await createUser(form)
      }
      ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
      dialogFormVisible.value = false
      fetchData()
    }
  })
}

const closeDialog = () => {
  dialogFormVisible.value = false
  formRef.value?.resetFields()
}

const setSelectRows = (val) => {
  selectRows.value = val
}

onMounted(() => {
  fetchRoles()
  fetchData()
})
</script>

<style scoped>
/* 新增样式：替代 vab-query-form 的布局 */
.user-management-container {
  padding: 20px;
  background: #fff;
}
.query-container {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}
.left-panel {
  display: flex;
  gap: 10px;
}
.pagination-container {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
