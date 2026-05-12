<template>
  <el-container class="main-layout">
    <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo" @click="$router.push('/dashboard')">
        <span v-if="!sidebarCollapsed">电力安全监管平台</span>
        <span v-else>⚡</span>
      </div>
      <el-menu
        :default-active="$route.path"
        :collapse="sidebarCollapsed"
        router
        background-color="#001529"
        text-color="#ffffffa6"
        active-text-color="#fff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Monitor /></el-icon>
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/annotation">
          <el-icon><Edit /></el-icon>
          <span>数据标注</span>
        </el-menu-item>
        <el-menu-item index="/training">
          <el-icon><Cpu /></el-icon>
          <span>模型训练</span>
        </el-menu-item>
        <el-menu-item index="/inference">
          <el-icon><View /></el-icon>
          <span>模型推理</span>
        </el-menu-item>
        <el-menu-item index="/drawing-review">
          <el-icon><Document /></el-icon>
          <span>图纸评审</span>
        </el-menu-item>
        <el-menu-item index="/plan-review">
          <el-icon><Files /></el-icon>
          <span>施工方案评审</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="topbar">
        <el-icon class="collapse-btn" @click="store.toggleSidebar()">
          <Fold v-if="!sidebarCollapsed" /><Expand v-else />
        </el-icon>
        <span class="page-title">{{ $route.meta.title }}</span>
        <div class="user-area">
          <span>{{ store.userName }}</span>
        </div>
      </el-header>
      <el-main><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/store'
import { Monitor, Edit, Cpu, View, Document, Files, Fold, Expand } from '@element-plus/icons-vue'

const store = useAppStore()
const sidebarCollapsed = computed(() => store.sidebarCollapsed)
</script>

<style scoped>
.main-layout { height: 100vh; }
.sidebar { background-color: #001529; overflow: hidden; transition: width 0.3s; }
.logo { height: 60px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 16px; font-weight: bold; cursor: pointer; border-bottom: 1px solid #ffffff1a; }
.topbar { display: flex; align-items: center; gap: 12px; background: #fff; border-bottom: 1px solid #e8e8e8; padding: 0 20px; }
.collapse-btn { cursor: pointer; font-size: 20px; }
.page-title { font-size: 16px; font-weight: 500; }
.user-area { margin-left: auto; }
</style>
