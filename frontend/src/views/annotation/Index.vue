<template>
  <div class="annotation-page">
    <div class="page-header">
      <h2>数据标注</h2>
      <el-button type="primary" @click="showCreate = true">新建数据集</el-button>
    </div>

    <el-table :data="datasets" stripe>
      <el-table-column prop="name" label="数据集名称" />
      <el-table-column prop="imageCount" label="图片数" width="100" />
      <el-table-column prop="annotatedCount" label="已标注" width="100" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }"><el-tag :type="row.status === '进行中' ? 'warning' : 'success'">{{ row.status }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/annotation/${row.id}`)">进入标注</el-button>
          <el-button size="small" type="success">导出</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreate" title="新建数据集" width="500px">
      <el-form :model="newDataset" label-width="80px">
        <el-form-item label="名称"><el-input v-model="newDataset.name" /></el-form-item>
        <el-form-item label="类别"><el-input v-model="newDataset.classes" placeholder="逗号分隔，如: 绝缘子,导线,塔材" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="newDataset.desc" type="textarea" /></el-form-item>
        <el-form-item><el-upload drag multiple><el-button>点击或拖拽上传图片</el-button></el-upload></el-form-item>
      </el-form>
      <template #footer><el-button @click="showCreate = false">取消</el-button><el-button type="primary" @click="showCreate = false">创建</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const showCreate = ref(false)
const newDataset = ref({ name: '', classes: '', desc: '' })

const datasets = ref([
  { id: 1, name: '输电线路缺陷-v3', imageCount: 1280, annotatedCount: 860, status: '进行中' },
  { id: 2, name: '绝缘子自爆-2024', imageCount: 460, annotatedCount: 460, status: '已完成' },
  { id: 3, name: '杆塔基础施工', imageCount: 320, annotatedCount: 120, status: '进行中' },
])
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
