<template>
  <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
    <el-form-item label="原密码" prop="oldPassword">
      <el-input v-model="form.oldPassword" type="password" show-password />
    </el-form-item>
    <el-form-item label="新密码" prop="newPassword">
      <el-input v-model="form.newPassword" type="password" show-password />
    </el-form-item>
    <el-form-item label="确认密码" prop="confirmPassword">
      <el-input v-model="form.confirmPassword" type="password" show-password />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="handleSubmit">保存</el-button>
      <el-button @click="handleReset">重置</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import {defineProps, ref} from 'vue'
import {ElMessage} from 'element-plus'
import { updateUserPassword } from '@/api/user' // ✅ Import API function

const props = defineProps({
  user: {
    type: Object,
    default: () => ({}),
    required: true
  }
})

const emit = defineEmits(['update-success'])

const formRef = ref(null)
const form = ref({
  id: -1,
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 自定义确认密码验证规则
const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== form.value.newPassword) {
    callback(new Error('两次输入密码不一致!'))
  } else {
    callback()
  }
}

const rules = ref({
  oldPassword: [
    {required: true, message: '请输入原密码', trigger: 'blur'}
  ],
  newPassword: [
    {required: true, message: '请输入新密码', trigger: 'blur'},
    {min: 6, message: '密码长度不能少于6位', trigger: 'blur'}
  ],
  confirmPassword: [
    {required: true, message: '请确认密码', trigger: 'blur'},
    {validator: validateConfirmPassword, trigger: 'blur'}
  ]
})

// 初始化用户ID
form.value.id = props.user.id

const handleSubmit = () => {
  formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const result = await updateUserPassword(form.value)
        if (result.code === 200) {
          ElMessage.success("密码修改成功，下次登录生效")
          emit('update-success')
          handleReset()
        } else {
          ElMessage.error(data.errorInfo || '修改失败')
        }
      } catch (error) {
        console.error('密码修改失败:', error)
        ElMessage.error('密码修改失败')
      }
    }
  })
}

const handleReset = () => {
  form.value.oldPassword = ''
  form.value.newPassword = ''
  form.value.confirmPassword = ''
  formRef.value?.clearValidate()
}
</script>
