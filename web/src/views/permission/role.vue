<template>
  <div class="role-management-container">
    <div class="query-container">
      <div class="left-panel">
        <el-button type="primary" icon="Plus" @click="handleAdd">添加角色</el-button>
      </div>
      <div class="right-panel">
        <el-button icon="Refresh" @click="fetchData" circle></el-button>
      </div>
    </div>

    <el-table v-loading="listLoading" :data="list" border>
      <el-table-column prop="id" label="ID" width="80" align="center" />
      <el-table-column prop="name" label="角色名称" align="center" />
      <el-table-column prop="code" label="角色标识" align="center" />
      <el-table-column prop="description" label="描述" align="center" />
      <el-table-column prop="created_at" label="创建时间" align="center" width="180" />
      <el-table-column label="操作" width="250" align="center" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="handleEdit(row)" :disabled="row.code === 'admin'">编辑</el-button>
          <el-button type="success" link @click="handlePermission(row)" :disabled="row.code === 'admin'">权限分配</el-button>
          <el-button type="danger" link @click="handleDelete(row)" :disabled="row.code === 'admin'">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog :title="title" v-model="dialogFormVisible" width="500px" @close="closeDialog">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="角色标识" prop="code">
          <el-input v-model="form.code" :disabled="isEdit" placeholder="如: admin, editor" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeDialog">取 消</el-button>
        <el-button type="primary" @click="saveData">确 定</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="permDrawerVisible" title="分配权限" size="400px">
      <div class="perm-tree-container">
        <el-tree
          ref="permTreeRef"
          :data="permissionData"
          show-checkbox
          node-key="id"
          default-expand-all
          :props="{ label: 'label', children: 'children' }"
        />
      </div>
      <template #footer>
        <el-button @click="permDrawerVisible = false">取消</el-button>
        <el-button type="primary" @click="savePermissions" :loading="permSaving">保存权限</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { getRoleList, createRole, updateRole, deleteRole, getRolePermissions, assignPermissions } from '@/api/role'
import { ElMessage, ElMessageBox } from 'element-plus'

defineOptions({ name: 'RoleManagement' })

const list = ref([])
const listLoading = ref(true)
const dialogFormVisible = ref(false)
const permDrawerVisible = ref(false)
const permSaving = ref(false)
const title = ref('')
const isEdit = ref(false)
const formRef = ref(null)
const permTreeRef = ref(null)

const permissionData = ref([])
const currentRoleId = ref(null)

const form = reactive({
  id: '',
  name: '',
  code: '',
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入角色标识', trigger: 'blur' }]
}

const fetchData = async () => {
  listLoading.value = true
  try {
    const { data } = await getRoleList()
    list.value = data.list
  } finally {
    listLoading.value = false
  }
}

const handleAdd = () => {
  title.value = '添加角色'
  isEdit.value = false
  Object.assign(form, { id: '', name: '', code: '', description: '' })
  dialogFormVisible.value = true
}

const handleEdit = (row) => {
  title.value = '编辑角色'
  isEdit.value = true
  Object.assign(form, row)
  dialogFormVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定删除该角色吗？', '提示', { type: 'warning' }).then(async () => {
    await deleteRole(row.id)
    ElMessage.success('删除成功')
    fetchData()
  })
}

const saveData = () => {
  formRef.value.validate(async (valid) => {
    if (valid) {
      if (isEdit.value) {
        await updateRole(form)
      } else {
        await createRole(form)
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

const handlePermission = async (row) => {
  currentRoleId.value = row.id
  const { data } = await getRolePermissions(row.id)

  const { menuTree, buttonPerms, checkedMenuIds, checkedPermIds } = data
  const tree = JSON.parse(JSON.stringify(menuTree))

  const addButtonsToTree = (nodes) => {
    nodes.forEach(node => {
      const buttons = buttonPerms.filter(btn => btn.parentId === node.id)
      if (buttons.length > 0) {
        if (!node.children) node.children = []
        node.children.push(...buttons)
      }
      if (node.children && node.children.length > 0) {
        addButtonsToTree(node.children)
      }
    })
  }

  addButtonsToTree(tree)
  permissionData.value = tree
  permDrawerVisible.value = true

  nextTick(() => {
    const allChecked = [...checkedMenuIds, ...checkedPermIds]
    permTreeRef.value.setCheckedKeys(allChecked, false)
  })
}

// 修改 savePermissions 函数
const savePermissions = async () => {
  permSaving.value = true

  // ✅ 只获取选中的叶子节点，排除父目录
  const checkedKeys = permTreeRef.value.getCheckedKeys(true)

  const menuIds = []
  const permIds = []

  checkedKeys.forEach(key => {
    if (typeof key === 'string' && key.startsWith('perm_')) {
      permIds.push(key)
    } else {
      menuIds.push(key)
    }
  })

  try {
    await assignPermissions({
      roleId: currentRoleId.value,
      menuIds: menuIds,
      permIds: permIds
    })
    ElMessage.success('权限分配成功')
    permDrawerVisible.value = false
  } catch (error) {
    ElMessage.error('权限分配失败')
  } finally {
    permSaving.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.role-management-container {
  padding: 20px;
  background: #fff;
}
.query-container {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}
</style>
