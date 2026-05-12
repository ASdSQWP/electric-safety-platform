<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in statsCards" :key="card.title">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" :style="{ background: card.color }"><el-icon :size="28"><component :is="card.icon" /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ card.value }}</div>
            <div class="stat-title">{{ card.title }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card>
          <template #header>最近活动</template>
          <el-timeline>
            <el-timeline-item timestamp="2025-05-12 14:30" placement="top">训练任务 #a3f2 完成 — YOLOv8s mAP50=0.87</el-timeline-item>
            <el-timeline-item timestamp="2025-05-12 10:15" placement="top">数据集「输电线路缺陷v3」审核通过，含1,280张照片</el-timeline-item>
            <el-timeline-item timestamp="2025-05-11 16:00" placement="top">图纸评审 #B2025-0042 已完成，发现3处问题</el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>快捷入口</template>
          <el-space direction="vertical" :size="12" style="width: 100%">
            <el-button type="primary" style="width: 100%" @click="$router.push('/annotation')">新建标注任务</el-button>
            <el-button style="width: 100%" @click="$router.push('/training')">启动模型训练</el-button>
            <el-button style="width: 100%" @click="$router.push('/drawing-review')">上传图纸评审</el-button>
            <el-button style="width: 100%" @click="$router.push('/plan-review')">上传施工方案</el-button>
          </el-space>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { PictureFilled, Cpu, Document, DataAnalysis } from '@element-plus/icons-vue'

const statsCards = [
  { title: '数据集', value: 12, icon: PictureFilled, color: '#409eff' },
  { title: '训练模型', value: 5, icon: Cpu, color: '#67c23a' },
  { title: '图纸评审', value: 42, icon: Document, color: '#e6a23c' },
  { title: '方案评审', value: 18, icon: DataAnalysis, color: '#f56c6c' },
]
</script>

<style scoped>
.stat-card { display: flex; align-items: center; gap: 16px; cursor: pointer; }
.stat-icon { width: 56px; height: 56px; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #fff; }
.stat-value { font-size: 24px; font-weight: bold; }
.stat-title { font-size: 13px; color: #999; }
</style>
