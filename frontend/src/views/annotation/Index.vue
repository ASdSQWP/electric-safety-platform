<template>
  <div class="annotation-page">
    <div class="page-header">
      <h2>数据标注</h2>
      <div class="header-actions">
        <el-input v-model="search" placeholder="搜索数据集..." prefix-icon="Search" clearable class="search-input" />
        <el-button type="primary" @click="showCreate = true"><el-icon><Plus /></el-icon>新建数据集</el-button>
      </div>
    </div>

    <el-card shadow="never" class="table-card">
      <el-table :data="datasets" stripe>
        <el-table-column prop="name" label="数据集名称" min-width="200">
          <template #default="{ row }">
            <div class="ds-name-cell">
              <el-icon :size="20" color="#3b82f6"><Folder /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="imageCount" label="图片数" width="100" align="center" />
        <el-table-column prop="annotatedCount" label="已标注" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.annotatedCount === row.imageCount ? 'success' : 'warning'" effect="light" round>
              {{ row.annotatedCount }}/{{ row.imageCount }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="180">
          <template #default="{ row }">
            <el-progress :percentage="Math.round(row.annotatedCount/row.imageCount*100)" :stroke-width="8"
              :color="row.annotatedCount === row.imageCount ? '#10b981' : '#3b82f6'" />
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '进行中' ? 'warning' : 'success'" effect="dark" round size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="$router.push(`/annotation/${row.id}`)">进入标注</el-button>
            <el-button size="small">导出</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreate" title="新建数据集" width="520px" destroy-on-close>
      <el-form :model="newDataset" label-width="80px">
        <el-form-item label="名称"><el-input v-model="newDataset.name" placeholder="输入数据集名称" /></el-form-item>
        <el-form-item label="类别"><el-input v-model="newDataset.classes" placeholder="逗号分隔，如: 绝缘子, 导线, 塔材" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="newDataset.desc" type="textarea" :rows="3" placeholder="数据集描述（可选）" /></el-form-item>
        <el-form-item label="上传图片">
          <el-upload drag multiple :auto-upload="false" class="upload-zone">
            <el-icon :size="40" color="#ccc"><Upload /></el-icon>
            <p>点击或拖拽上传图片</p>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="showCreate = false">创建数据集</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Plus, Search, Folder, Upload } from '@element-plus/icons-vue'

const search = ref('')
const showCreate = ref(false)
const newDataset = ref({ name: '', classes: '', desc: '' })

const datasets = ref([
  { id: 1, name: '输电线路缺陷-v3', imageCount: 1280, annotatedCount: 860, status: '进行中' },
  { id: 2, name: '绝缘子自爆-2024', imageCount: 460, annotatedCount: 460, status: '已完成' },
  { id: 3, name: '杆塔基础施工', imageCount: 320, annotatedCount: 120, status: '进行中' },
])
</script>

<style scoped>
.header-actions { display: flex; gap: 12px; }
.search-input { width: 220px; }
.table-card { margin-top: 8px; }
.ds-name-cell { display: flex; align-items: center; gap: 10px; font-weight: 500; }
.upload-zone :deep(.el-upload-dragger) { padding: 24px; }
.upload-zone p { color: var(--gray-400); font-size: 14px; margin-top: 8px; }
</style>
