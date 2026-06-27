<template>
  <el-dialog v-model="visible" title="IP详情" width="600px" @close="handleClose">
    <el-descriptions :column="2" border>
      <el-descriptions-item label="IP地址">
        <el-tag size="small">{{ detail.ip_address }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="来源">
        <el-tag :type="getSourceType(detail.source)">{{ getSourceText(detail.source) }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="资源名称">{{ detail.bound_instance_name || '-' }}</el-descriptions-item>
      <el-descriptions-item label="资源ID">
        <span class="text-blue-500">{{ detail.object_id || '-' }}</span>
      </el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="getStatusType(detail.status)">
          {{ getStatusText(detail.status) }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="MAC">{{ detail.mac_address || '-' }}</el-descriptions-item>
      <el-descriptions-item label="环境">{{ detail.environment || '-' }}</el-descriptions-item>
      <el-descriptions-item label="负责人">{{ detail.owner || '-' }}</el-descriptions-item>
       <el-descriptions-item label="网段/掩码">{{ detail.network_segment_info ? detail.network_segment_info.segment : (detail.mask || '-') }}</el-descriptions-item>
      <el-descriptions-item label="备注" :span="2">
        {{ detail.description || '-' }}
      </el-descriptions-item>
    </el-descriptions>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: Boolean,
  detail: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const handleClose = () => {
  emit('update:modelValue', false)
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

const getSourceType = (source) => {
   return source === 'manual' ? undefined : 'info'
}

const getSourceText = (source) => {
    const map = {
        manual: '手动',
        aliyun: '阿里云',
        datacenter: '本地机房'
    }
    return map[source] || source
}
</script>

<style scoped>
.text-blue-500 {
    color: #409EFF;
    cursor: pointer;
}
</style>
