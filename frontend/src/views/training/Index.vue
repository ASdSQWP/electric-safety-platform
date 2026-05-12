<template>
  <div class="training-page">
    <div class="page-header">
      <h2>模型训练</h2>
      <el-button type="primary" @click="showCreate = true"><el-icon><Plus /></el-icon>创建训练任务</el-button>
    </div>

    <el-card shadow="never" class="content-card">
      <el-tabs v-model="activeTab" class="training-tabs">
        <el-tab-pane label="训练任务" name="jobs">
          <el-table :data="jobs" stripe>
            <el-table-column prop="id" label="任务ID" width="90" />
            <el-table-column prop="model" label="模型" width="110" />
            <el-table-column prop="dataset" label="数据集" min-width="180" />
            <el-table-column prop="status" label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="statusTag(row.status)" effect="dark" round size="small">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="进度" width="200">
              <template #default="{ row }">
                <el-progress :percentage="row.progress" :stroke-width="10" :status="row.status === 'failed' ? 'exception' : undefined"
                  :color="row.status === 'completed' ? '#10b981' : '#3b82f6'" />
              </template>
            </el-table-column>
            <el-table-column label="mAP50" width="100" align="center">
              <template #default="{ row }">
                <span v-if="row.metrics" class="metric-val">{{ row.metrics.mAP50 }}</span>
                <span v-else class="metric-na">-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button v-if="row.status === 'completed'" size="small" type="success">导出模型</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="模型管理" name="models">
          <el-table :data="models" stripe>
            <el-table-column prop="name" label="模型名称" min-width="240" />
            <el-table-column prop="type" label="类型" width="120" />
            <el-table-column prop="mAP50" label="mAP50" width="100" align="center">
              <template #default="{ row }"><span class="metric-val">{{ row.mAP50 }}</span></template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default>
                <el-button size="small" type="primary">推理</el-button>
                <el-button size="small" type="success">导出ONNX</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 创建训练任务弹窗 -->
    <el-dialog v-model="showCreate" title="创建训练任务" width="580px" destroy-on-close>
      <el-form :model="newJob" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="选择模型"><el-select v-model="newJob.model" style="width:100%"><el-option v-for="m in modelOptions" :key="m" :label="m" :value="m" /></el-select></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="选择数据集"><el-select v-model="newJob.dataset" style="width:100%"><el-option v-for="d in datasetOptions" :key="d" :label="d" :value="d" /></el-select></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8"><el-form-item label="Epochs"><el-input-number v-model="newJob.epochs" :min="1" :max="500" style="width:100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="Batch"><el-input-number v-model="newJob.batch" :min="1" :max="64" style="width:100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="Img Size"><el-input-number v-model="newJob.imgSize" :min="320" :max="1280" :step="32" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="GPU设备"><el-select v-model="newJob.gpu" style="width:100%"><el-option label="GPU 0" value="0" /><el-option label="GPU 0,1 (双卡)" value="0,1" /></el-select></el-form-item>
      </el-form>
      <template #footer><el-button @click="showCreate = false">取消</el-button><el-button type="primary" @click="startTraining">开始训练</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'

const activeTab = ref('jobs')
const showCreate = ref(false)
const modelOptions = ['yolov8n', 'yolov8s', 'yolov8m', 'yolov8l', 'yolov8x']
const datasetOptions = ['输电线路缺陷-v3', '绝缘子自爆-2024']
const newJob = ref({ model: 'yolov8s', dataset: '输电线路缺陷-v3', epochs: 100, batch: 16, imgSize: 640, gpu: '0' })

const jobs = ref([
  { id: 'a3f2', model: 'yolov8s', dataset: '输电线路缺陷-v3', status: 'completed', progress: 100, metrics: { mAP50: 0.87 } },
  { id: 'b1d4', model: 'yolov8n', dataset: '绝缘子自爆-2024', status: 'running', progress: 65, metrics: null },
])

const models = ref([
  { name: 'yolov8s-var3-20250512', type: 'YOLOv8s Fine-tuned', mAP50: 0.87 },
  { name: 'yolov8n-insulator-v2', type: 'YOLOv8n Fine-tuned', mAP50: 0.92 },
])

const statusTag = (s) => ({ completed: 'success', running: 'warning', queued: 'info', failed: 'danger' }[s] || 'info')
const statusLabel = (s) => ({ completed: '已完成', running: '运行中', queued: '排队中', failed: '失败' }[s] || s)

const startTraining = () => {
  showCreate.value = false
  jobs.value.unshift({ id: Date.now().toString(36).slice(-4), model: newJob.value.model, dataset: newJob.value.dataset, status: 'queued', progress: 0, metrics: null })
}
</script>

<style scoped>
.content-card { margin-top: 8px; }
.training-tabs :deep(.el-tabs__header) { margin-bottom: 8px; }
.metric-val { font-weight: 700; font-size: 15px; color: #10b981; font-family: var(--font-mono, monospace); }
.metric-na { color: var(--gray-400); }
</style>
