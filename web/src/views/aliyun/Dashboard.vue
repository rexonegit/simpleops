<template>
  <div class="monitor-dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="card-header">
            <el-icon><Warning /></el-icon>
            <span>告警总数</span>
          </div>
          <div class="card-body">
            <div class="display-4">{{ stats.total_alerts }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="card-header">
            <el-icon><CircleCheck /></el-icon>
            <span>已解决告警</span>
          </div>
          <div class="card-body">
            <div class="display-4">{{ stats.resolved_alerts }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="card-header">
            <el-icon><Monitor /></el-icon>
            <span>监控主机</span>
          </div>
          <div class="card-body">
            <div class="display-4">{{ stats.total_hosts }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="card-header">
            <el-icon><Cloudy /></el-icon>
            <span>云账号</span>
          </div>
          <div class="card-body">
            <div class="display-4">{{ stats.total_accounts }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 简单的占位图表，实际需要引入 ECharts 或类似库 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="chart-header">
              <span>告警类型分布 (示例)</span>
            </div>
          </template>
          <div class="chart-container">
            <div v-for="item in alertTypeData" :key="item.name" style="margin-bottom: 10px;">
              <span>{{ item.name }}: </span>
              <el-progress :percentage="item.value" :format="() => item.value" />
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="chart-header">
              <span>告警级别分布 (示例)</span>
            </div>
          </template>
          <div class="chart-container">
             <div v-for="item in alertLevelData" :key="item.name" style="margin-bottom: 10px;">
              <span>{{ item.name }}: </span>
              <el-progress :percentage="item.value" :status="getLevelStatus(item.name)" :format="() => item.value" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="clearfix">
              <span>最近告警</span>
              <el-button style="float: right; padding: 3px 0" type="primary" link @click="goToAlerts">查看更多</el-button>
            </div>
          </template>
          <el-table :data="recentAlerts" style="width: 100%" height="250" border stripe>
            <el-table-column prop="hostname" label="主机名" width="150" />
            <el-table-column prop="alert_name" label="告警名称" />
            <el-table-column prop="alert_level" label="级别" width="80">
              <template #default="{ row }">
                <el-tag :type="getAlertLevelTag(row.alert_level)" size="small">
                  {{ row.alert_level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="start_time" label="开始时间" width="180" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === '已解决' ? 'success' : 'danger'" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Warning, CircleCheck, Monitor, Cloudy } from '@element-plus/icons-vue'
import {
  getDashboardStats,
  getAlertTypeDistribution,
  getAlertLevelDistribution,
  getRecentAlerts
} from '@/api/auto/monitor'

const router = useRouter()

const stats = ref({
  total_alerts: 0,
  resolved_alerts: 0,
  total_hosts: 0,
  total_accounts: 0
})

const alertTypeData = ref([])
const alertLevelData = ref([])
const recentAlerts = ref([])

const fetchDashboardData = async () => {
  try {
    const [statsRes, typeRes, levelRes, alertsRes] = await Promise.all([
      getDashboardStats(),
      getAlertTypeDistribution(),
      getAlertLevelDistribution(),
      getRecentAlerts()
    ])

    stats.value = statsRes.data || statsRes
    alertTypeData.value = typeRes.data || typeRes
    alertLevelData.value = levelRes.data || levelRes
    recentAlerts.value = (alertsRes.data || alertsRes).slice(0, 5)
  } catch (error) {
    console.error('获取仪表盘数据失败:', error)
    // Mock data on failure for display
    // stats.value = { total_alerts: 128, resolved_alerts: 98, total_hosts: 56, total_accounts: 3 }
  }
}

const getAlertLevelTag = (level) => {
  const map = { 'P1': 'danger', 'P2': 'warning', 'P3': 'primary' }
  return map[level] || 'info'
}

const getLevelStatus = (name) => {
  if (name === 'P1') return 'exception'
  if (name === 'P2') return 'warning'
  return 'success'
}

const goToAlerts = () => {
  router.push({ name: 'RealTimeAlerts' }) // Ensure this route name exists
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<style scoped>
.monitor-dashboard { padding: 20px; background-color: #f5f7fa; min-height: calc(100vh - 84px); }
.stat-card { margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1); transition: all 0.3s; }
.stat-card:hover { transform: translateY(-5px); }
.card-header { display: flex; align-items: center; font-size: 16px; font-weight: bold; color: #606266; }
.card-header .el-icon { margin-right: 8px; font-size: 20px; }
.card-body { padding: 15px 0; text-align: center; }
.display-4 { font-size: 28px; font-weight: bold; color: #409EFF; }
.chart-row { margin-bottom: 20px; }
.chart-header { font-weight: bold; color: #606266; }
.chart-container { min-height: 200px; padding: 20px; }
.clearfix:after { content: ""; display: table; clear: both; }
</style>
