<template>
  <div class="login-page">
    <el-card class="login-box">
      <h2 style="text-align: center; margin-bottom: 24px">电力安全监管平台</h2>
      <el-form :model="form" label-width="0">
        <el-form-item><el-input v-model="form.username" placeholder="用户名" prefix-icon="User" /></el-form-item>
        <el-form-item><el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" show-password /></el-form-item>
        <el-form-item><el-button type="primary" style="width: 100%" @click="handleLogin">登 录</el-button></el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const form = reactive({ username: 'admin', password: '' })

const handleLogin = async () => {
  // TODO: 对接后端认证
  localStorage.setItem('token', 'demo-token')
  ElMessage.success('登录成功')
  router.push('/dashboard')
}
</script>

<style scoped>
.login-page { height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #1e3c72, #2a5298); }
.login-box { width: 400px; }
</style>
