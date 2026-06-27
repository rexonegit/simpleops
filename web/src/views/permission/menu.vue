<template>
  <div class="menu-management-container">
    <div class="query-container">
      <div class="left-panel">
        <el-button type="primary" icon="Plus" @click="handleAdd()">添加根菜单</el-button>
        <el-button type="info" icon="Sort" @click="toggleExpand">展开/折叠</el-button>
      </div>
      <div class="right-panel">
        <el-button icon="Refresh" @click="fetchData" circle></el-button>
      </div>
    </div>

    <el-table
      ref="tableRef"
      v-loading="listLoading"
      :data="list"
      row-key="id"
      border
      :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
    >
      <el-table-column prop="label" label="标题" min-width="150" />
      <el-table-column prop="icon" label="图标" align="center" width="60">
        <template #default="{ row }">
          <vab-icon v-if="row.icon" :icon="row.icon" />
        </template>
      </el-table-column>
      <el-table-column prop="type" label="类型" align="center" width="80">
        <template #default="{ row }">
          <el-tag v-if="row.type === 0" type="primary">目录</el-tag>
          <el-tag v-else-if="row.type === 1" type="success">菜单</el-tag>
          <el-tag v-else type="warning">按钮</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="路由Name" align="center" min-width="120" />
      <el-table-column prop="path" label="路由路径" align="center" min-width="150" />
      <el-table-column prop="component" label="组件路径" align="center" min-width="180" />
      <el-table-column prop="sort" label="排序" align="center" width="60" />
      <el-table-column prop="hidden" label="隐藏" align="center" width="60">
        <template #default="{ row }">
          <el-tag :type="row.hidden ? 'danger' : 'info'">{{ row.hidden ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" align="center" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
          <el-button type="primary" link @click="handleAdd(row)" v-if="row.type !== 2">新增子项</el-button>
          <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 编辑/新增对话框 -->
    <el-dialog :title="title" v-model="dialogFormVisible" width="700px" @close="closeDialog">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="上级菜单">
          <el-tree-select
            v-model="form.parent"
            :data="menuTreeSelect"
            :render-after-expand="false"
            check-strictly
            clearable
            placeholder="请选择（空则为根节点）"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-radio-group v-model="form.type">
            <el-radio :label="0">目录</el-radio>
            <el-radio :label="1">菜单</el-radio>
            <el-radio :label="2">按钮</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="菜单名称或按钮描述" />
        </el-form-item>

        <template v-if="form.type !== 2">
          <!-- 图标选择（只在非按钮时显示） -->
        <el-form-item label="图标" prop="icon" v-if="form.type !== 2">
          <el-input
            v-model="form.icon"
            placeholder="点击选择图标"
            readonly
            clearable
            @click="iconDialogVisible = true"
          >
            <template #prefix>
              <el-icon v-if="form.icon" :size="20">
                <component :is="form.icon" />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>
          <el-form-item label="路由Name" prop="name">
            <el-input v-model="form.name" placeholder="唯一英文标识" />
          </el-form-item>
          <el-form-item label="路由Path" prop="path">
            <el-input v-model="form.path" placeholder=" 目录/开头 例如 /aliyun 菜单直接写英文例如 oss" />
          </el-form-item>
          <el-form-item label="组件路径" prop="component" v-if="form.type === 1">
             <el-input v-model="form.component" placeholder="样例：src/views/aliyun/oss.vue 输入 aliyun/oss" />
          </el-form-item>
          <el-form-item label="排序" prop="sort">
            <el-input-number v-model="form.sort" :min="0" :max="999" />
          </el-form-item>
          <el-row>
             <el-col :span="12">
                <el-form-item label="隐藏" prop="hidden">
                  <el-switch v-model="form.hidden" />
                </el-form-item>
             </el-col>
             <el-col :span="12" v-if="form.type === 0">
               <el-form-item label="始终显示" prop="alwaysShow">
                  <el-switch v-model="form.alwaysShow" />
               </el-form-item>
             </el-col>
          </el-row>
        </template>

        <template v-else>
           <el-form-item label="权限标识" prop="permissionCode">
             <el-input v-model="form.permissionCode" placeholder="例如: user:add" />
           </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="closeDialog">取 消</el-button>
        <el-button type="primary" @click="saveData">确 定</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 图标选择弹窗 ==================== -->
    <el-dialog
      v-model="iconDialogVisible"
      title="选择图标"
      width="860px"
      append-to-body
      destroy-on-close
    >
      <el-input
        v-model="iconSearch"
        placeholder="搜索图标名称（如 Menu、Home）"
        clearable
        style="margin-bottom: 16px"
      />
      <div class="icon-grid">
        <div
          v-for="icon in filteredIcons"
          :key="icon"
          class="icon-item"
          :class="{ active: form.icon === icon }"
          @click="form.icon = icon; iconDialogVisible = false"
        >
          <el-icon :size="28">
            <component :is="icon" />
          </el-icon>
          <span class="icon-name">{{ icon }}</span>
        </div>
      </div>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { getMenuTree, createMenu, updateMenu, deleteMenu } from '@/api/menu'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

defineOptions({ name: 'MenuManagement' })

/* ==================== 图标选择相关 ==================== */
const iconDialogVisible = ref(false)
const iconSearch = ref('')

// 所有 Element Plus 图标名称数组
const allIconNames = computed(() => {
  return Object.keys(ElementPlusIconsVue)
})

// 搜索过滤后的图标
const filteredIcons = computed(() => {
  if (!iconSearch.value) return allIconNames.value
  const keyword = iconSearch.value.toLowerCase()
  return allIconNames.value.filter(name =>
    name.toLowerCase().includes(keyword)
  )
})

const list = ref([])
const listLoading = ref(true)
const dialogFormVisible = ref(false)
const title = ref('')
const isEdit = ref(false)
const tableRef = ref(null)
const isExpand = ref(false)
const formRef = ref(null)
const menuTreeSelect = ref([])

const form = reactive({
  id: '',
  parent: null,
  type: 1,
  title: '',
  name: '',
  path: '',
  component: '',
  icon: '',
  sort: 0,
  hidden: false,
  alwaysShow: false,
  permissionCode: ''
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  name: [{ required: true, message: '请输入路由Name', trigger: 'blur' }],
  path: [{ required: true, message: '请输入路由Path', trigger: 'blur' }]
}

const fetchData = async () => {
  listLoading.value = true
  try {
    const { data } = await getMenuTree()
    list.value = data
    menuTreeSelect.value = filterMenuForSelect(JSON.parse(JSON.stringify(data)))
  } finally {
    listLoading.value = false
  }
}

const filterMenuForSelect = (tree) => {
  return tree.filter(node => {
    if (node.type === 2) return false
    node.value = node.id
    if (node.children && node.children.length) {
      node.children = filterMenuForSelect(node.children)
    }
    return true
  })
}

const handleAdd = (row) => {
  title.value = row ? '添加子菜单' : '添加根菜单'
  isEdit.value = false
  Object.assign(form, {
    id: '',
    parent: row ? row.id : null,
    type: 1,
    title: '',
    name: '',
    path: '',
    component: '',
    icon: '',
    sort: 0,
    hidden: false,
    alwaysShow: false,
    permissionCode: ''
  })
  dialogFormVisible.value = true
}

const handleEdit = (row) => {
  title.value = '编辑菜单'
  isEdit.value = true
  Object.assign(form, {
    id: row.id,
    parent: row.parent,
    type: row.type,
    title: row.label,
    name: row.name,
    path: row.path,
    component: row.component,
    icon: row.icon || '',
    sort: row.sort,
    hidden: row.hidden,
    alwaysShow: row.always_show,
    permissionCode: row.type === 2 ? row.name : ''
  })
  dialogFormVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定删除该菜单/按钮吗？', '提示', { type: 'warning' }).then(async () => {
    await deleteMenu(row.id)
    ElMessage.success('删除成功')
    fetchData()
  })
}

const saveData = () => {
  formRef.value.validate(async (valid) => {
    if (valid) {
      const data = {
        ...form,
        alwaysShow: form.alwaysShow
      }
      if (form.type === 2) {
        data.name = form.permissionCode
      }

      if (isEdit.value) {
        await updateMenu(data)
      } else {
        await createMenu(data)
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

const toggleExpand = () => {
  isExpand.value = !isExpand.value
  toggleRowExpansion(list.value, isExpand.value)
}

const toggleRowExpansion = (data, expanded) => {
  data.forEach((item) => {
    tableRef.value.toggleRowExpansion(item, expanded)
    if (item.children) {
      toggleRowExpansion(item.children, expanded)
    }
  })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.menu-management-container {
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

/* 图标弹窗网格 */
.icon-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
  max-height: 480px;
  overflow-y: auto;
  padding: 8px;
}
.icon-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 4px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}
.icon-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
}
.icon-item.active {
  border-color: #409eff;
  background: #409eff;
  color: #fff;
}
.icon-name {
  margin-top: 6px;
  font-size: 12px;
  word-break: break-all;
}

</style>
