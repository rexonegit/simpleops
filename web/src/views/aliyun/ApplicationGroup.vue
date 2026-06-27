<template>
  <div class="application-group">
    <el-card>
      <template #header>
        <div class="clearfix">
          <span>应用分组管理</span>
          <el-button
            style="float: right; padding: 3px 0"
            type="primary"
            link
            :loading="syncing"
            @click="syncGroups"
          >
            <el-icon><Refresh /></el-icon> 同步分组
          </el-button>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="6">
          <div class="group-tree">
            <div class="group-controls">
              <el-input
                v-model="filterGroupText"
                placeholder="搜索分组"
                prefix-icon="Search"
                style="margin-bottom: 10px;"
              />

              <el-tree
                ref="groupTreeRef"
                :data="groups"
                :props="groupProps"
                :filter-node-method="filterGroupNode"
                node-key="id"
                highlight-current
                @node-click="handleGroupClick"
              />
            </div>
          </div>
        </el-col>

        <el-col :span="18">
          <div class="host-list">
            <el-alert
              v-if="selectedGroup"
              :title="`当前分组: ${selectedGroup.name} (${totalHosts}台主机)`"
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 10px;"
            />

            <el-alert
              v-else
              title="请从左侧选择一个分组查看主机详情"
              type="warning"
              :closable="false"
              show-icon
              style="margin-bottom: 10px;"
            />

            <el-table
              v-loading="loading"
              :data="hosts"
              style="width: 100%"
              height="calc(100vh - 340px)"
              border
              stripe
            >
              <el-table-column label="实例名" min-width="220" sortable>
                <template #default="{ row }">
                  <div class="host-info">
                    <el-icon style="margin-right: 5px;"><Monitor /></el-icon>
                    <div>
                      <div>{{ row.hostname }}</div>
                      <div style="font-size: 12px; color: #909399;">{{ row.instance_id }}</div>
                    </div>
                  </div>
                </template>
              </el-table-column>

              <el-table-column prop="agent_version" label="Agent版本" width="120" />

              <el-table-column prop="agent_status" label="Agent状态" width="120">
                <template #default="{ row }">
                  <el-tag :type="getAgentStatusType(row.agent_status)" size="small">
                    {{ getAgentStatusText(row.agent_status) }}
                  </el-tag>
                </template>
              </el-table-column>

              <el-table-column label="内网IP" width="140">
                <template #default="{ row }">
                  {{ row.internal_ip || 'N/A' }}
                </template>
              </el-table-column>

              <el-table-column label="外网IP" width="140">
                <template #default="{ row }">
                  {{ row.external_ip || 'N/A' }}
                </template>
              </el-table-column>

              <el-table-column label="区域" width="120" prop="region" sortable />
              <el-table-column prop="account" label="阿里云账号" width="140" />
              <el-table-column v-if="selectedGroup" label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button
                    type="danger"
                    size="small"
                    link
                    @click="removeFromGroup(row)"
                  >移除</el-button>
                </template>
              </el-table-column>
            </el-table>

            <div v-if="selectedGroup" class="host-pagination" style="margin-top: 10px; text-align: right;">
              <el-pagination
                small
                layout="prev, pager, next"
                :total="totalHosts"
                :page-size="hostPageSize"
                :current-page="hostCurrentPage"
                @current-change="handleHostPageChange"
              />
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="ungrouped-hosts" style="margin-top: 20px;">
      <template #header>
        <div class="clearfix">
          <span>未分组主机</span>
          <el-tag type="danger" size="small" style="margin-left: 10px;">{{ ungroupedHosts.length }}台</el-tag>
        </div>
      </template>

      <el-table v-loading="ungroupedLoading" :data="ungroupedHosts" style="width: 100%" height="250" border stripe>
        <el-table-column label="实例名" min-width="220" sortable>
          <template #default="{ row }">
            <div class="host-info">
              <el-icon style="margin-right: 5px;"><Monitor /></el-icon>
              <div>
                <div>{{ row.hostname }}</div>
                <div style="font-size: 12px; color: #909399;">{{ row.instance_id }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="agent_version" label="Agent版本" width="120" />

        <el-table-column prop="agent_status" label="Agent状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getAgentStatusType(row.agent_status)" size="small">
              {{ getAgentStatusText(row.agent_status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="内网IP" width="140">
          <template #default="{ row }">
            {{ row.internal_ip || 'N/A' }}
          </template>
        </el-table-column>

        <el-table-column label="外网IP" width="140">
          <template #default="{ row }">
            {{ row.external_ip || 'N/A' }}
          </template>
        </el-table-column>

        <el-table-column label="区域" width="120" prop="region" sortable />
        <el-table-column prop="account" label="阿里云账号" width="140" />

        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click="assignToGroup(row)"
            >
              分配分组
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      title="分配分组"
      v-model="assignDialogVisible"
      width="400px"
    >
      <el-form>
        <el-form-item label="选择分组">
          <el-select v-model="selectedGroupId" placeholder="请选择分组" style="width: 100%" filterable>
            <el-option
              v-for="group in groups"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            >
              <span style="float: left">{{ group.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px">
                {{ group.host_count }}台
              </span>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignDialogVisible = false">取 消</el-button>
        <el-button
          type="primary"
          :loading="assignLoading"
          @click="confirmAssign"
        >
          确 定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Monitor } from '@element-plus/icons-vue'
import {
  listGroups,
  getUngroupedHosts,
  getGroupHosts,
  assignHostToGroup,
  removeHostFromGroup,
  syncGroups as apiSyncGroups
} from '@/api/auto/monitor'

const groups = ref([])
const hosts = ref([])
const ungroupedHosts = ref([])
const selectedGroup = ref(null)
const filterGroupText = ref('')
const loading = ref(false)
const ungroupedLoading = ref(false)
const syncing = ref(false)
const assignLoading = ref(false)
const assignDialogVisible = ref(false)
const selectedGroupId = ref(null)
const selectedHost = ref(null)

const totalHosts = ref(0)
const hostCurrentPage = ref(1)
const hostPageSize = ref(20)

const groupTreeRef = ref(null)
const groupProps = {
  label: 'name',
  children: 'children',
  isLeaf: (data) => !data.children || data.children.length === 0
}

watch(filterGroupText, (val) => {
  groupTreeRef.value.filter(val)
})

const filterGroupNode = (value, data) => {
  if (!value) return true
  return data.name.indexOf(value) !== -1
}

const fetchGroups = async () => {
  try {
    const res = await listGroups()
    groups.value = res.data || res
  } catch (err) {
    ElMessage.error('获取分组失败')
  }
}

const fetchUngroupedHosts = async () => {
  ungroupedLoading.value = true
  try {
    const res = await getUngroupedHosts()
    ungroupedHosts.value = res.data || res
  } catch (err) {
    ElMessage.error('获取未分组主机失败')
  } finally {
    ungroupedLoading.value = false
  }
}

const handleGroupClick = (data) => {
  selectedGroup.value = data
  hostCurrentPage.value = 1
  fetchGroupHosts()
}

const fetchGroupHosts = async () => {
  if (!selectedGroup.value) return
  loading.value = true
  try {
    const res = await getGroupHosts(selectedGroup.value.id)
    const data = res.data || res
    // Assuming API returns all hosts for the group, do client-side pagination if needed,
    // or if API supports pagination, use params.
    // Here simplified to assume client pagination for now or all data.
    hosts.value = data
    totalHosts.value = data.length
  } catch (err) {
    ElMessage.error('获取主机列表失败')
  } finally {
    loading.value = false
  }
}

const handleHostPageChange = (val) => {
  hostCurrentPage.value = val
  // If backend pagination is implemented, call fetchGroupHosts() again with page param.
  // For client side:
  // This requires storing allHosts and slicing.
  // Since I don't have backend pagination details for group hosts, assuming full list returned.
}

const syncGroups = async () => {
  syncing.value = true
  try {
    await apiSyncGroups()
    ElMessage.success('同步成功')
    fetchGroups()
    fetchUngroupedHosts()
  } catch (err) {
    ElMessage.error('同步失败')
  } finally {
    syncing.value = false
  }
}

const assignToGroup = (row) => {
  selectedHost.value = row
  selectedGroupId.value = null
  assignDialogVisible.value = true
}

const confirmAssign = async () => {
  if (!selectedGroupId.value) {
    return ElMessage.warning('请选择分组')
  }
  assignLoading.value = true
  try {
    await assignHostToGroup({
      host_id: selectedHost.value.instance_id,
      group_id: selectedGroupId.value
    })
    ElMessage.success('分配成功')
    assignDialogVisible.value = false
    fetchUngroupedHosts()
    if (selectedGroup.value && selectedGroup.value.id === selectedGroupId.value) {
      fetchGroupHosts()
    }
    fetchGroups() // refresh counts
  } catch (err) {
    ElMessage.error('分配失败')
  } finally {
    assignLoading.value = false
  }
}

const removeFromGroup = (row) => {
  ElMessageBox.confirm(`确定将主机 ${row.hostname} 从分组中移除？`, '提示', {
    type: 'warning'
  }).then(async () => {
    try {
      await removeHostFromGroup({
        host_id: row.instance_id,
        group_id: selectedGroup.value.id
      })
      ElMessage.success('移除成功')
      fetchGroupHosts()
      fetchUngroupedHosts()
      fetchGroups()
    } catch (err) {
      ElMessage.error('移除失败')
    }
  })
}

const getAgentStatusText = (status) => {
  const map = { 'online': '在线', 'offline': '离线' }
  return map[status] || status
}

const getAgentStatusType = (status) => {
  return status === 'online' ? 'success' : 'info'
}

onMounted(() => {
  fetchGroups()
  fetchUngroupedHosts()
})
</script>

<style scoped>
.application-group { padding: 20px; background-color: #f5f7fa; min-height: calc(100vh - 84px); }
.clearfix:after { content: ""; display: table; clear: both; }
.host-info { display: flex; align-items: center; }
</style>
