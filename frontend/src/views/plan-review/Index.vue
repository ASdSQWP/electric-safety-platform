<template>
  <div class="plan-review-page">
    <div class="page-header">
      <h2>施工方案评审</h2>
      <el-button type="primary" @click="showUpload = true">上传施工方案</el-button>
    </div>

    <el-table :data="reviews" stripe>
      <el-table-column prop="docId" label="文档编号" width="150" />
      <el-table-column prop="name" label="方案名称" />
      <el-table-column prop="type" label="类型" width="120" />
      <el-table-column prop="opinionCount" label="审查意见" width="120">
        <template #default="{ row }">
          <el-tag :type="row.opinionCount > 0 ? 'warning' : 'success'">{{ row.opinionCount }}条</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }"><el-tag>{{ row.status }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">查看详情</el-button>
          <el-button size="small" type="warning">导出意见</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showUpload" title="上传施工方案" width="500px">
      <el-upload drag :auto-upload="false" accept=".pdf,.docx,.doc">
        <el-icon :size="48"><Upload /></el-icon>
        <p>支持 PDF / DOCX 格式</p>
      </el-upload>
      <template #footer><el-button @click="showUpload = false">取消</el-button><el-button type="primary" @click="showUpload = false; startReview()">开始审查</el-button></template>
    </el-dialog>

    <el-dialog v-model="showDetail" title="审查详情" width="800px">
      <div v-if="currentReview">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="文档编号">{{ currentReview.docId }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ currentReview.status }}</el-descriptions-item>
        </el-descriptions>
        <el-table :data="currentReview.opinions" stripe style="margin-top: 12px">
          <el-table-column prop="clause_ref" label="引用规范" width="180" />
          <el-table-column prop="severity" label="严重程度" width="100">
            <template #default="{ row }"><el-tag :type="row.severity === '严重' ? 'warning' : 'info'">{{ row.severity }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="comment" label="审查意见" />
          <el-table-column prop="suggestion" label="修改建议" />
        </el-table>
        <el-divider />
        <h4>综合评估</h4>
        <p>{{ currentReview.overall }}</p>
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
  { docId: 'S2025-0018', name: '220kV线路停电施工方案', type: '施工方案', opinionCount: 5, status: '已完成',
    opinions: [
      { clause_ref: 'DL 5009.2-2013 §6.2', severity: '严重', comment: '缺少高处作业安全带系挂方案', suggestion: '补充杆塔攀爬防坠措施专项说明' },
      { clause_ref: 'GB 26860-2011 §4.1', severity: '一般', comment: '工作票签发人资质未明确', suggestion: '补充签发人姓名及资质编号' },
    ],
    overall: '方案总体可行，但安全措施部分需补充高处作业防护细节，建议修改后重新提交。'
  },
  { docId: 'S2025-0017', name: '变电站设备吊装方案', type: '专项方案', opinionCount: 0, status: '已完成', opinions: [], overall: '' },
])

const viewDetail = (row) => { currentReview.value = row; showDetail.value = true }
const startReview = () => { ElMessage.info('审查任务已提交') }
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
