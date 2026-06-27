<template>
  <div class="app-container">
    <!-- 列表页 -->
    <div v-if="!selectedBucket" class="page-list">
      <!-- 查询卡片 -->
      <el-card shadow="always">
        <el-form ref="queryFormRef" :model="queryParams" :inline="true">
          <el-form-item label="Bucket名称" prop="search">
            <el-input
              v-model="queryParams.search"
              placeholder="Bucket名称模糊查询"
              clearable
              style="width:160px"
              @keyup.enter="handleQuery"
            />
          </el-form-item>
          <el-form-item label="地域" prop="region">
            <el-select v-model="queryParams.region" clearable style="width:120px">
              <el-option label="华东1(杭州)" value="cn-hangzhou" />
              <el-option label="华东2(上海)" value="cn-shanghai" />
              <el-option label="华北1(青岛)" value="cn-qingdao" />
              <el-option label="华北2(北京)" value="cn-beijing" />
              <el-option label="华南1(深圳)" value="cn-shenzhen" />
            </el-select>
          </el-form-item>
          <el-form-item label="存储类型" prop="storage_class">
            <el-select v-model="queryParams.storage_class" clearable style="width:120px">
              <el-option label="标准存储" value="Standard" />
              <el-option label="低频访问" value="IA" />
              <el-option label="归档存储" value="Archive" />
              <el-option label="冷归档" value="ColdArchive" />
            </el-select>
          </el-form-item>
          <el-form-item label="冗余类型" prop="redundancy_type">
            <el-select v-model="queryParams.redundancy_type" clearable style="width:120px">
              <el-option label="本地冗余" value="LRS" />
              <el-option label="同城冗余" value="ZRS" />
            </el-select>
          </el-form-item>
          <el-form-item label="所属账号" prop="account_name">
            <el-select v-model="queryParams.account_name" clearable style="width:160px">
              <el-option v-for="a in accountOptions" :key="a" :label="a" :value="a" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleQuery">
              <el-icon><Search /></el-icon>搜索
            </el-button>
            <el-button @click="resetQuery">
              <el-icon><Refresh /></el-icon>重置
            </el-button>
            <el-button type="success" @click="handleSync">
              <el-icon><RefreshRight /></el-icon>同步
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 列表表格 -->
      <el-card class="mt-10">
        <template #header>
          <div class="card-header">
            <span>OSS Bucket列表</span>
            <el-button type="primary" plain @click="handleExport">
              <el-icon><Download /></el-icon>导出
            </el-button>
          </div>
        </template>
        <el-table
          v-loading="loading"
          :data="tableData"
          stripe
          border
          height="calc(100vh - 360px)"
        >
          <el-table-column prop="name" label="Bucket名称" min-width="200" sortable fixed="left">
            <template #default="{row}">
              <a class="bucket-link" @click="openDetail(row)">{{ row.name }}</a>
            </template>
          </el-table-column>
          <el-table-column prop="region" label="地域" width="120" sortable />
          <el-table-column prop="storage_class" label="存储类型" width="120" />
          <el-table-column label="读写权限" width="100" align="center">
            <template #default="{row}">
              <el-tag :type="getAclType(row.acl)" size="small">
                {{ getAclDisplay(row.acl) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="冗余类型" width="100" align="center">
            <template #default="{row}">
              <el-tag :type="row.redundancy_type === 'ZRS' ? 'success' : 'warning'" size="small">
                {{ getRedundancyDisplay(row.redundancy_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="版本控制" width="90" align="center">
            <template #default="{row}">
              <el-tag :type="row.versioning === 'Enabled' ? 'success' : 'danger'" size="small">
                {{ row.versioning === 'Enabled' ? '已开启' : '未开启' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="传输加速" width="90" align="center">
            <template #default="{row}">
              <el-tag :type="row.transfer_acceleration === 'Enabled' ? 'success' : 'info'" size="small">
                {{ row.transfer_acceleration === 'Enabled' ? '已开启' : '未开启' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="storage" label="容量" width="100" align="right" />
          <el-table-column prop="object_count" label="文件数量" width="100" align="right" />
          <el-table-column prop="monthly_flow" label="当月流量" width="100" align="right" />
          <el-table-column prop="monthly_access_count" label="当月访问" width="100" align="right" />
          <el-table-column prop="account_name" label="所属账号" width="120" sortable />
          <el-table-column label="最后修改" width="160" sortable>
            <template #default="{row}">
              {{ formatTimestamp(row.last_modified_time) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right" align="center">
            <template #default="scope">
              <el-button size="small" type="primary" @click="openDetail(scope.row)">
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.pageSize"
          :page-sizes="[10,20,30,50,100]"
          layout="->, total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </el-card>
    </div>

    <!-- 详情页 -->
    <div v-else class="page-detail">
      <!-- 面包屑 -->
      <div class="detail-header">
        <el-breadcrumb separator-class="el-icon-arrow-right">
          <el-breadcrumb-item>
            <a @click="closeDetail">OSS管理</a>
          </el-breadcrumb-item>
          <el-breadcrumb-item>Bucket详情</el-breadcrumb-item>
        </el-breadcrumb>
        <el-button icon="el-icon-back" @click="closeDetail">返回列表</el-button>
      </div>

      <el-card v-loading="detailLoading" shadow="never">
        <template #header>
          <span>OSS Bucket详情 - {{ bucketDetail.name }}</span>
        </template>

        <el-descriptions title="基本信息" :column="2" border>
          <el-descriptions-item label="Bucket名称">{{ bucketDetail.name }}</el-descriptions-item>
          <el-descriptions-item label="地域">{{ bucketDetail.region }}</el-descriptions-item>
          <el-descriptions-item label="存储类型">{{ bucketDetail.storage_class }}</el-descriptions-item>
          <el-descriptions-item label="冗余类型">
            <el-tag :type="bucketDetail.redundancy_type === 'ZRS' ? 'success' : 'warning'">
              {{ getRedundancyDisplay(bucketDetail.redundancy_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="读写权限">
            <el-tag :type="getAclType(bucketDetail.acl)">
              {{ getAclDisplay(bucketDetail.acl) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="版本控制">
            <el-tag :type="bucketDetail.versioning === 'Enabled' ? 'success' : 'danger'">
              {{ bucketDetail.versioning === 'Enabled' ? '已开启' : '未开启' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="传输加速">
            <el-tag :type="bucketDetail.transfer_acceleration === 'Enabled' ? 'success' : 'info'">
              {{ bucketDetail.transfer_acceleration === 'Enabled' ? '已开启' : '未开启' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="归档直读">
            <el-tag :type="bucketDetail.archive_direct_read === 'Enabled' ? 'success' : 'danger'">
              {{ bucketDetail.archive_direct_read === 'Enabled' ? '已开启' : '未开启' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(bucketDetail.creation_date) }}</el-descriptions-item>
          <el-descriptions-item label="最后修改时间">{{ formatTimestamp(bucketDetail.last_modified_time) }}</el-descriptions-item>
          <el-descriptions-item label="所属账号">{{ bucketDetail.account_name }}</el-descriptions-item>
        </el-descriptions>

        <el-divider />
        <h3>存储用量</h3>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="总存储量">{{ bucketDetail.storage }}</el-descriptions-item>
          <el-descriptions-item label="月同比增长">
            {{ bucketDetail.storage_growth && bucketDetail.storage_growth > 0 ? bucketDetail.storage_growth + '%' : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="标准型存储">{{ bucketDetail.standard_storage }}</el-descriptions-item>
          <el-descriptions-item label="低频型存储">{{ bucketDetail.ia_storage }}</el-descriptions-item>
          <el-descriptions-item label="归档型存储">{{ bucketDetail.archive_storage }}</el-descriptions-item>
          <el-descriptions-item label="冷归档型存储">{{ bucketDetail.cold_archive_storage }}</el-descriptions-item>
          <el-descriptions-item label="深度冷归档型存储">{{ bucketDetail.deep_cold_archive_storage }}</el-descriptions-item>
        </el-descriptions>

        <el-divider />
        <h3>访问端点</h3>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="外网Endpoint">{{ bucketDetail.extranet_endpoint || '-' }}</el-descriptions-item>
          <el-descriptions-item label="内网Endpoint">{{ bucketDetail.intranet_endpoint || '-' }}</el-descriptions-item>
        </el-descriptions>

        <el-divider />
        <h3>Bucket 授权策略</h3>
        <el-alert type="info" :closable="false" class="mb-16">
          <p>Bucket Policy 是 OSS 推出的针对 Bucket 的授权策略，您可以通过 Bucket Policy 授权子账户和其他账号访问您指定的 OSS 资源。</p>
        </el-alert>

        <el-table
          v-if="bucketDetail.policy_info && filteredPolicyPrincipals.length"
          :data="filteredPolicyPrincipals"
          stripe
          border
          class="policy-table"
        >
          <el-table-column type="expand" width="60">
            <template #default="{ row }">
              <div class="policy-detail-expand">
                <div v-if="row.expandedStatements && row.expandedStatements.length">
                  <table class="inner-table">
                    <colgroup>
                      <col style="width: 60px">
                      <col style="width: 298px">
                      <col style="width: 296px">
                      <col style="width: 197px">
                      <col style="width: 355px">
                      <col style="width: 80px">
                    </colgroup>
                    <tbody>
                      <tr
                        v-for="(statement, index) in row.expandedStatements"
                        :key="index"
                        class="inner-row"
                      >
                        <td class="inner-cell expand-cell"></td>
                        <td class="inner-cell resource-cell">
                          <div class="content-list">
                            <div v-for="(resource, resIndex) in statement.resources" :key="resIndex" class="content-item">
                              {{ simplifyResource(resource) }}
                            </div>
                          </div>
                        </td>
                        <td class="inner-cell action-cell">
                          <div class="content-list">
                            <div v-for="(action, actionIndex) in statement.actions" :key="actionIndex" class="content-item">
                              {{ action }}
                            </div>
                          </div>
                        </td>
                        <td class="inner-cell condition-cell">
                          <div class="content-list">
                            <div v-if="statement.conditions && statement.conditions.length">
                              <div v-for="(condition, condIndex) in statement.conditions" :key="condIndex" class="content-item">
                                {{ condition }}
                              </div>
                            </div>
                            <span v-else class="empty-text">-</span>
                          </div>
                        </td>
                        <td class="inner-cell user-cell">
                          <div class="user-content">
                            <div class="display-name">{{ row.display_name }}</div>
                            <div class="principal-name">{{ row.user_principal_name }}</div>
                          </div>
                        </td>
                        <td class="inner-cell effect-cell">
                          <el-tag :type="statement.effect === 'Allow' ? 'success' : 'danger'" size="small">
                            {{ statement.effect === 'Allow' ? '允许' : '拒绝' }}
                          </el-tag>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="no-statements">
                  <el-empty description="暂无策略明细" :image-size="60" />
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="授权资源" min-width="150">
            <template #default="{row}">
              <div v-for="(resource, index) in row.resources" :key="index" class="resource-item">
                {{ simplifyResource(resource) }}
              </div>
            </template>
          </el-table-column>

          <el-table-column label="授权操作" min-width="150">
            <template #default="{row}">
              <div class="action-content">
                <el-tag
                  :type="getPermissionType(mapActionsToPermissionGroup(row.actions))"
                  size="small"
                  class="action-tag"
                >
                  {{ mapActionsToPermissionGroup(row.actions) }}
                </el-tag>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="条件" min-width="100">
            <template #default="{row}">
              <div v-if="row.conditions && row.conditions.length">
                <el-tooltip :content="row.conditions.join('; ')" placement="top">
                  <el-tag size="small" type="info">有条件</el-tag>
                </el-tooltip>
              </div>
              <span v-else>-</span>
            </template>
          </el-table-column>

          <el-table-column label="授权用户" min-width="180">
            <template #default="{row}">
              <div class="user-info">
                <div class="display-name">{{ row.display_name }}</div>
                <div class="principal-name">{{ row.user_principal_name }}</div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="效力" width="80" align="center">
            <template #default="{row}">
              <el-tag :type="row.effect === 'Allow' ? 'success' : 'danger'" size="small">
                {{ row.effect === 'Allow' ? '允许' : '拒绝' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>

        <el-empty
          v-else
          :description="bucketDetail.policy_info ? '暂无授权策略' : '策略信息加载中...'"
          :image-size="80"
        />

        <el-divider />
        <h3>策略信息</h3>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="策略状态">
            <el-tag :type="bucketDetail.tags && bucketDetail.tags.policy && bucketDetail.tags.policy.is_public ? 'danger' : 'success'">
              {{ bucketDetail.tags && bucketDetail.tags.policy ? (bucketDetail.tags.policy.is_public ? '公开' : '私有') : '未知' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="策略内容">
            <div v-if="bucketDetail.tags && bucketDetail.tags.policy && bucketDetail.tags.policy.policy_content" class="policy-content">
              <pre>{{ formatPolicyContent(bucketDetail.tags.policy.policy_content) }}</pre>
            </div>
            <span v-else>暂无策略内容</span>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider />
        <h3>CNAME 域名信息</h3>
        <el-table
          v-if="bucketDetail.tags && bucketDetail.tags.cname && bucketDetail.tags.cname.length"
          :data="bucketDetail.tags.cname"
          stripe
          border
        >
          <el-table-column prop="domain" label="域名" min-width="200" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{row}">
              <el-tag :type="row.status === 'Enabled' ? 'success' : 'danger'">
                {{ row.status === 'Enabled' ? '已启用' : '未启用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="证书信息" min-width="250">
            <template #default="{row}">
              <div v-if="row.certificate">
                <div>类型: {{ row.certificate.type }}</div>
                <div>状态: {{ row.certificate.status }}</div>
                <div>有效期: {{ formatCertDate(row.certificate.valid_start_date) }} - {{ formatCertDate(row.certificate.valid_end_date) }}</div>
              </div>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="last_modified" label="最后修改" width="160">
            <template #default="{row}">
              {{ formatDateTime(row.last_modified) }}
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无CNAME记录" :image-size="80" />

        <el-divider />
        <h3>标签信息</h3>
        <el-table
          v-if="bucketDetail.tags && Object.keys(bucketDetail.tags).filter(k => k !== 'cname' && k !== 'policy').length"
          :data="Object.entries(bucketDetail.tags).filter(([k]) => k !== 'cname' && k !== 'policy')"
          stripe
          border
        >
          <el-table-column prop="0" label="标签键" min-width="150" />
          <el-table-column prop="1" label="标签值" min-width="200" />
        </el-table>
        <el-empty v-else description="暂无标签信息" :image-size="80" />

        <el-divider />
        <h3>访问统计</h3>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="当月流量">{{ bucketDetail.monthly_flow }}</el-descriptions-item>
          <el-descriptions-item label="当月访问次数">{{ bucketDetail.monthly_access_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="文件总数">{{ bucketDetail.object_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="文件碎片">{{ bucketDetail.fragments || 0 }}</el-descriptions-item>
          <el-descriptions-item label="Multipart Uploads">{{ bucketDetail.multipart_uploads || 0 }}</el-descriptions-item>
        </el-descriptions>

      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, RefreshRight, Download } from '@element-plus/icons-vue'
import { listOSSBuckets, syncOSSBuckets, exportOSSBuckets, getOSSBucketDetail } from '@/api/aliyun/oss'
import { handleFileError } from '@/utils/export'

// State
const loading = ref(false)
const detailLoading = ref(false)
const tableData = ref([])
const total = ref(0)
const accountOptions = ref([])
const selectedBucket = ref(null)
const bucketDetail = ref({})
const queryFormRef = ref(null)

const queryParams = reactive({
  page: 1,
  pageSize: 10,
  search: '',
  region: '',
  storage_class: '',
  redundancy_type: '',
  account_name: ''
})

// Computed
const filteredPolicyPrincipals = computed(() => {
  if (!bucketDetail.value.policy_info || !bucketDetail.value.policy_info.principals?.length) {
    return []
  }
  return bucketDetail.value.policy_info.principals
    .filter(p => !shouldHidePolicy(p))
    .map(p => ({
      ...p,
      expandedStatements: getExpandedStatements(p)
    }))
})

// Helper functions
const shouldHidePolicy = (principal) => {
  const hasWildcardPrefix = principal.conditions?.some(c =>
    c.includes('StringLike') && c.includes('oss:Prefix') && c.includes('*')
  )
  return hasWildcardPrefix &&
    principal.actions?.length === 2 &&
    principal.actions.includes('oss:ListObjects') &&
    principal.actions.includes('oss:GetObject')
}

const getExpandedStatements = (principal) => {
  if (principal.rawStatements && principal.rawStatements.length) {
    return principal.rawStatements.map(stmt => parseStatement(stmt))
  }
  return [{
    effect: principal.effect || 'Allow',
    resources: principal.resources || [],
    actions: principal.actions || [],
    conditions: principal.conditions || []
  }]
}

const parseStatement = (statement) => {
  const resources = Array.isArray(statement.Resource)
    ? statement.Resource
    : (statement.Resource ? [statement.Resource] : [])

  const actions = Array.isArray(statement.Action)
    ? statement.Action
    : (statement.Action ? [statement.Action] : [])

  const conditions = []
  if (statement.Condition) {
    Object.entries(statement.Condition).forEach(([type, value]) => {
      Object.entries(value).forEach(([key, val]) => {
        const v = Array.isArray(val) ? val.join(', ') : val
        conditions.push(`${type}: ${key} = ${v}`)
      })
    })
  }

  return { effect: statement.Effect || '', resources, actions, conditions }
}

const simplifyResource = (resource) => {
  return resource.replace(/acs:oss:\*:\d+:/, '')
}

const mapActionsToPermissionGroup = (actions) => {
  if (!actions || !actions.length) return '未知权限'
  if (actions.includes('oss:*')) return '完全控制'

  const patterns = [
    {
      name: '读/写',
      actions: ['oss:GetObject', 'oss:PutObject', 'oss:GetObjectAcl', 'oss:PutObjectAcl',
                'oss:ListObjects', 'oss:AbortMultipartUpload', 'oss:ListParts',
                'oss:RestoreObject', 'oss:GetVodPlaylist', 'oss:PostVodPlaylist',
                'oss:PublishRtmpStream', 'oss:ListObjectVersions', 'oss:GetObjectVersion',
                'oss:GetObjectVersionAcl', 'oss:RestoreObjectVersion']
    },
    {
      name: '只读（包含ListObject操作）',
      actions: ['oss:GetObject', 'oss:GetObjectAcl', 'oss:ListObjects',
                'oss:RestoreObject', 'oss:GetVodPlaylist', 'oss:ListObjectVersions',
                'oss:GetObjectVersion', 'oss:GetObjectVersionAcl', 'oss:RestoreObjectVersion']
    },
    {
      name: '只读（不包含ListObject操作）',
      actions: ['oss:GetObject', 'oss:GetObjectAcl', 'oss:RestoreObject',
                'oss:GetVodPlaylist', 'oss:GetObjectVersion',
                'oss:GetObjectVersionAcl', 'oss:RestoreObjectVersion']
    }
  ]

  const set = new Set(actions)
  for (const p of patterns) {
    if (p.actions.every(a => set.has(a))) {
      return p.name
    }
  }
  return actions.map(a => a.replace('oss:', '')).join(', ')
}

const getPermissionType = (permission) => {
  if (!permission) return ''
  const map = {
    '只读（不包含ListObject操作）': 'info',
    '只读（包含ListObject操作）': 'primary',
    '读/写': 'warning',
    '完全控制': 'danger'
  }
  if (map[permission]) return map[permission]
  if (permission.includes('Put') || permission.includes('Delete')) return 'warning'
  if (permission.includes('Get') || permission.includes('List')) return 'info'
  return 'default'
}

const getAclDisplay = (acl) => {
  const m = { private: '私有', 'public-read': '公共读', 'public-read-write': '公共读写' }
  return m[acl] || acl
}

const getAclType = (acl) => {
  const m = { private: 'success', 'public-read': 'warning', 'public-read-write': 'danger' }
  return m[acl] || 'info'
}

const getRedundancyDisplay = (type) => {
  const m = { LRS: '本地冗余', ZRS: '同城冗余' }
  return m[type] || type
}

const formatPolicyContent = (policyContent) => {
  if (!policyContent) return ''
  try {
    const policy = JSON.parse(policyContent)
    return JSON.stringify(policy, null, 2)
  } catch (e) {
    return policyContent
  }
}

const formatDateTime = (dateString) => {
  if (!dateString) return ''
  try { return new Date(dateString).toLocaleString('zh-CN') }
  catch { return dateString }
}

const formatTimestamp = (ts) => {
  if (!ts) return '-'
  try { return new Date(ts * 1000).toLocaleString('zh-CN') }
  catch { return ts.toString() }
}

const formatCertDate = (dateString) => {
  if (!dateString) return ''
  try {
    if (dateString.includes('GMT')) {
      return new Date(dateString).toLocaleDateString('zh-CN')
    }
    return dateString
  } catch {
    return dateString
  }
}

// API methods
const getList = async () => {
  loading.value = true
  try {
    const params = { ...queryParams }
    Object.keys(params).forEach(k => (params[k] === '' || params[k] === undefined) && delete params[k])

    const res = await listOSSBuckets(params)
    const { code, data, msg } = res
    if (code === 200) {
      tableData.value = data.data || []
      total.value = data.total || 0
      accountOptions.value = [...new Set(tableData.value.map(i => i.account_name))].filter(Boolean)
    } else {
      ElMessage.error(msg || '获取数据失败')
    }
  } catch (e) {
    ElMessage.error('请求异常')
    console.error(e)
  } finally {
    loading.value = false
  }
}

const fetchBucketDetail = async (bucketName) => {
  detailLoading.value = true
  try {
    const res = await getOSSBucketDetail(bucketName)
    const { code, data } = res
    if (code !== 200) return

    if (data.policy_info && data.tags?.policy?.policy_content) {
      try {
        const policy = JSON.parse(data.tags.policy.policy_content)
        const statements = policy.Statement || []

        data.policy_info.principals = data.policy_info.principals || []
        data.policy_info.principals.forEach(p => {
          const matched = statements.filter(stmt => {
            if (!stmt.Principal) return false
            let principals = []
            if (Array.isArray(stmt.Principal)) principals = stmt.Principal
            else if (typeof stmt.Principal === 'object') principals = Object.values(stmt.Principal).flat()
            else principals = [stmt.Principal]

            return principals.some(pr => {
              if (typeof pr !== 'string') return false
              return pr.includes(p.user_principal_name) ||
                     pr.includes(p.user_principal_name?.split('@')[0])
            })
          })
          p.rawStatements = matched
        })
      } catch (e) {
        console.error('解析 policy_content 失败', e)
      }
    }

    bucketDetail.value = data
  } catch (e) {
    console.error('获取详情失败', e)
  } finally {
    detailLoading.value = false
  }
}

// Event handlers
const handleQuery = () => {
  queryParams.page = 1
  getList()
}

const resetQuery = () => {
  queryFormRef.value?.resetFields()
  queryParams.page = 1
  queryParams.pageSize = 20
  queryParams.search = ''
  queryParams.region = ''
  queryParams.storage_class = ''
  queryParams.redundancy_type = ''
  queryParams.account_name = ''
  getList()
}

const handleSync = async () => {
  loading.value = true
  try {
    const res = await syncOSSBuckets()
    if (res?.code === 200) {
      ElMessage.success(res.msg || '同步成功')
      getList()
    } else {
      ElMessage.error(res?.msg || '同步失败')
    }
  } catch (e) {
    ElMessage.error('同步异常')
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleExport = () => {
  ElMessageBox.confirm('是否确认导出当前条件的 OSS Bucket 数据？', '导出确认', { type: 'warning' })
    .then(() => {
      const params = { ...queryParams }
      Object.keys(params).forEach(k => (params[k] === '' || params[k] === undefined) && delete params[k])
      return exportOSSBuckets(params)
    })
    .then(res => {
      handleFileError(res, `oss_buckets_${Date.now()}.xlsx`)
    })
    .catch(err => {
      if (err !== 'cancel') ElMessage.error('导出失败')
    })
}

const openDetail = (row) => {
  selectedBucket.value = row
  fetchBucketDetail(row.name)
}

const closeDetail = () => {
  selectedBucket.value = null
  bucketDetail.value = {}
}

const handleSizeChange = (val) => {
  queryParams.pageSize = val
  queryParams.page = 1
  getList()
}

const handleCurrentChange = (val) => {
  queryParams.page = val
  getList()
}

// Lifecycle
onMounted(() => {
  getList()
})

onUnmounted(() => {
  // Clean up state on unmount to prevent memory leaks
  selectedBucket.value = null
  bucketDetail.value = {}
  tableData.value = []
})
</script>

<style scoped>
.app-container { padding: 20px; }
.mt-10 { margin-top: 10px; }
.mb-16 { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; background: #fff; padding: 10px 15px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,.1); }
.bucket-link { color: #409eff; cursor: pointer; text-decoration: none; }
.bucket-link:hover { text-decoration: underline; }
.policy-content { max-height: 200px; overflow: auto; background: #f5f5f5; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px; }
.user-info { display: flex; flex-direction: column; gap: 2px; }
.display-name { font-weight: 500; color: #303133; }
.principal-name { font-size: 12px; color: #909399; }
.action-content { word-break: break-all; white-space: normal; }
.action-tag { max-width: 100%; white-space: normal; word-break: break-word; height: auto; line-height: 1.5; padding: 4px 8px; margin: 2px 0; }
.resource-item { word-break: break-all; white-space: normal; margin: 2px 0; }
.policy-table .el-table__cell { padding: 8px 0; }
.policy-detail-expand { padding: 8px 0; background: #fafafa; }
.content-list { max-height: 120px; overflow-y: auto; width: 100%; }
.content-item { padding: 4px 6px; margin: 2px 0; background: transparent; border-radius: 3px; font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; font-size: 12px; line-height: 1.4; word-break: break-all; }
.empty-text { color: #c0c4cc; font-size: 14px; }
.user-content { width: 100%; }
.effect-cell { text-align: center; justify-content: center; align-items: center; }
.no-statements { text-align: center; padding: 20px; color: #909399; background: white; }
.inner-table { width: 100%; table-layout: fixed; border-collapse: collapse; }
:deep(.policy-table .el-table__cell) { padding: 12px 0; }
:deep(.policy-table .el-table__row) { height: auto; }
</style>
