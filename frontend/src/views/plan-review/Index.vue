<template>
  <div class="plan-review-page">
    <div class="page-header">
      <h2>施工方案评审</h2>
      <div class="header-actions">
        <el-input v-model="search" placeholder="搜索方案..." prefix-icon="Search" clearable class="search-input" />
        <el-button type="primary" @click="showUpload = true"><el-icon><Upload /></el-icon>上传施工方案</el-button>
      </div>
    </div>

    <el-card shadow="never" class="table-card">
      <el-table :data="reviews" stripe>
        <el-table-column prop="docId" label="文档编号" width="150">
          <template #default="{ row }"><span class="id-tag">{{ row.docId }}</span></template>
        </el-table-column>
        <el-table-column prop="name" label="方案名称" min-width="200">
          <template #default="{ row }">
            <div class="name-cell">
              <el-icon :size="18" color="#3b82f6"><Notebook /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="120" align="center">
          <template #default="{ row }"><el-tag effect="plain" round size="small">{{ row.type }}</el-tag></template>
        </el-table-column>
        <el-table-column label="审查意见" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.opinionCount > 0 ? 'danger' : 'success'" effect="dark" round size="small">
              {{ row.opinionCount }}条意见
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '已完成' ? 'success' : 'info'" effect="light" round size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="viewDetail(row)">查看详情</el-button>
            <el-button size="small" type="warning" @click="exportOpinions(row)">导出意见</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 上传弹窗 -->
    <el-dialog v-model="showUpload" title="上传施工方案" width="520px" destroy-on-close>
      <el-upload drag :auto-upload="false" accept=".pdf,.docx,.doc" class="upload-zone">
        <el-icon :size="48" color="#ccc"><Upload /></el-icon>
        <p>支持 PDF / DOCX 格式</p>
        <small>方案文档将基于知识库规范进行AI审查</small>
      </el-upload>
      <template #footer>
        <el-button @click="showUpload = false">取消</el-button>
        <el-button type="primary" @click="showUpload = false; startReview()">开始审查</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="showDetail" title="审查详情" width="860px" destroy-on-close>
      <template v-if="currentReview">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="文档编号">{{ currentReview.docId }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ currentReview.type }}</el-descriptions-item>
          <el-descriptions-item label="方案名称" :span="2">{{ currentReview.name }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:20px 0 12px;font-size:15px;color:var(--gray-800)">审查意见清单</h4>
        <el-table :data="currentReview.opinions" stripe size="small" v-if="currentReview.opinions.length">
          <el-table-column prop="clause_ref" label="引用规范" width="190">
            <template #default="{ row }"><el-tag effect="plain" size="small" type="info">{{ row.clause_ref }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="severity" label="严重程度" width="85" align="center">
            <template #default="{ row }">
              <el-tag :type="row.severity === '严重' ? 'danger' : row.severity === '危急' ? 'danger' : 'warning'" effect="dark" size="small">
                {{ row.severity }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="comment" label="审查意见" min-width="200" />
          <el-table-column prop="suggestion" label="修改建议" min-width="200" />
        </el-table>
        <el-empty v-else description="无审查意见" :image-size="60" />
        <el-divider />
        <div class="overall-box">
          <h4>综合评估</h4>
          <p>{{ currentReview.overall || '暂未生成综合评估' }}</p>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Upload, Search, Notebook } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const search = ref('')
const showUpload = ref(false)
const showDetail = ref(false)
const currentReview = ref(null)

const reviews = ref([
  { docId: 'S2025-0018', name: '220kV线路停电施工方案', type: '施工方案', opinionCount: 5, status: '已完成',
    opinions: [
      { clause_ref: 'DL 5009.2-2013 §6.2', severity: '严重', comment: '缺少高处作业安全带系挂方案', suggestion: '补充杆塔攀爬防坠措施专项说明' },
      { clause_ref: 'GB 26860-2011 §4.1', severity: '一般', comment: '工作票签发人资质未明确', suggestion: '补充签发人姓名及资质编号' },
      { clause_ref: 'DL 5009.2-2013 §8.3', severity: '严重', comment: '临近带电体作业安全距离不足', suggestion: '增加绝缘遮蔽措施并明确安全监护人员' },
      { clause_ref: 'GB 26860-2011 §5.2', severity: '一般', comment: '应急预案缺少触电急救流程', suggestion: '补充触电急救步骤和就近医院信息' },
      { clause_ref: 'DL 5009.2-2013 §3.1', severity: '一般', comment: '施工人员安全培训记录缺失', suggestion: '附上安全技术交底签字表' },
    ],
    overall: '方案总体可行，但安全措施部分需补充高处作业防护和临近带电体作业细节。建议根据审查意见修改后重新提交，重点完善第1、3条严重问题。'
  },
  { docId: 'S2025-0017', name: '变电站设备吊装方案', type: '专项方案', opinionCount: 0, status: '已完成', opinions: [], overall: '方案审查通过，各项安全措施完备，同意实施。' },
])

const viewDetail = (row) => { currentReview.value = row; showDetail.value = true }
const exportOpinions = (row) => { ElMessage.success({ message: `意见导出中: ${row.docId}`, duration: 2000 }) }
const startReview = () => {
  ElMessage.info('方案审查任务已提交，正在基于知识库规范进行AI分析')
  reviews.value.unshift({ docId: 'S2025-0019', name: '新上传方案', type: '施工方案', opinionCount: 0, status: '审查中', opinions: [], overall: '' })
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
.overall-box { background: var(--gray-50); border-radius: var(--radius); padding: 16px 20px; border-left: 3px solid var(--brand-500); }
.overall-box h4 { margin-bottom: 8px; font-size: 14px; color: var(--gray-800); }
.overall-box p { color: var(--gray-600); font-size: 14px; line-height: 1.7; }
</style>
