<template>
  <div class="inference-page">
    <div class="page-header"><h2>模型推理</h2></div>

    <el-row :gutter="20">
      <!-- 左侧配置 -->
      <el-col :span="8">
        <el-card shadow="never">
          <template #header><div class="card-title"><el-icon><Upload /></el-icon>上传媒体</div></template>
          <el-upload drag :auto-upload="false" @change="onFileChange" accept="image/*,video/*" class="inference-upload">
            <div v-if="!previewUrl" class="upload-placeholder">
              <el-icon :size="52" color="#d1d5db"><Picture /></el-icon>
              <p>点击或拖拽上传图片/视频</p>
            </div>
            <el-image v-else :src="previewUrl" fit="contain" class="upload-preview" />
          </el-upload>
        </el-card>

        <el-card shadow="never" style="margin-top: 16px">
          <template #header><div class="card-title"><el-icon><Setting /></el-icon>推理配置</div></template>
          <el-form label-width="70px" size="default">
            <el-form-item label="模型"><el-select v-model="config.model" style="width:100%"><el-option v-for="m in models" :key="m" :label="m" :value="m" /></el-select></el-form-item>
            <el-form-item label="置信度">
              <el-slider v-model="config.conf" :min="0.1" :max="0.9" :step="0.05" :marks="{0.25:'0.25',0.5:'0.5',0.75:'0.75'}" show-input />
            </el-form-item>
            <el-form-item label="IoU阈值">
              <el-slider v-model="config.iou" :min="0.1" :max="0.9" :step="0.05" show-input />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" size="large" style="width:100%" :icon="VideoCamera" @click="runInference" :disabled="!previewUrl">
                开始推理
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧结果 -->
      <el-col :span="16">
        <el-card shadow="never" class="result-card">
          <template #header>
            <div class="card-title">
              <el-icon><DataAnalysis /></el-icon>推理结果
              <el-tag v-if="result" size="small" type="success" effect="light" style="margin-left:8px">
                {{ result.detections.length }}个目标
              </el-tag>
            </div>
          </template>

          <div class="result-area" v-if="!result">
            <el-empty description="请上传文件并点击推理">
              <template #image><el-icon :size="64" color="#d1d5db"><Picture /></el-icon></template>
            </el-empty>
          </div>

          <div class="result-area" v-else>
            <el-alert :title="`检测到 ${result.detections.length} 个目标 · 耗时 ${result.inference_time_ms}ms`" type="success" :closable="false" />
            <div class="result-preview">
              <el-image v-if="previewUrl" :src="previewUrl" fit="contain" class="result-image" />
            </div>
            <el-table :data="result.detections" stripe size="small">
              <el-table-column prop="class_name" label="类别" width="140">
                <template #default="{ row }">
                  <el-tag size="small" effect="dark" round>{{ row.class_name }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="confidence" label="置信度" width="120" align="center">
                <template #default="{ row }">
                  <el-progress :percentage="Math.round(row.confidence*100)" :stroke-width="8" :color="row.confidence > 0.7 ? '#10b981' : '#f59e0b'" />
                </template>
              </el-table-column>
              <el-table-column prop="bbox" label="边界框 (归一化)">
                <template #default="{ row }"><code class="bbox-code">{{ row.bbox.join(', ') }}</code></template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Upload, Picture, Setting, VideoCamera, DataAnalysis } from '@element-plus/icons-vue'

const models = ['yolov8n', 'yolov8s', 'yolov8m']
const config = ref({ model: 'yolov8s', conf: 0.25, iou: 0.45 })
const previewUrl = ref('')
const result = ref(null)

const onFileChange = (file) => {
  previewUrl.value = URL.createObjectURL(file.raw)
}

const runInference = async () => {
  result.value = {
    detections: [
      { class_name: '绝缘子', confidence: 0.92, bbox: [0.12, 0.34, 0.28, 0.56] },
      { class_name: '导线', confidence: 0.85, bbox: [0.55, 0.20, 0.88, 0.45] },
    ],
    inference_time_ms: 45.2,
  }
}
</script>

<style scoped>
.card-title { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600; color: var(--gray-800); }
.inference-upload :deep(.el-upload-dragger) { padding: 16px; min-height: 150px; }
.upload-placeholder p { color: var(--gray-400); font-size: 14px; margin-top: 12px; }
.upload-preview { max-height: 200px; }
.result-card { height: 100%; }
.result-area { min-height: 350px; }
.result-preview { margin: 16px 0; text-align: center; background: var(--gray-100); border-radius: var(--radius); padding: 12px; }
.result-image { max-height: 350px; }
.bbox-code { font-size: 12px; color: var(--gray-600); background: var(--gray-100); padding: 2px 8px; border-radius: 4px; }
</style>
