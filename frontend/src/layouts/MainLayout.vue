<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside :width="collapsed ? '72px' : '240px'" class="sidebar">
      <div class="logo-area" @click="$router.push('/dashboard')">
        <div class="logo-icon">⚡</div>
        <transition name="fade">
          <div v-if="!collapsed" class="logo-text">
            <div class="logo-title">电力安全监管</div>
            <div class="logo-sub">AI SUPERVISION</div>
          </div>
        </transition>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        router
        background-color="transparent"
        text-color="rgba(255,255,255,.6)"
        active-text-color="#fff"
        class="side-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
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
          <el-icon><VideoCamera /></el-icon>
          <span>模型推理</span>
        </el-menu-item>
        <el-menu-item index="/drawing-review">
          <el-icon><Document /></el-icon>
          <span>图纸评审</span>
        </el-menu-item>
        <el-menu-item index="/plan-review">
          <el-icon><Notebook /></el-icon>
          <span>方案评审</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <el-icon class="collapse-trigger" @click="store.toggleSidebar()">
          <DArrowLeft v-if="!collapsed" /><DArrowRight v-else />
        </el-icon>
      </div>
    </el-aside>

    <!-- 右侧区域 -->
    <el-container>
      <el-header class="topbar">
        <div class="breadcrumb">
          <span class="bc-root">工作区</span>
          <el-icon class="bc-sep"><ArrowRight /></el-icon>
          <span class="bc-current">{{ $route.meta.title }}</span>
        </div>
        <div class="header-right">
          <el-badge :value="3" class="notice-badge">
            <el-button circle :icon="Bell" />
          </el-badge>
          <el-dropdown trigger="click">
            <div class="user-dropdown">
              <el-avatar :size="34" icon="UserFilled" />
              <span class="user-name">{{ store.userName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item><el-icon><User /></el-icon>个人设置</el-dropdown-item>
                <el-dropdown-item divided @click="store.logout();$router.push('/login')">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-content"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/store'
import {
  DataBoard, Edit, Cpu, VideoCamera, Document, Notebook,
  DArrowLeft, DArrowRight, ArrowRight, ArrowDown,
  Bell, User, SwitchButton
} from '@element-plus/icons-vue'

const store = useAppStore()
const route = useRoute()
const collapsed = computed(() => store.sidebarCollapsed)
const activeMenu = computed(() => route.path)
</script>

<style scoped>
.main-layout { height: 100vh; }

/* ── 侧边栏 ───────────────────────────────────── */
.sidebar {
  background: linear-gradient(180deg, #0b1a30 0%, #0f2644 50%, #112b4f 100%);
  display: flex;
  flex-direction: column;
  transition: width .25s cubic-bezier(.4,0,.2,1);
  overflow: hidden;
  border-right: 1px solid rgba(255,255,255,.06);
}

.logo-area {
  height: 68px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,.08);
  flex-shrink: 0;
}
.logo-icon {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #00b4d8, #0096c7);
  border-radius: 10px;
  font-size: 18px;
  flex-shrink: 0;
}
.logo-text { overflow: hidden; white-space: nowrap; }
.logo-title { color: #fff; font-size: 15px; font-weight: 700; letter-spacing: .5px; }
.logo-sub { color: rgba(255,255,255,.4); font-size: 10px; letter-spacing: 2px; font-weight: 500; }

/* 菜单 */
.side-menu {
  flex: 1;
  padding: 12px 0;
  border-right: none !important;
}
.side-menu :deep(.el-menu-item) {
  margin: 4px 12px;
  border-radius: 8px;
  height: 44px;
  line-height: 44px;
  transition: all .2s;
}
.side-menu :deep(.el-menu-item:hover) {
  background: rgba(255,255,255,.08) !important;
  color: #fff !important;
}
.side-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(0,180,216,.25), rgba(0,150,199,.15)) !important;
  color: #48e5ff !important;
  box-shadow: inset 3px 0 0 #00b4d8;
}
.side-menu :deep(.el-menu-item .el-icon) { font-size: 18px; }

/* 底部折叠按钮 */
.sidebar-footer {
  padding: 12px;
  border-top: 1px solid rgba(255,255,255,.08);
  flex-shrink: 0;
}
.collapse-trigger {
  width: 100%;
  padding: 10px;
  color: rgba(255,255,255,.4);
  font-size: 16px;
  cursor: pointer;
  border-radius: 8px;
  transition: all .2s;
  display: flex; justify-content: center;
}
.collapse-trigger:hover { color: #fff; background: rgba(255,255,255,.08); }

/* ── 顶栏 ─────────────────────────────────────── */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid var(--gray-200);
  padding: 0 24px;
  flex-shrink: 0;
  z-index: 10;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--gray-500);
}
.bc-sep { font-size: 12px; }
.bc-current { color: var(--gray-900); font-weight: 600; font-size: 14px; }

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.notice-badge :deep(.el-badge__content) { font-size: 10px; }

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background .2s;
}
.user-dropdown:hover { background: var(--gray-100); }
.user-name { font-size: 13px; font-weight: 500; color: var(--gray-700); }

/* ── 内容区 ───────────────────────────────────── */
.main-content {
  background: var(--gray-50);
  padding: 24px;
  overflow-y: auto;
  height: calc(100vh - 56px);
}

/* 过渡 */
.fade-enter-active, .fade-leave-active { transition: opacity .2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
