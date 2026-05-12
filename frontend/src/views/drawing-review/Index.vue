<template>
  <div class="drawing-review-page">
    <div class="page-header">
      <h2>图纸评审</h2>
      <div class="header-actions">
        <el-input v-model="search" placeholder="搜索图纸..." prefix-icon="Search" clearable class="search-input" />
        <el-button type="primary" @click="showUpload = true"><el-icon><Upload /></el-icon>上传图纸</el-button>
      </div>
    </div>

    <el-card shadow="never" class="table-card">
      <el-table :data="reviews" stripe>
        <el-table-column prop="drawingId" label="图纸编号" width="150">
          <template #default="{ row }"><span class="id-tag">{{ row.drawingId }}</span></template>
        </el-table-column>
        <el-table-column prop="name" label="图纸名称" min-width="200">
          <template #default="{ row }">
            <div class="name-cell">
              <el-icon :size="18" color="#f59e0b"><Document /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="pages" label="页数" width="70" align="center" />
        <el-table-column label="问题数" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.issueCount > 0 ? 'danger' : 'success'" effect="dark" round size="small">
              {{ row.issueCount > 0 ? `${row.issueCount}个问题` : '无问题' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" effect="light" round size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="viewDetail(row)">查看详情</el-button>
            <el-button size="small" type="warning" @click="generateReport(row)">生成报告</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 上传弹窗 -->
    <el-dialog v-model="showUpload" title="上传工程图纸" width="520px" destroy-on-close>
      <el-upload drag :auto-upload="false" accept=".pdf,.dwg,.png,.jpg" class="upload-zone">
        <el-icon :size="48" color="#ccc"><Upload /></el-icon>
        <p>支持 PDF / DWG / PNG / JPG 格式</p>
        <small>最大文件大小 500MB</small>
      </el-upload>
      <template #footer>
        <el-button @click="showUpload = false">取消</el-button>
        <el-button type="primary" @click="showUpload = false; startAnalysis()">开始分析</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="showDetail" title="评审详情" width="800px" destroy-on-close>
      <template v-if="currentReview">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="图纸编号" :span="1">{{ currentReview.drawingId }}</el-descriptions-item>
          <el-descriptions-item label="页数" :span="1">{{ currentReview.pages }} 页</el-descriptions-item>
          <el-descriptions-item label="图纸名称" :span="2">{{ currentReview.name }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:20px 0 12px;font-size:15px;color:var(--gray-800)">发现的问题</h4>
        <el-table :data="currentReview.issues" stripe size="small" v-if="currentReview.issues.length">
          <el-table-column prop="severity" label="严重程度" width="90" align="center">
            <template #default="{ row }">
              <el-tag :type="severityTag(row.severity)" effect="dark" size="small">{{ row.severity }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="category" label="类别" width="130" />
          <el-table-column prop="description" label="问题描述" min-width="300" />
        </el-table>
        <el-empty v-else description="未发现问题" :image-size="60" />
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Upload, Search, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const search = ref('')
const showUpload = ref(false)
const showDetail = ref(false)
const currentReview = ref(null)

const reviews = ref([
  { drawingId: 'B2025-0042', name: '220kV铁塔基础施工图', pages: 12, issueCount: 3, status: '已完成', issues: [
    { severity: '严重', category: '尺寸缺失', description: 'A-A剖面缺少地脚螺栓间距标注' },
    { severity: '一般', category: '符号错误', description: '焊缝符号不符合GB/T 324规范' },
    { severity: '一般', category: '材料问题', description: '基础混凝土强度等级未在图中标明' },
  ]},
  { drawingId: 'B2025-0041', name: '110kV变电站平面布置图', pages: 8, issueCount: 0, status: '已完成', issues: [] },
  { drawingId: 'B2025-0040', name: '输电线路路径图', pages: 5, issueCount: 1, status: '进行中', issues: [] },
])

const statusTag = (s) => ({ '已完成': 'success', '进行中': 'warning', '分析中': 'info' }[s] || 'info')
const severityTag = (s) => ({ '一般': 'info', '严重': 'danger', '危急': 'danger' }[s] || 'info')

const viewDetail = (row) => { currentReview.value = row; showDetail.value = true }
const generateReport = (row) => { ElMessage.success({ message: `报告生成中: ${row.drawingId}`, duration: 2000 }) }
const startAnalysis = () => {
  ElMessage.info('图纸分析任务已提交')
  reviews.value.unshift({ drawingId: 'B2025-0043', name: '新上传图纸', pages: 1, issueCount: 0, status: '分析中', issues: [] })
}
</script>

<style scoped>
.header-actions { display: flex; gap: 12px; }
.search-input { width: 220px; }
.table-card { margin-top: 8px; }
.id-tag { font-family: monospace; font-size: 13px; color: var(--brand-500); font-weight: 500; }
.name-cell { display: flex; align-items: center; gap: 8px; font-weight: 500; }
.upload-zone :deep(.el-upload-dragger) { padding: 32px; }
.upload-zone p { color: var(--gray-500); margin-top: 12px; }
.upload-zone small { color: var(--gray-400); font-size: 12px; }
</style>
