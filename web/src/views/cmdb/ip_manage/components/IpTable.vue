<template>
  <el-table :data="data" v-loading="loading" style="width: 100%" border stripe>
    <el-table-column prop="ip_address" label="IP地址" width="160" sortable :sort-method="sortByIP"d>
       <template #default="{ row }">
          <span class="font-bold text-blue-500 cursor-pointer" @click="$emit('detail', row)">{{ row.ip_address }}</span>
          <el-tag v-if="row.is_gateway" size="small" type="danger" effect="plain" class="ml-2">GW</el-tag>
       </template>
    </el-table-column>
    <el-table-column prop="status" label="状态" width="100">
      <template #default="{ row }">
        <el-tag :type="getStatusType(row.status)">
          {{ getStatusText(row.status) }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="hostname" label="主机名/资源" min-width="180">
      <template #default="{ row }">
        <div v-if="row.hostname">{{ row.hostname }}</div>
        <div v-if="row.bound_instance_name" class="text-xs text-gray-400">
          <el-icon><Link /></el-icon> {{ row.bound_instance_name }}
        </div>
      </template>
    </el-table-column>
    <el-table-column prop="mac_address" label="MAC地址" width="150" />
    <el-table-column prop="environment" label="环境" width="100">
       <template #default="{ row }">
          <el-tag v-if="row.environment" size="small" effect="plain">{{ row.environment }}</el-tag>
       </template>
    </el-table-column>
    <el-table-column prop="owner" label="负责人" width="100" />
    <el-table-column prop="source" label="来源" width="100">
      <template #default="{ row }">
        <el-tag :type="row.source === 'manual' ? undefined : 'info'" size="small">
          {{ row.source === 'aliyun' ? '阿里云' : (row.source === 'datacenter' ? '机房' : '手动') }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="description" label="备注" min-width="150" show-overflow-tooltip />
    <el-table-column label="操作" width="150" fixed="right">
      <template #default="{ row }">
        <el-button link type="primary" size="small" @click="$emit('edit', row)">编辑</el-button>
        <el-button link type="danger" size="small" @click="$emit('delete', row)">删除</el-button>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
import { Link } from '@element-plus/icons-vue'

defineProps({
  data: {
    type: Array,
    default: () => []
  },
  loading: Boolean
})

defineEmits(['edit', 'delete', 'detail'])

// IP 地址排序函数
const sortByIP = (a, b) => {
  const ipToNumber = (ip) => {
    return ip.split('.').map(Number)
  }
  const aParts = ipToNumber(a.ip_address)
  const bParts = ipToNumber(b.ip_address)

  for (let i = 0; i < 4; i++) {
    if (aParts[i] !== bParts[i]) {
      return aParts[i] - bParts[i]
    }
  }
  return 0
}

const getStatusType = (status) => {
  const map = {
    used: 'success',
    available: 'info',
    reserved: 'warning',
    deprecated: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    used: '使用中',
    available: '空闲',
    reserved: '保留',
    deprecated: '废弃'
  }
  return map[status] || status
}
</script>

<style scoped>
.font-bold {
  font-weight: 600;
}
.ml-2 {
  margin-left: 0.5rem;
}
.text-xs {
  font-size: 12px;
}
.text-gray-400 {
  color: #9ca3af;
}
</style>
