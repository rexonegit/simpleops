<!-- src/views/aliyun/securitygroup.vue -->
<template>
  <div class="security-group-container">
    <!-- ====================== 列表页 ====================== -->
    <div v-if="!selectedGroup" class="list-view">
      <div class="filter-container">
        <el-input
          v-model="listQuery.search"
          placeholder="搜索安全组名称/ID/描述"
          clearable
          style="width: 300px;"
          @keyup.enter="handleFilter"
        />

        <el-button type="primary" :icon="Search" @click="handleFilter">搜索</el-button>
        <el-button :icon="Refresh" @click="refreshData">刷新</el-button>
        <el-button type="success" :icon="RefreshLeft" :loading="syncing" @click="handleSyncData">
          {{ syncing ? '同步中...' : '同步数据' }}
        </el-button>
      </div>

      <el-table
        v-loading="listLoading"
        :data="list"
        border
        stripe
        style="width: 100%; margin-top: 20px;"
        @sort-change="sortChange"
      >
        <el-table-column label="安全组名称" prop="security_group_name" min-width="180" fixed="left">
          <template #default="{ row }">
            <el-link type="primary" @click="gotoDetail(row)">{{ row.security_group_name || '-' }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="安全组ID" prop="security_group_id" width="200" />
        <el-table-column label="标签" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.value" size="small" type="info">{{ row.value }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="VPC ID" prop="vpc_id" width="180" show-overflow-tooltip />
        <el-table-column label="地域" prop="region_id" width="100" />
        <el-table-column label="账号" prop="account_name" width="120" />
        <el-table-column label="关联ECS" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.ecs_count > 0 ? 'success' : 'info'">{{ row.ecs_count }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="规则数" width="100" align="center">
          <template #default="{ row }">
            <el-tag>{{ row.rule_count }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="描述" prop="description" min-width="200" show-overflow-tooltip />
        <el-table-column label="创建时间" prop="creation_time" width="170" sortable="custom" />
        <el-table-column label="更新时间" prop="updated_at" width="170" sortable="custom" />
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- ====================== 详情页 ====================== -->
    <div v-else class="detail-view">
      <div class="detail-header">
        <span class="header-title">
          {{ selectedGroup.security_group_name }}
          <span class="header-subtitle">({{ selectedGroup.security_group_id }})</span>
        </span>
        <div class="header-actions">
          <el-button type="primary" :icon="Back" @click="backToList">返回列表</el-button>
        </div>
      </div>

      <el-tabs v-model="activeTab" class="detail-tabs">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="basic">
          <el-card shadow="never" class="info-card">
            <template #header><div class="card-header">基础信息</div></template>
            <el-descriptions :column="3" border>
              <el-descriptions-item label="安全组ID">{{ groupDetail.security_group_id || '-' }}</el-descriptions-item>
              <el-descriptions-item label="安全组名称">{{ groupDetail.security_group_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="描述">{{ groupDetail.description || '-' }}</el-descriptions-item>
              <el-descriptions-item label="VPC ID">{{ groupDetail.vpc_id || '-' }}</el-descriptions-item>
              <el-descriptions-item label="地域">{{ groupDetail.region_id || '-' }}</el-descriptions-item>
              <el-descriptions-item label="账号">{{ groupDetail.account_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="关联ECS数量">
                <el-tag :type="groupDetail.ecs_count > 0 ? 'success' : 'info'">{{ groupDetail.ecs_count }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="规则数量">
                <el-tag>{{ groupDetail.rule_count }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="标签值">{{ groupDetail.value || '-' }}</el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ formatTime(groupDetail.creation_time) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ formatTime(groupDetail.updated_at) }}</el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 标签 -->
          <el-card shadow="never" class="info-card" style="margin-top: 20px;">
            <template #header><div class="card-header">标签</div></template>
            <el-table :data="formatTags(groupDetail.tags)" border stripe empty-text="暂无标签">
              <el-table-column label="标签键" prop="key" />
              <el-table-column label="标签值" prop="value" />
            </el-table>
          </el-card>
        </el-tab-pane>

        <!-- 安全组规则 -->
        <el-tab-pane label="安全组规则" name="rules">
          <div class="rule-filter">
            <el-radio-group v-model="ruleDirection" size="default" @change="handleRuleFilter">
              <el-radio-button label="ingress">入方向规则</el-radio-button>
              <el-radio-button label="egress">出方向规则</el-radio-button>
            </el-radio-group>

            <div class="rule-search">
              <el-input
                v-model="ruleSearchKey"
                placeholder="搜索协议/端口/授权对象"
                clearable
                style="width: 300px; margin-left: 20px;"
                @keyup.enter="handleRuleFilter"
                @clear="handleRuleFilter"
              />
              <el-button type="primary" :icon="Plus" @click="showAddRuleDialog = true" style="margin-left: 10px;">
                添加规则
              </el-button>
            </div>
          </div>

          <el-table
            :data="filteredRules"
            border
            stripe
            style="width: 100%; margin-top: 20px;"
            v-loading="rulesLoading"
          >
            <el-table-column label="策略" width="100">
              <template #default="{ row }">
                <el-tag :type="row.policy === 'accept' ? 'success' : 'danger'" size="small">
                  {{ row.policy === 'accept' ? '允许' : '拒绝' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="优先级" prop="priority" width="90" align="center" />
            <el-table-column label="协议" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.ip_protocol.toUpperCase() }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="端口范围" prop="port_range" width="120" />
            <el-table-column label="授权对象" min-width="250">
              <template #default="{ row }">
                <div v-if="row.direction === 'ingress'">
                  <div v-if="row.source_cidr_ip" class="auth-object">
                    <el-tag type="info" size="small">IP</el-tag>
                    <span style="margin-left: 5px;">{{ row.source_cidr_ip }}</span>
                  </div>
                  <div v-else-if="row.ipv6_source_cidr_ip" class="auth-object">
                    <el-tag type="warning" size="small">IPv6</el-tag>
                    <span style="margin-left: 5px;">{{ row.ipv6_source_cidr_ip }}</span>
                  </div>
                  <div v-else-if="row.source_group_id" class="auth-object">
                    <el-tag type="success" size="small">安全组</el-tag>
                    <span style="margin-left: 5px;">{{ row.source_group_id }}</span>
                    <span v-if="row.source_group_owner_account" class="text-muted">
                      ({{ row.source_group_owner_account }})
                    </span>
                  </div>
                  <div v-else-if="row.source_prefix_list_id" class="auth-object">
                    <el-tag type="primary" size="small">前缀列表</el-tag>
                    <span style="margin-left: 5px;">{{ row.source_prefix_list_id }}</span>
                  </div>
                  <div v-else>-</div>
                </div>
                <div v-else>
                  <div v-if="row.dest_cidr_ip" class="auth-object">
                    <el-tag type="info" size="small">IP</el-tag>
                    <span style="margin-left: 5px;">{{ row.dest_cidr_ip }}</span>
                  </div>
                  <div v-else-if="row.ipv6_dest_cidr_ip" class="auth-object">
                    <el-tag type="warning" size="small">IPv6</el-tag>
                    <span style="margin-left: 5px;">{{ row.ipv6_dest_cidr_ip }}</span>
                  </div>
                  <div v-else-if="row.dest_group_id" class="auth-object">
                    <el-tag type="success" size="small">安全组</el-tag>
                    <span style="margin-left: 5px;">{{ row.dest_group_id }}</span>
                    <span v-if="row.dest_group_owner_account" class="text-muted">
                      ({{ row.dest_group_owner_account }})
                    </span>
                  </div>
                  <div v-else-if="row.dest_prefix_list_id" class="auth-object">
                    <el-tag type="primary" size="small">前缀列表</el-tag>
                    <span style="margin-left: 5px;">{{ row.dest_prefix_list_id }}</span>
                  </div>
                  <div v-else>-</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="描述" prop="description" min-width="150" show-overflow-tooltip />
            <el-table-column label="创建时间" width="170">
              <template #default="{ row }">
                {{ formatTime(row.creation_time) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button type="text" size="small" style="color: #f56c6c" @click="handleDeleteRule(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-container" v-if="rulesPagination.total > 0">
            <el-pagination
              v-model:current-page="rulesPagination.current"
              v-model:page-size="rulesPagination.pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="rulesPagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleRulesSizeChange"
              @current-change="handleRulesPageChange"
            />
          </div>
        </el-tab-pane>

        <!-- 关联实例 -->
        <el-tab-pane label="关联实例" name="instances">
          <el-table
            :data="relatedInstances"
            border
            stripe
            style="width: 100%;"
            v-loading="instancesLoading"
            empty-text="暂无关联实例"
          >
            <el-table-column label="实例ID" prop="instance_id" width="200" />
            <el-table-column label="主机名" prop="hostname" min-width="150" />
            <el-table-column label="实例名称" prop="instance_name" min-width="150" />
            <el-table-column label="私网IP" prop="private_ip" width="120" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'Running' ? 'success' : 'danger'" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="规格" prop="instance_type" width="150" />
            <el-table-column label="地域" prop="region_id" width="100" />
            <el-table-column label="可用区" prop="zone_id" width="120" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 添加规则对话框 -->
    <el-dialog
      v-model="showAddRuleDialog"
      title="添加安全组规则"
      width="600px"
      @closed="resetNewRule"
    >
      <el-form :model="newRule" label-width="120px" :rules="ruleRules" ref="ruleFormRef">
        <el-form-item label="方向" prop="direction">
          <el-radio-group v-model="newRule.direction">
            <el-radio label="ingress">入方向</el-radio>
            <el-radio label="egress">出方向</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="协议" prop="ip_protocol">
          <el-select v-model="newRule.ip_protocol" placeholder="请选择协议" style="width: 200px;">
            <el-option label="ALL" value="all" />
            <el-option label="TCP" value="tcp" />
            <el-option label="UDP" value="udp" />
            <el-option label="ICMP" value="icmp" />
            <el-option label="ICMPv6" value="icmpv6" />
            <el-option label="GRE" value="gre" />
          </el-select>
        </el-form-item>

        <el-form-item label="端口范围" prop="port_range">
          <el-input v-model="newRule.port_range" placeholder="如: 80/80 或 3306/3306 或 22/22" style="width: 200px;" />
          <div class="form-tip">端口范围格式: 起始端口/结束端口，-1/-1表示所有端口</div>
        </el-form-item>

        <el-form-item label="授权类型" prop="auth_type">
          <el-radio-group v-model="newRule.auth_type">
            <el-radio label="cidr">CIDR IP</el-radio>
            <el-radio label="ipv6">IPv6 CIDR</el-radio>
            <el-radio label="security_group">安全组</el-radio>
            <el-radio label="prefix_list">前缀列表</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item
          v-if="newRule.auth_type === 'cidr'"
          :label="newRule.direction === 'ingress' ? '源IP地址段' : '目标IP地址段'"
          prop="cidr_ip"
        >
          <el-input v-model="newRule.cidr_ip" placeholder="如: 0.0.0.0/0 或 192.168.1.0/24" />
        </el-form-item>

        <el-form-item
          v-if="newRule.auth_type === 'ipv6'"
          :label="newRule.direction === 'ingress' ? '源IPv6地址段' : '目标IPv6地址段'"
          prop="ipv6_cidr_ip"
        >
          <el-input v-model="newRule.ipv6_cidr_ip" placeholder="如: ::/0" />
        </el-form-item>

        <el-form-item
          v-if="newRule.auth_type === 'security_group'"
          :label="newRule.direction === 'ingress' ? '源安全组' : '目标安全组'"
          prop="source_group_id"
        >
          <el-select v-model="newRule.source_group_id" placeholder="请选择安全组" style="width: 300px;">
            <el-option
              v-for="group in availableSecurityGroups"
              :key="group.security_group_id"
              :label="`${group.security_group_name} (${group.security_group_id})`"
              :value="group.security_group_id"
            />
          </el-select>
        </el-form-item>

        <el-form-item
          v-if="newRule.auth_type === 'prefix_list'"
          :label="newRule.direction === 'ingress' ? '源前缀列表' : '目标前缀列表'"
          prop="prefix_list_id"
        >
          <el-input v-model="newRule.prefix_list_id" placeholder="请输入前缀列表ID" />
        </el-form-item>

        <el-form-item label="策略" prop="policy">
          <el-radio-group v-model="newRule.policy">
            <el-radio label="accept">允许</el-radio>
            <el-radio label="drop">拒绝</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="优先级" prop="priority">
          <el-input-number v-model="newRule.priority" :min="1" :max="100" />
          <div class="form-tip">数值越小优先级越高，1-100</div>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input v-model="newRule.description" type="textarea" :rows="3" placeholder="请输入规则描述" />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddRuleDialog = false">取消</el-button>
          <el-button type="primary" @click="submitNewRule" :loading="addingRule">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, RefreshLeft, Back, Plus } from '@element-plus/icons-vue'
import {
  fetchSecurityGroups,
  fetchSecurityGroupDetail,
  fetchSecurityGroupRules,
  addSecurityGroupRule,
  deleteSecurityGroupRule,
  fetchSecurityGroupInstances,
  syncSecurityGroups
} from '@/api/aliyun/securitygroup'

// 响应式数据
const list = ref([])
const listLoading = ref(false)
const syncing = ref(false)
const selectedGroup = ref(null)
const groupDetail = ref({})
const activeTab = ref('basic')
const ruleDirection = ref('ingress')
const ruleSearchKey = ref('')
const rules = ref([])
const rulesLoading = ref(false)
const relatedInstances = ref([])
const instancesLoading = ref(false)
const showAddRuleDialog = ref(false)
const addingRule = ref(false)
const ruleFormRef = ref()

// 分页
const pagination = reactive({
  total: 0,
  current: 1,
  pageSize: 20
})

const rulesPagination = reactive({
  total: 0,
  current: 1,
  pageSize: 20
})

// 查询条件
const listQuery = reactive({
  search: '',  // 使用DRF标准的search参数
  region_id: '',
  account_name: '',
  sort: '-updated_at'
})

// 新规则表单
const newRule = reactive({
  direction: 'ingress',
  ip_protocol: 'tcp',
  port_range: '',
  auth_type: 'cidr',
  cidr_ip: '',
  ipv6_cidr_ip: '',
  source_group_id: '',
  prefix_list_id: '',
  policy: 'accept',
  priority: 1,
  description: ''
})

// 规则验证
const ruleRules = {
  direction: [{ required: true, message: '请选择方向', trigger: 'change' }],
  ip_protocol: [{ required: true, message: '请选择协议', trigger: 'change' }],
  port_range: [{ required: true, message: '请输入端口范围', trigger: 'blur' }],
  priority: [{ required: true, message: '请输入优先级', trigger: 'blur' }]
}

// 计算属性
const filteredRules = computed(() => {
  const key = ruleSearchKey.value.toLowerCase()
  return rules.value.filter(rule => {
    if (rule.direction !== ruleDirection.value) return false
    if (!key) return true

    return (
      rule.ip_protocol.toLowerCase().includes(key) ||
      rule.port_range.includes(key) ||
      (rule.source_cidr_ip && rule.source_cidr_ip.toLowerCase().includes(key)) ||
      (rule.dest_cidr_ip && rule.dest_cidr_ip.toLowerCase().includes(key)) ||
      (rule.ipv6_source_cidr_ip && rule.ipv6_source_cidr_ip.toLowerCase().includes(key)) ||
      (rule.ipv6_dest_cidr_ip && rule.ipv6_dest_cidr_ip.toLowerCase().includes(key)) ||
      (rule.description && rule.description.toLowerCase().includes(key))
    )
  })
})

const availableSecurityGroups = computed(() => {
  return list.value.filter(group =>
    group.security_group_id !== selectedGroup.value?.security_group_id
  )
})

// 选项数据
const regionOptions = ref([
  { label: '华东1（杭州）', value: 'cn-hangzhou' },
  { label: '华东2（上海）', value: 'cn-shanghai' },
  { label: '华北1（青岛）', value: 'cn-qingdao' },
  { label: '华北2（北京）', value: 'cn-beijing' },
  { label: '华北3（张家口）', value: 'cn-zhangjiakou' },
  { label: '华南1（深圳）', value: 'cn-shenzhen' },
  { label: '西南1（成都）', value: 'cn-chengdu' },
])

const accountOptions = ref([])

// 方法
const getList = async () => {
  listLoading.value = true
  try {
    const params = {
      ...listQuery,
      page: pagination.current,
      page_size: pagination.pageSize
    }

    const response = await fetchSecurityGroups(params)
    if (response.code === 200) {
      const data = response.data || {}
      list.value = data.results || data.data || []
      pagination.total = data.count || data.total || 0

      // 提取账号选项
      const accounts = [...new Set(list.value.map(item => item.account_name))]
      accountOptions.value = accounts.map(acc => ({ label: acc, value: acc }))
    } else {
      ElMessage.error(response.msg || '获取数据失败')
      list.value = []
      pagination.total = 0
    }
  } catch (err) {
    console.error('获取安全组列表失败:', err)
    ElMessage.error('请求异常')
    list.value = []
    pagination.total = 0
  } finally {
    listLoading.value = false
  }
}

const gotoDetail = async (row) => {
  selectedGroup.value = row
  activeTab.value = 'basic'
  await getGroupDetail(row.security_group_id)
  await getGroupRules(row.security_group_id)
  await getGroupInstances(row.security_group_id)
}

const getGroupDetail = async (groupId) => {
  try {
    const response = await fetchSecurityGroupDetail(groupId)
    if (response.code === 200) {
      groupDetail.value = response.data || {}
    } else {
      ElMessage.error(response.msg || '获取详情失败')
    }
  } catch (err) {
    console.error('获取安全组详情失败:', err)
    ElMessage.error('获取详情失败')
  }
}

const getGroupRules = async (groupId) => {
  rulesLoading.value = true
  try {
    const params = {
      security_group_id: groupId,
      page: rulesPagination.current,
      page_size: rulesPagination.pageSize,
      direction: ruleDirection.value
    }

    const response = await fetchSecurityGroupRules(params)
    if (response.code === 200) {
      const data = response.data || {}
      rules.value = data.results || data.data || []
      rulesPagination.total = data.count || data.total || 0
    } else {
      ElMessage.error(response.msg || '获取规则失败')
      rules.value = []
      rulesPagination.total = 0
    }
  } catch (err) {
    console.error('获取安全组规则失败:', err)
    ElMessage.error('获取规则失败')
    rules.value = []
    rulesPagination.total = 0
  } finally {
    rulesLoading.value = false
  }
}

const getGroupInstances = async (groupId) => {
  instancesLoading.value = true
  try {
    const response = await fetchSecurityGroupInstances(groupId)
    if (response.code === 200) {
      const data = response.data || {}
      relatedInstances.value = data.results || data.data || []
    } else {
      ElMessage.error(response.msg || '获取关联实例失败')
      relatedInstances.value = []
    }
  } catch (err) {
    console.error('获取关联实例失败:', err)
    ElMessage.error('获取关联实例失败')
    relatedInstances.value = []
  } finally {
    instancesLoading.value = false
  }
}

// 解决冲突：重命名同步函数
const handleSyncData = async () => {
  syncing.value = true
  try {
    const response = await syncSecurityGroups()
    if (response.code === 200) {
      ElMessage.success(response.msg || '同步成功')
      getList()
    } else {
      ElMessage.error(response.msg || '同步失败')
    }
  } catch (err) {
    ElMessage.error('同步异常: ' + err.message)
  } finally {
    syncing.value = false
  }
}

const handleFilter = () => {
  pagination.current = 1
  getList()
}

const handlePageChange = (val) => {
  pagination.current = val
  getList()
}

const handleSizeChange = (val) => {
  pagination.pageSize = val
  getList()
}

const handleRuleFilter = () => {
  rulesPagination.current = 1
  if (selectedGroup.value) {
    getGroupRules(selectedGroup.value.security_group_id)
  }
}

const handleRulesPageChange = (val) => {
  rulesPagination.current = val
  if (selectedGroup.value) {
    getGroupRules(selectedGroup.value.security_group_id)
  }
}

const handleRulesSizeChange = (val) => {
  rulesPagination.pageSize = val
  if (selectedGroup.value) {
    getGroupRules(selectedGroup.value.security_group_id)
  }
}

const refreshData = () => {
  listQuery.securityGroupName = ''
  listQuery.securityGroupId = ''
  listQuery.regionId = ''
  listQuery.accountName = ''
  listQuery.sort = '-updated_at'
  pagination.current = 1
  getList()
}

const sortChange = ({ prop, order }) => {
  listQuery.sort = order === 'ascending' ? `+${prop}` : order === 'descending' ? `-${prop}` : '-updated_at'
  handleFilter()
}

const backToList = () => {
  selectedGroup.value = null
  groupDetail.value = {}
  rules.value = []
  relatedInstances.value = []
  activeTab.value = 'basic'
}

const resetNewRule = () => {
  Object.assign(newRule, {
    direction: 'ingress',
    ip_protocol: 'tcp',
    port_range: '',
    auth_type: 'cidr',
    cidr_ip: '',
    ipv6_cidr_ip: '',
    source_group_id: '',
    prefix_list_id: '',
    policy: 'accept',
    priority: 1,
    description: ''
  })
  if (ruleFormRef.value) {
    ruleFormRef.value.resetFields()
  }
}

const submitNewRule = async () => {
  if (!ruleFormRef.value) return

  try {
    await ruleFormRef.value.validate()
    addingRule.value = true

    const payload = {
      security_group: selectedGroup.value.security_group_id,
      direction: newRule.direction,
      ip_protocol: newRule.ip_protocol,
      port_range: newRule.port_range,
      policy: newRule.policy,
      priority: newRule.priority,
      description: newRule.description
    }

    // 根据授权类型设置对应字段
    if (newRule.auth_type === 'cidr') {
      if (newRule.direction === 'ingress') {
        payload.source_cidr_ip = newRule.cidr_ip
      } else {
        payload.dest_cidr_ip = newRule.cidr_ip
      }
    } else if (newRule.auth_type === 'ipv6') {
      if (newRule.direction === 'ingress') {
        payload.ipv6_source_cidr_ip = newRule.ipv6_cidr_ip
      } else {
        payload.ipv6_dest_cidr_ip = newRule.ipv6_cidr_ip
      }
    } else if (newRule.auth_type === 'security_group') {
      if (newRule.direction === 'ingress') {
        payload.source_group_id = newRule.source_group_id
      } else {
        payload.dest_group_id = newRule.source_group_id
      }
    } else if (newRule.auth_type === 'prefix_list') {
      if (newRule.direction === 'ingress') {
        payload.source_prefix_list_id = newRule.prefix_list_id
      } else {
        payload.dest_prefix_list_id = newRule.prefix_list_id
      }
    }

    const response = await addSecurityGroupRule(payload)
    if (response.code === 200) {
      ElMessage.success('添加规则成功')
      showAddRuleDialog.value = false
      getGroupRules(selectedGroup.value.security_group_id)
    } else {
      ElMessage.error(response.msg || '添加规则失败')
    }
  } catch (err) {
    if (err.message !== 'validate') {
      ElMessage.error('提交失败: ' + err.message)
    }
  } finally {
    addingRule.value = false
  }
}

const handleDeleteRule = async (rule) => {
  try {
    await ElMessageBox.confirm(
      `确定删除规则 ${rule.ip_protocol.toUpperCase()}:${rule.port_range} 吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await deleteSecurityGroupRule(rule.rule_id)
    if (response.code === 200) {
      ElMessage.success('删除规则成功')
      getGroupRules(selectedGroup.value.security_group_id)
    } else {
      ElMessage.error(response.msg || '删除规则失败')
    }
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 工具函数
const formatTime = (time) => {
  if (!time) return '-'
  const d = new Date(time)
  return isNaN(d.getTime()) ? time : d.toLocaleString('zh-CN', { hour12: false })
}

const formatTags = (tags) => {
  if (!tags || typeof tags !== 'object') return []
  return Object.entries(tags).map(([key, value]) => ({ key, value }))
}

// 生命周期
onMounted(() => {
  getList()
})
</script>

<style scoped>
.security-group-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 84px);
}

.filter-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  background: #fff;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  background: #fff;
  padding: 10px;
  border-radius: 6px;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(0,0,0,.04);
}

.header-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.header-subtitle {
  font-size: 14px;
  font-weight: normal;
  color: #909399;
  margin-left: 10px;
}

.info-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: bold;
  color: #303133;
}

.rule-filter {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.rule-search {
  display: flex;
  align-items: center;
}

.auth-object {
  display: flex;
  align-items: center;
}

.text-muted {
  color: #909399;
  font-size: 12px;
  margin-left: 5px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
