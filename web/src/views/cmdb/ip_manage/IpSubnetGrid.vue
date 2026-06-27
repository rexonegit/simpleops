<template>
  <div class="ip-overview-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">内网IP地址总览 (Intranet)</span>

          <div class="header-center">
            <span class="selector-label">网络范围 (CIDR)</span>
            <el-select
              v-model="selectedSegment"
              placeholder="请选择内网网段"
              class="segment-select"
              @change="handleSegmentChange"
              filterable
            >
              <el-option
                v-for="item in segmentOptions"
                :key="item.network"
                :label="item.cidr"
                :value="item.network"
              >
                <div class="segment-option">
                  <span class="cidr-text">{{ item.cidr }}</span>
                  <span class="ip-count">({{ item.used }}/{{ item.total }})</span>
                </div>
              </el-option>
            </el-select>
          </div>

          <div class="header-actions">
            <el-button type="primary" :loading="syncLoading" @click="handleSync">
              <el-icon class="el-icon--left"><Refresh /></el-icon>同步IP数据
            </el-button>
            <el-button type="success" @click="handleAdd()">
              <el-icon class="el-icon--left"><Plus /></el-icon>新增IP
            </el-button>
          </div>
        </div>
      </template>

      <!-- 网段卡片 -->
      <div class="segment-cards-row">
        <div
          v-for="segment in segmentStats"
          :key="segment.network"
          class="segment-card"
          :class="{ active: selectedSegment === segment.network }"
          @click="selectSegment(segment.network)"
        >
          <div class="card-cidr">{{ segment.cidr }}</div>
          <div class="card-stats">
            <span class="stat used">{{ segment.used }}</span>
            <span class="divider">/</span>
            <span class="stat total">{{ segment.total }}</span>
          </div>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div class="simple-stats-row" v-if="currentSegmentStats">
        <div class="simple-stat">
          <span class="label">总IP</span>
          <span class="value">{{ currentSegmentStats.total }}</span>
        </div>
        <div class="simple-stat used">
          <span class="label">已用</span>
          <span class="value">{{ currentSegmentStats.used }}</span>
        </div>
        <div class="simple-stat online">
          <span class="label">在线</span>
          <span class="value">{{ onlineCount }}</span>
        </div>
        <div class="simple-stat available">
          <span class="label">空闲</span>
          <span class="value">{{ currentSegmentStats.available }}</span>
        </div>
        <div class="simple-stat reserved">
          <span class="label">保留</span>
          <span class="value">{{ currentSegmentStats.reserved }}</span>
        </div>
      </div>

      <!-- 图例与搜索工具栏 -->
      <div class="toolbar-row">
        <div class="legend-group">
          <span class="legend-item">
            <span class="dot dot-available"></span>空闲
          </span>
          <span class="legend-item">
            <span class="dot dot-used"></span>已使用
          </span>
          <span class="legend-item">
            <span class="dot dot-online"></span>在线
          </span>
          <span class="legend-item">
            <span class="dot dot-reserved"></span>保留
          </span>
          <span class="legend-item">
            <span class="dot dot-deprecated"></span>废弃
          </span>
        </div>

        <!-- 🔥 增强搜索区域 -->
        <div class="search-area">
          <el-input
            v-model="searchQuery"
            placeholder="搜索 IP / 主机名 / 负责人"
            clearable
            style="width: 280px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </div>
      </div>

      <!-- 搜索结果提示 -->
      <div v-if="searchQuery && searchQuery.trim()" class="search-result-tips">
        <el-tag type="info" closable @close="resetSearch">
          搜索结果: 找到 {{ filteredIpList.length }} 个匹配项
        </el-tag>
      </div>

      <!-- IP 网格 -->
      <div class="ip-grid-container" v-loading="listLoading">
        <div v-if="filteredIpList.length === 0" class="empty-result">
          <el-empty description="未找到匹配的 IP 地址" />
        </div>
        <div v-else class="ip-grid">
          <div
            v-for="ip in filteredIpList"
            :key="ip.suffix"
            class="ip-box"
            :class="getIpStatusClass(ip)"
            @click="handleIpClick(ip)"
          >
            <span class="ip-num">{{ ip.suffix }}</span>
            <span class="ip-status">{{ getIpStatusText(ip.status) }}</span>
            <div v-if="ip.hostname" class="ip-hostname">{{ ip.hostname }}</div>
            <div v-if="ip.owner" class="ip-owner">{{ ip.owner }}</div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- IP 详情抽屉 -->
    <el-drawer v-model="detailVisible" title="IP 详情" size="400px">
      <div v-if="currentDetail" class="ip-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="IP 地址">{{ currentDetail.ip_address }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(currentDetail.status)">
              {{ getIpStatusText(currentDetail.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="主机名">{{ currentDetail.hostname || '-' }}</el-descriptions-item>
          <el-descriptions-item label="所属实例">{{ currentDetail.bound_instance_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="来源">{{ currentDetail.source || '-' }}</el-descriptions-item>
          <el-descriptions-item label="环境">{{ currentDetail.environment || '-' }}</el-descriptions-item>
          <el-descriptions-item label="负责人">{{ currentDetail.owner || '-' }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ currentDetail.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ currentDetail.updated_at || '-' }}</el-descriptions-item>
        </el-descriptions>
        <div class="drawer-footer">
          <el-button type="primary" @click="handleEditFromDetail">编辑</el-button>
          <el-button @click="detailVisible = false">关闭</el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 新增/编辑 IP 对话框 -->
    <el-dialog :title="dialogTitle" v-model="dialogVisible" width="600px" @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="IP地址" prop="ip_address">
          <el-input v-model="form.ip_address" :disabled="isEdit" placeholder="例如: 10.164.12.100" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="使用中" value="used" />
            <el-option label="空闲" value="available" />
            <el-option label="在线" value="online" />
            <el-option label="保留" value="reserved" />
            <el-option label="废弃" value="deprecated" />
          </el-select>
        </el-form-item>
        <el-form-item label="主机名" prop="hostname">
          <el-input v-model="form.hostname" placeholder="请输入主机名" />
        </el-form-item>
        <el-form-item label="MAC地址" prop="mac_address">
          <el-input v-model="form.mac_address" placeholder="请输入MAC地址" />
        </el-form-item>
        <el-form-item label="负责人" prop="owner">
          <el-input v-model="form.owner" placeholder="请输入负责人" />
        </el-form-item>
        <el-form-item label="所属实例" prop="bound_instance_name">
          <el-input v-model="form.bound_instance_name" placeholder="请输入所属实例" />
        </el-form-item>
        <el-form-item label="环境" prop="environment">
          <el-input v-model="form.environment" placeholder="例如: prod, dev, test" />
        </el-form-item>
        <el-form-item label="来源" prop="source">
          <el-select v-model="form.source" style="width: 100%">
            <el-option label="手动" value="manual" />
            <el-option label="阿里云" value="aliyun" />
            <el-option label="机房" value="datacenter" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" rows="3" placeholder="请输入描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Plus, Search } from '@element-plus/icons-vue'
import {
  getIPAddressList,
  syncIPAddress,
  getIPSegments,
  createIPAddress,
  updateIPAddress,
  deleteIPAddress
} from '@/api/cmdb/ip_manage'

const listLoading = ref(false)
const syncLoading = ref(false)
const submitLoading = ref(false)
const segmentStats = ref([])
const ipList = ref([])
const selectedSegment = ref('')
const searchQuery = ref('')
const detailVisible = ref(false)
const currentDetail = ref({})
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const form = reactive({
  id: '',
  ip_address: '',
  type: 'intranet',
  status: 'used',
  hostname: '',
  mac_address: '',
  owner: '',
  bound_instance_name: '',
  environment: '',
  source: 'manual',
  description: ''
})

const rules = {
  ip_address: [{ required: true, message: '请输入IP地址', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑IP地址' : '新增IP地址')
const currentSegmentStats = computed(() => segmentStats.value.find(s => s.network === selectedSegment.value) || null)
const onlineCount = computed(() => ipList.value.filter(ip => ip.status === 'online').length)

const segmentOptions = computed(() => {
  return segmentStats.value.map(s => ({
    network: s.network,
    cidr: s.cidr,
    total: s.total,
    used: s.used
  }))
})

// 🔥 增强的搜索过滤逻辑 - 支持 IP、主机名、负责人
const filteredIpList = computed(() => {
  if (!searchQuery.value || !searchQuery.value.trim()) return ipList.value

  const query = searchQuery.value.toLowerCase().trim()

  return ipList.value.filter(ip => {
    // 搜索 IP 后缀 (如输入 100 匹配 10.164.9.100)
    const suffixMatch = ip.suffix.toString().includes(query)

    // 搜索完整 IP 地址
    const ipMatch = ip.ip_address && ip.ip_address.toLowerCase().includes(query)

    // 搜索主机名
    const hostnameMatch = ip.hostname && ip.hostname.toLowerCase().includes(query)

    // 搜索负责人
    const ownerMatch = ip.owner && ip.owner.toLowerCase().includes(query)

    // 搜索所属实例
    const instanceMatch = ip.bound_instance_name && ip.bound_instance_name.toLowerCase().includes(query)

    return suffixMatch || ipMatch || hostnameMatch || ownerMatch || instanceMatch
  })
})

const getApiSegmentParam = (network) => {
  if (!network) return ''
  const parts = network.split('.')
  if (parts.length === 3) return network + '.0'
  return network
}

const fetchSegmentStats = async () => {
  try {
    const res = await getIPSegments({ type: 'intranet' })
    const payload = res.data || res
    if (payload.data) {
      segmentStats.value = payload.data
      if (segmentStats.value.length > 0 && !selectedSegment.value) {
        selectedSegment.value = segmentStats.value[0].network
        await fetchIpList()
      }
    } else {
      segmentStats.value = payload || []
      if (segmentStats.value.length > 0 && !selectedSegment.value) {
        selectedSegment.value = segmentStats.value[0].network
        await fetchIpList()
      }
    }
  } catch (error) {
    ElMessage.error('获取网段统计失败')
  }
}

const fetchIpList = async () => {
  if (!selectedSegment.value) return
  listLoading.value = true
  try {
    const apiSegment = getApiSegmentParam(selectedSegment.value)
    const res = await getIPAddressList({
      segment: apiSegment,
      type: 'intranet',
      pageSize: 1000,
      page: 1
    })
    const payload = res.data || res
    let existingIps = []
    if (payload.data && Array.isArray(payload.data.data)) {
      existingIps = payload.data.data
    } else if (payload.data && Array.isArray(payload.data)) {
      existingIps = payload.data
    } else if (Array.isArray(payload)) {
      existingIps = payload
    }
    const segmentPrefix = selectedSegment.value.replace(/\.0$/, '')
    ipList.value = generateFullIpList(segmentPrefix, existingIps)
  } catch (error) {
    ElMessage.error('获取 IP 列表失败')
  } finally {
    listLoading.value = false
  }
}

const generateFullIpList = (segmentPrefix, existingIps) => {
  const ipMap = new Map()
  existingIps.forEach(ip => {
    const parts = ip.ip_address.split('.')
    const suffix = parseInt(parts[parts.length - 1])
    ipMap.set(suffix, { suffix, ...ip })
  })
  const fullList = []
  for (let i = 1; i <= 254; i++) {
    if (ipMap.has(i)) {
      fullList.push(ipMap.get(i))
    } else {
      fullList.push({
        suffix: i,
        ip_address: `${segmentPrefix}.${i}`,
        status: 'available',
        hostname: null,
        bound_instance_name: null,
        owner: null
      })
    }
  }
  return fullList
}

const selectSegment = (network) => {
  selectedSegment.value = network
  // 切换网段时清空搜索
  searchQuery.value = ''
  fetchIpList()
}

const handleSegmentChange = () => {
  searchQuery.value = ''
  fetchIpList()
}

// 🔥 搜索处理函数
const handleSearch = () => {
  // 搜索逻辑已在 computed 中实现，这里可以添加额外的处理
  if (filteredIpList.value.length === 0) {
    ElMessage.info('未找到匹配的 IP 地址')
  }
}

// 🔥 重置搜索
const resetSearch = () => {
  searchQuery.value = ''
}

const handleIpClick = (ip) => {
  if (ip.status === 'available') {
    handleAdd(ip.ip_address)
  } else if (ip.id) {
    currentDetail.value = ip
    detailVisible.value = true
  }
}

const handleEditFromDetail = () => {
  detailVisible.value = false
  handleEdit(currentDetail.value)
}

const handleAdd = (ipAddress = '') => {
  isEdit.value = false
  resetForm()
  if (ipAddress) {
    form.ip_address = ipAddress
    form.type = 'intranet'
  }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  dialogVisible.value = true
  Object.assign(form, {
    id: row.id,
    ip_address: row.ip_address,
    type: row.type || 'intranet',
    status: row.status,
    hostname: row.hostname || '',
    mac_address: row.mac_address || '',
    owner: row.owner || '',
    bound_instance_name: row.bound_instance_name || '',
    environment: row.environment || '',
    source: row.source || 'manual',
    description: row.description || ''
  })
}

const submitForm = async () => {
  try {
    await formRef.value.validate()
    submitLoading.value = true
    const submitData = { ...form }
    delete submitData.id
    if (isEdit.value) {
      await updateIPAddress(form.id, submitData)
      ElMessage.success('更新成功')
    } else {
      await createIPAddress(submitData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchIpList()
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

const resetForm = () => {
  if (formRef.value) formRef.value.resetFields()
  Object.assign(form, {
    id: '',
    ip_address: '',
    type: 'intranet',
    status: 'used',
    hostname: '',
    mac_address: '',
    owner: '',
    bound_instance_name: '',
    environment: '',
    source: 'manual',
    description: ''
  })
}

const getIpStatusClass = (ip) => {
  const statusMap = {
    'available': 'status-available',
    'used': 'status-used',
    'online': 'status-online',
    'reserved': 'status-reserved',
    'deprecated': 'status-deprecated'
  }
  return statusMap[ip.status] || 'status-available'
}

const getIpStatusText = (status) => {
  const textMap = { 'available': '空闲', 'used': '已用', 'online': '在线', 'reserved': '保留', 'deprecated': '废弃' }
  return textMap[status] || '空闲'
}

const getIpTooltip = (ip) => {
  if (ip.hostname) return `${ip.ip_address} - ${ip.hostname}`
  if (ip.bound_instance_name) return `${ip.ip_address} - ${ip.bound_instance_name}`
  return ip.ip_address
}

const getStatusTagType = (status) => {
  const typeMap = { 'available': 'info', 'used': 'success', 'online': 'success', 'reserved': 'warning', 'deprecated': 'danger' }
  return typeMap[status] || 'info'
}

const handleSync = async () => {
  try {
    syncLoading.value = true
    await syncIPAddress()
    ElMessage.success('同步指令已发送')
    setTimeout(fetchSegmentStats, 2000)
  } catch (err) {
    console.error(err)
  } finally {
    syncLoading.value = false
  }
}

onMounted(fetchSegmentStats)
</script>

<style scoped>
.ip-overview-page { padding: 20px; background: #f5f7fa; min-height: 100vh; }

/* 头部布局 */
.card-header {
  display: flex;
  align-items: center;
  gap: 20px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
}

.header-center {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  margin-left: 40px;
}

.selector-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.segment-select {
  width: 240px;
}

.segment-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cidr-text {
  font-family: 'Courier New', monospace;
}

.ip-count {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

.header-actions {
  display: flex;
  gap: 10px;
  margin-left: auto;
}

/* 网段卡片行 */
.segment-cards-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin: 16px 0;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.segment-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 140px;
}

.segment-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64,158,255,0.2);
}

.segment-card.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.card-cidr {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.card-stats {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.card-stats .stat.used {
  color: #f56c6c;
  font-weight: 600;
}

.card-stats .divider {
  color: #c0c4cc;
}

.card-stats .stat.total {
  color: #909399;
}

/* 简单统计卡片 */
.simple-stats-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.simple-stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.simple-stat .label {
  font-size: 12px;
  color: #909399;
}

.simple-stat .value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.simple-stat.used .value { color: #f56c6c; }
.simple-stat.online .value { color: #67c23a; }
.simple-stat.available .value { color: #409eff; }
.simple-stat.reserved .value { color: #e6a23c; }

/* 工具栏 */
.toolbar-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 10px 0;
  flex-wrap: wrap;
  gap: 12px;
}

.legend-group {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot-available { background: #409eff; }
.dot-used { background: #f56c6c; }
.dot-online { background: #67c23a; }
.dot-reserved { background: #e6a23c; }
.dot-deprecated { background: #909399; }

/* 🔥 搜索区域样式 */
.search-area {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 🔥 搜索结果提示 */
.search-result-tips {
  margin-bottom: 12px;
}

/* IP网格 */
.ip-grid-container {
  background: #fff;
  border-radius: 4px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  min-height: 400px;
}

.empty-result {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
}

.ip-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 8px;
}

.ip-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  padding: 4px;
  position: relative;
}

.ip-box:hover {
  transform: scale(1.05);
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.ip-num {
  font-size: 14px;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.ip-status {
  font-size: 10px;
  margin-top: 2px;
}

.ip-hostname {
  font-size: 9px;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 2px;
}

/* 🔥 负责人显示 */
.ip-owner {
  font-size: 9px;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #909399;
  margin-top: 1px;
}

.status-available { background: #ecf5ff; border-color: #a0cfff; color: #409eff; }
.status-used { background: #fdf2f2; border-color: #fab6b6; color: #f56c6c; }
.status-online { background: #f0f9eb; border-color: #b3e19d; color: #67c23a; }
.status-reserved { background: #fdf6ec; border-color: #f5dab1; color: #e6a23c; }
.status-deprecated { background: #f4f4f5; border-color: #d3d4d6; color: #909399; }

/* 抽屉底部 */
.drawer-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.ip-detail {
  padding: 0 4px;
}

/* 响应式 */
@media (max-width: 768px) {
  .toolbar-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .search-area {
    width: 100%;
  }

  .search-area .el-input {
    flex: 1;
  }

  .ip-grid {
    grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
    gap: 4px;
  }

  .ip-box {
    min-height: 50px;
    padding: 2px;
  }

  .ip-num {
    font-size: 12px;
  }
}
</style>
