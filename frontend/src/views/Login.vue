<template>
  <div class="login-page">
    <!-- 左侧品牌展示 -->
    <div class="login-left">
      <div class="brand-content">
        <div class="brand-badge">AI POWERED</div>
        <h1>电力作业<br/>AI安全监管平台</h1>
        <p>基于深度学习的电力作业现场智能监控系统，<br/>覆盖图纸评审、方案审查、实时推理全流程</p>
        <div class="feature-list">
          <div class="feat-item">
            <div class="feat-icon"><el-icon><Cpu /></el-icon></div>
            <span>YOLOv8 视觉检测</span>
          </div>
          <div class="feat-item">
            <div class="feat-icon"><el-icon><Document /></el-icon></div>
            <span>图纸与方案AI评审</span>
          </div>
          <div class="feat-item">
            <div class="feat-icon"><el-icon><DataAnalysis /></el-icon></div>
            <span>知识库RAG检索增强</span>
          </div>
        </div>
      </div>
      <div class="brand-bg-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
      </div>
    </div>

    <!-- 右侧登录表单 -->
    <div class="login-right">
      <div class="login-card">
        <div class="card-header">
          <div class="avatar-circle">
            <el-icon :size="28" color="#fff"><UserFilled /></el-icon>
          </div>
          <h2>欢迎回来</h2>
          <p>请登录您的账号以继续</p>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" size="large" class="login-form">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password />
          </el-form-item>
          <div class="form-options">
            <el-checkbox v-model="remember">记住密码</el-checkbox>
            <a href="#">忘记密码？</a>
          </div>
          <el-button type="primary" :loading="loading" class="login-btn" @click="handleLogin">
            登 录
          </el-button>
        </el-form>

        <div class="login-footer">
          <span>测试账号：admin / 任意密码</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/store'
import { User, Lock, Cpu, Document, DataAnalysis } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const store = useAppStore()
const loading = ref(false)
const remember = ref(false)

const form = reactive({ username: 'admin', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const handleLogin = async () => {
  loading.value = true
  await new Promise(r => setTimeout(r, 800))
  store.setToken('demo-token')
  store.setUser({ username: form.username, avatar: '' })
  ElMessage.success({ message: '登录成功，欢迎使用电力安全监管平台', duration: 2000 })
  loading.value = false
  router.push('/dashboard')
}
</script>

<style scoped>
.login-page {
  display: flex;
  height: 100vh;
  width: 100%;
}

/* ── 左侧品牌区 ────────────────────────────────── */
.login-left {
  flex: 1;
  background: linear-gradient(135deg, #0b1a30, #0f2644 40%, #162d5e 70%, #1a3a6e);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}
.brand-content {
  position: relative;
  z-index: 2;
  max-width: 480px;
  padding: 48px;
}
.brand-badge {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 20px;
  background: rgba(0,180,216,.2);
  color: #48e5ff;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  margin-bottom: 28px;
  border: 1px solid rgba(0,180,216,.3);
}
.brand-content h1 {
  font-size: 36px;
  font-weight: 700;
  color: #fff;
  line-height: 1.3;
  margin-bottom: 16px;
  letter-spacing: 1px;
}
.brand-content p {
  color: rgba(255,255,255,.5);
  font-size: 14px;
  line-height: 1.8;
  margin-bottom: 36px;
}
.feature-list { display: flex; flex-direction: column; gap: 14px; }
.feat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  color: rgba(255,255,255,.65);
  font-size: 14px;
}
.feat-icon {
  width: 34px; height: 34px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,.07);
  border-radius: 8px;
  color: #48e5ff;
}

/* 背景装饰 */
.brand-bg-shapes { position: absolute; inset: 0; z-index: 1; pointer-events: none; }
.shape {
  position: absolute;
  border-radius: 50%;
  opacity: .05;
  background: #48e5ff;
}
.shape-1 { width: 500px; height: 500px; top: -150px; right: -100px; }
.shape-2 { width: 300px; height: 300px; bottom: -80px; left: 60px; }
.shape-3 { width: 200px; height: 200px; top: 50%; left: -40px; }

/* ── 右侧表单区 ────────────────────────────────── */
.login-right {
  width: 520px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  padding: 40px;
}
.login-card { width: 100%; max-width: 380px; }
.card-header { text-align: center; margin-bottom: 36px; }
.avatar-circle {
  width: 56px; height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--brand-500), var(--brand-400));
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 16px;
}
.card-header h2 { font-size: 24px; font-weight: 700; color: var(--gray-900); margin-bottom: 6px; }
.card-header p { color: var(--gray-500); font-size: 14px; }

.login-form :deep(.el-input__wrapper) { padding: 10px 14px; }
.login-form :deep(.el-form-item) { margin-bottom: 18px; }

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  font-size: 13px;
}
.form-options a { color: var(--brand-500); text-decoration: none; }

.login-btn {
  width: 100%;
  height: 46px;
  font-size: 16px;
  letter-spacing: 4px;
  font-weight: 600 !important;
}

.login-footer {
  text-align: center;
  margin-top: 32px;
  color: var(--gray-400);
  font-size: 12px;
}

@media (max-width: 768px) {
  .login-left { display: none; }
  .login-right { width: 100%; }
}
</style>
