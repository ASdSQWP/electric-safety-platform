<template>
  <div class="workspace">
    <!-- 左侧：图片文件列表 -->
    <div class="left-panel" :style="{ width: panelWidth + 'px' }">
      <div class="panel-header">
        <span>图片列表 ({{ images.length }})</span>
        <el-upload :show-file-list="false" accept="image/*" multiple @change="onUpload">
          <el-button size="small" type="primary" circle><el-icon><Plus /></el-icon></el-button>
        </el-upload>
      </div>
      <div class="image-list">
        <div
          v-for="(img, i) in images"
          :key="i"
          class="image-item"
          :class="{ active: currentIndex === i }"
          @click="selectImage(i)"
        >
          <img :src="img.thumbnail || img.url" :alt="img.name" />
          <div class="image-name">{{ img.name }}</div>
          <el-tag size="small" type="success" v-if="img.annotated">{{ img.shapes?.length || 0 }}</el-tag>
        </div>
        <el-empty v-if="images.length === 0" description="请上传图片" :image-size="60" />
      </div>
    </div>

    <!-- 拖拽分隔条 -->
    <div class="resize-handle" @mousedown="startResize" :style="{ left: panelWidth + 'px' }"></div>

    <!-- 中间：标注画布 -->
    <div class="canvas-panel" :style="{ left: panelWidth + 'px' }">
      <AnnotationCanvas
        ref="canvasRef"
        :image-url="currentImage?.url"
        :classes="classList"
        :shapes="currentImage?.shapes || []"
        :ai-loading="aiLoading"
        @shapes-update="onShapesUpdate"
        @ai-predict="aiPredict"
        @shape-select="onShapeSelect"
      />
    </div>

    <!-- 右侧：属性面板 -->
    <div class="right-panel">
      <el-tabs v-model="rightTab">
        <el-tab-pane label="标注" name="labels">
          <div class="shape-list">
            <div v-for="(shape, i) in currentImage?.shapes || []" :key="i" class="shape-item"
              :style="{ borderLeftColor: classColor(shape.label) }"
              @click="canvasRef?.selectShape(i)"
            >
              <el-tag size="small" :color="classColor(shape.label)" style="border: none; color: #fff">{{ shape.label }}</el-tag>
              <span class="shape-type">{{ shape.shape_type === 'rectangle' ? '□' : shape.shape_type === 'polygon' ? '⬠' : '●' }}</span>
              <el-button size="small" circle :icon="Delete" @click.stop="deleteShape(i)" />
            </div>
            <el-empty v-if="!currentImage?.shapes?.length" description="暂无标注" :image-size="40" />
          </div>
        </el-tab-pane>
        <el-tab-pane label="信息" name="info">
          <el-descriptions :column="1" size="small" border v-if="currentImage">
            <el-descriptions-item label="文件名">{{ currentImage.name }}</el-descriptions-item>
            <el-descriptions-item label="尺寸">{{ currentImage.width }} × {{ currentImage.height }}</el-descriptions-item>
            <el-descriptions-item label="标注数">{{ currentImage.shapes?.length || 0 }}</el-descriptions-item>
          </el-descriptions>
          <el-empty v-else description="未选择图片" :image-size="40" />
        </el-tab-pane>
      </el-tabs>

      <div class="export-area">
        <el-select v-model="exportFormat" size="small" style="width: 100%">
          <el-option label="YOLO TXT" value="yolo" />
          <el-option label="VOC XML" value="voc" />
          <el-option label="COCO JSON" value="coco" />
        </el-select>
        <el-button type="primary" size="small" style="width: 100%; margin-top: 6px" @click="exportAnnotations">导出标注</el-button>
        <el-button size="small" style="width: 100%; margin-top: 4px" @click="$router.back()">返回列表</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Delete, Plus } from '@element-plus/icons-vue'
import { ai } from '@/api'
import AnnotationCanvas from '@/components/AnnotationCanvas/Canvas.vue'
import http from '@/api'

const route = useRoute()
const datasetId = route.params.datasetId
const canvasRef = ref(null)

// 面板尺寸
const panelWidth = ref(220)
const rightTab = ref('labels')
const exportFormat = ref('yolo')
const aiLoading = ref(false)

// 图片数据
const images = ref([])
const currentIndex = ref(-1)
const currentImage = ref(null)
const classList = ref([])

// 获取类别
onMounted(async () => {
  try {
    const res = await http.get('/annotation/classes')
    const names = Object.keys(res.classes)
    const colors = res.colors
    classList.value = names.map(n => ({ name: n, color: colors[n] || '#409eff' }))
  } catch {
    classList.value = [
      { name: '绝缘子', color: '#FF0000' }, { name: '导线', color: '#00FF00' },
      { name: '塔材', color: '#0000FF' }, { name: '防振锤', color: '#FFFF00' },
      { name: '间隔棒', color: '#FF00FF' }, { name: '人员', color: '#008000' },
    ]
  }
})

