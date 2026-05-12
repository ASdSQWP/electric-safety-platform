<template>
  <div class="drawing-review-page">
    <div class="page-header">
      <h2>图纸评审</h2>
      <el-button type="primary" @click="showUpload = true">上传图纸</el-button>
    </div>

    <el-table :data="reviews" stripe>
      <el-table-column prop="drawingId" label="图纸编号" width="150" />
      <el-table-column prop="name" label="图纸名称" />
      <el-table-column prop="pages" label="页数" width="80" />
      <el-table-column prop="issueCount" label="问题数" width="100">
        <template #default="{ row }">
          <el-tag :type="row.issueCount > 0 ? 'danger' : 'success'">{{ row.issueCount }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }"><el-tag>{{ row.status }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="250">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">查看详情</el-button>
          <el-button size="small" type="warning" @click="generateReport(row)">生成报告</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showUpload" title="上传工程图纸" width="500px">
      <el-upload drag :auto-upload="false" accept=".pdf,.dwg,.png,.jpg">
        <el-icon :size="48"><Upload /></el-icon>
        <p>支持 PDF / DWG / PNG / JPG 格式</p>
      </el-upload>
      <template #footer><el-button @click="showUpload = false">取消</el-button><el-button type="primary" @click="showUpload = false; startAnalysis()">开始分析</el-button></template>
    </el-dialog>

    <el-dialog v-model="showDetail" title="评审详情" width="800px">
      <div v-if="currentReview">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="图纸编号">{{ currentReview.drawingId }}</el-descriptions-item>
          <el-descriptions-item label="页数">{{ currentReview.pages }}</el-descriptions-item>
        </el-descriptions>
        <el-table :data="currentReview.issues" stripe style="margin-top: 12px">
          <el-table-column prop="severity" label="严重程度" width="100">
            <template #default="{ row }"><el-tag :type="severityTag(row.severity)">{{ row.severity }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="category" label="类别" width="150" />
          <el-table-column prop="description" label="问题描述" />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Upload } from '@element-plus/icons-vue'

const showUpload = ref(false)
const showDetail = ref(false)
const currentReview = ref(null)

const reviews = ref([
  { drawingId: 'B2025-0042', name: '220kV铁塔基础施工图', pages: 12, issueCount: 3, status: '已完成', issues: [
    { severity: '严重', category: '尺寸缺失', description: 'A-A剖面缺少地脚螺栓间距标注' },
    { severity: '一般', category: '符号错误', description: '焊缝符号不符合GB/T 324规范' },
  ]},
  { drawingId: 'B2025-0041', name: '110kV变电站平面布置图', pages: 8, issueCount: 0, status: '已完成', issues: [] },
  { drawingId: 'B2025-0040', name: '输电线路路径图', pages: 5, issueCount: 1, status: '进行中', issues: [] },
])

const severityTag = (s) => ({ '一般': 'info', '严重': 'warning', '危急': 'danger' }[s] || 'info')

const viewDetail = (row) => { currentReview.value = row; showDetail.value = true }
const generateReport = (row) => { ElMessage.success(`报告生成中: ${row.drawingId}`) }
const startAnalysis = () => { reviews.value.unshift({ drawingId: 'B2025-0043', name: '新上传图纸', pages: 1, issueCount: 0, status: '分析中', issues: [] }) }
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
