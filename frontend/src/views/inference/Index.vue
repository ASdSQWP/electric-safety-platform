<template>
  <div class="inference-page">
    <div class="page-header"><h2>模型推理</h2></div>

    <el-row :gutter="16">
      <el-col :span="8">
        <el-card>
          <template #header>上传媒体</template>
          <el-upload drag :auto-upload="false" @change="onFileChange" accept="image/*,video/*">
            <el-icon :size="48"><Upload /></el-icon>
            <p>点击或拖拽上传图片/视频</p>
          </el-upload>
        </el-card>
        <el-card style="margin-top: 12px">
          <template #header>推理配置</template>
          <el-form label-width="80px">
            <el-form-item label="模型"><el-select v-model="config.model" style="width:100%"><el-option v-for="m in models" :key="m" :label="m" :value="m" /></el-select></el-form-item>
            <el-form-item label="置信度"><el-slider v-model="config.conf" :min="0.1" :max="0.9" :step="0.05" show-input /></el-form-item>
            <el-form-item label="IoU"><el-slider v-model="config.iou" :min="0.1" :max="0.9" :step="0.05" show-input /></el-form-item>
            <el-form-item><el-button type="primary" style="width:100%" @click="runInference">开始推理</el-button></el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card>
          <template #header>推理结果</template>
          <div class="result-area" v-if="!result">
            <el-empty description="请上传文件并点击推理" />
          </div>
          <div class="result-area" v-else>
            <el-alert :title="`检测到 ${result.detections.length} 个目标 (${result.inference_time_ms}ms)`" type="success" closable />
            <div style="margin-top: 12px">
              <el-image v-if="previewUrl" :src="previewUrl" style="max-width: 100%; max-height: 500px" fit="contain" />
            </div>
            <el-table :data="result.detections" stripe style="margin-top: 12px" max-height="300">
              <el-table-column prop="class_name" label="类别" width="120" />
              <el-table-column prop="confidence" label="置信度" width="100">
                <template #default="{ row }">{{ (row.confidence * 100).toFixed(1) }}%</template>
              </el-table-column>
              <el-table-column prop="bbox" label="BBox" />
            </el-table>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import { ai } from '@/api'

const models = ['yolov8n', 'yolov8s', 'yolov8m']
const config = ref({ model: 'yolov8s', conf: 0.25, iou: 0.45 })
const previewUrl = ref('')
const result = ref(null)

const onFileChange = (file) => {
  previewUrl.value = URL.createObjectURL(file.raw)
}

const runInference = async () => {
  // TODO: 调用后端推理接口
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
.page-header { margin-bottom: 16px; }
.result-area { min-height: 300px; }
</style>