// 图片上传
const onUpload = (uploadFile) => {
  const file = uploadFile.raw
  const url = URL.createObjectURL(file)
  const img = new window.Image()
  img.onload = () => {
    images.value.push({
      name: file.name, url, width: img.naturalWidth, height: img.naturalHeight,
      thumbnail: url, shapes: [], annotated: false,
    })
    if (currentIndex.value < 0) selectImage(0)
  }
  img.src = url
}

const selectImage = (i) => {
  currentIndex.value = i
  currentImage.value = images.value[i]
}

// 形状更新
const onShapesUpdate = (shapes) => {
  if (currentImage.value) {
    currentImage.value.shapes = shapes
    currentImage.value.annotated = shapes.length > 0
  }
}

const onShapeSelect = (shape) => { /* 属性面板联动 */ }

const deleteShape = (i) => {
  if (currentImage.value) {
    currentImage.value.shapes.splice(i, 1)
  }
}

const classColor = (label) => {
  return classList.value.find(c => c.name === label)?.color || '#409eff'
}

// AI 预标注
const aiPredict = async () => {
  if (!currentImage.value) return
  aiLoading.value = true
  try {
    const blob = await fetch(currentImage.value.url).then(r => r.blob())
    const formData = new FormData()
    formData.append('file', blob, currentImage.value.name)
    const res = await ai.post('/annotation/predict', formData)
    const shapes = (res.shapes || []).map(s => ({
      label: s.class_name,
      shape_type: 'rectangle',
      points: [[s.bbox[0] * currentImage.value.width, s.bbox[1] * currentImage.value.height],
               [s.bbox[2] * currentImage.value.width, s.bbox[3] * currentImage.value.height]],
      score: s.confidence,
    }))
    currentImage.value.shapes = [...(currentImage.value.shapes || []), ...shapes]
    currentImage.value.annotated = currentImage.value.shapes.length > 0
    ElMessage.success(`AI预标注完成：${shapes.length} 个目标`)
  } catch (e) {
    ElMessage.error('AI预标注失败')
  }
  aiLoading.value = false
}

// 导出
const exportAnnotations = async () => {
  const exportData = {
    images: images.value.filter(img => img.shapes.length > 0).map(img => ({
      image_path: img.name, width: img.width, height: img.height,
      shapes: img.shapes.map(s => ({
        label: s.label, shape_type: s.shape_type, points: s.points,
        group_id: s.group_id, score: s.score, difficult: s.difficult,
        description: s.description || '', flags: s.flags || {}, attributes: s.attributes || {},
      })),
    })),
    format: exportFormat.value,
    classes: classList.value.map(c => c.name),
  }
  try {
    const res = await http.post('/annotation/export', exportData)
    ElMessage.success(`已导出 ${res.count} 张图片的标注数据`)
  } catch {
    ElMessage.error('导出失败')
  }
}

// 面板拖拽
let dragging = false
const startResize = () => { dragging = true }
const onMouseMove = (e) => { if (dragging) panelWidth.value = Math.max(150, Math.min(e.clientX - 80, 400)) }
const onMouseUp = () => { dragging = false }
onMounted(() => { document.addEventListener('mousemove', onMouseMove); document.addEventListener('mouseup', onMouseUp) })
onUnmounted(() => { document.removeEventListener('mousemove', onMouseMove); document.removeEventListener('mouseup', onMouseUp) })
</script>

<style scoped>
.workspace { display: flex; height: calc(100vh - 120px); position: relative; }
.left-panel { position: absolute; left: 0; top: 0; bottom: 0; background: #fff; border-right: 1px solid #eee; display: flex; flex-direction: column; z-index: 2; }
.panel-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 10px; font-weight: 500; border-bottom: 1px solid #eee; }
.image-list { flex: 1; overflow-y: auto; padding: 6px; }
.image-item { padding: 4px; margin-bottom: 6px; border-radius: 4px; cursor: pointer; border: 2px solid transparent; }
.image-item.active { border-color: #409eff; background: #ecf5ff; }
.image-item img { width: 100%; height: 80px; object-fit: cover; border-radius: 2px; }
.image-name { font-size: 11px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; margin-top: 2px; }

.resize-handle { position: absolute; top: 0; bottom: 0; width: 4px; cursor: col-resize; z-index: 3; background: transparent; }
.resize-handle:hover { background: #409eff44; }

.canvas-panel { position: absolute; top: 0; right: 320px; bottom: 0; left: 220px; }

.right-panel { position: absolute; right: 0; top: 0; bottom: 0; width: 320px; background: #fff; border-left: 1px solid #eee; display: flex; flex-direction: column; padding: 6px; }
.shape-list { flex: 1; overflow-y: auto; }
.shape-item { display: flex; align-items: center; gap: 6px; padding: 6px 8px; border-left: 3px solid; margin-bottom: 2px; background: #fafafa; cursor: pointer; border-radius: 0 4px 4px 0; }
.shape-item:hover { background: #f0f0f0; }
.shape-type { font-size: 14px; color: #999; flex: 1; }
.export-area { padding: 8px 0; border-top: 1px solid #eee; margin-top: auto; }
</style>
