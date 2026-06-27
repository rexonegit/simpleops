<template>
  <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
    <el-form-item label="用户名">
      <el-input v-model="form.username" disabled />
    </el-form-item>
    <el-form-item label="手机号码" prop="phone">  <!-- ✅ 修复：phonenumber → phone -->
      <el-input v-model="form.phone" maxlength="11"/>
    </el-form-item>
    <el-form-item label="邮箱" prop="email">
      <el-input v-model="form.email" maxlength="50"/>
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="handleSubmit">保存</el-button>
      <el-button @click="handleReset">重置</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { defineProps, defineEmits, watch, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { updateUserInfo } from '@/api/user' // ✅ Import API function

const props = defineProps({
  user: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update-success'])

const formRef = ref(null)

// ✅ 修复：使用reactive创建表单对象
const form = reactive({
  id: -1,
  username: '',
  phone: '',  // ✅ 匹配接口字段
  email: '',
})

// ✅ 修复：监听props，正确赋值
watch(() => props.user, (newUser) => {
  if (newUser && Object.keys(newUser).length > 0) {
    form.id = newUser.id
    form.username = newUser.username
    form.phone = newUser.phone || ''  // ✅ 匹配phone字段
    form.email = newUser.email || ''
  }
}, { immediate: true, deep: true })

const rules = {
  phone: [  // ✅ 修复：phonenumber → phone
    { required: true, message: "手机号码不能为空", trigger: "blur" },
    {
      pattern: /^1[3|4|5|6|7|8|9][0-9]\d{8}$/,
      message: "请输入正确的手机号码",
      trigger: "blur"
    }
  ],
  email: [
    { required: true, message: "邮箱地址不能为空", trigger: "blur" },
    { type: "email", message: "请输入正确的邮箱地址", trigger: ["blur", "change"] }
  ]
}

const handleSubmit = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      // ✅ 简化提交逻辑，直接发送form
      const result = await updateUserInfo(form)
      if (result.code === 200) {
        ElMessage.success("保存成功！")
        emit('update-success', form)
      } else {
        ElMessage.error(result.data.errorInfo || '保存失败')
      }
    } catch (error) {
      console.error('保存失败:', error)
      ElMessage.error('保存失败')
    }
  })
}

const handleReset = () => {
  if (props.user) {
    form.phone = props.user.phone || ''
    form.email = props.user.email || ''
  }
  formRef.value?.clearValidate()
}
</script>
