<template>
  <div class="canvas-container" ref="containerRef" tabindex="0" @keydown="onKeydown">
    <!-- 顶部工具栏 -->
    <div class="canvas-toolbar">
      <el-button-group size="small">
        <el-button :type="tool === 'select' ? 'primary' : ''" @click="setTool('select')" title="选择 (S)"><el-icon><Rank /></el-icon></el-button>
        <el-button :type="tool === 'rect' ? 'primary' : ''" @click="setTool('rect')" title="矩形框 (R)"><el-icon><FullScreen /></el-icon></el-button>
        <el-button :type="tool === 'polygon' ? 'primary' : ''" @click="setTool('polygon')" title="多边形 (P)"><el-icon><Lollipop /></el-icon></el-button>
        <el-button :type="tool === 'point' ? 'primary' : ''" @click="setTool('point')" title="关键点 (K)"><el-icon><Aim /></el-icon></el-button>
      </el-button-group>
      <el-select v-model="activeClass" size="small" placeholder="类别" style="width: 140px; margin-left: 8px" clearable>
        <el-option v-for="c in classes" :key="c.name" :label="c.name" :value="c.name">
          <span :style="{ display:'inline-block', width:'12px', height:'12px', background: c.color, marginRight:'8px', borderRadius:'2px' }"></span>
          {{ c.name }}
        </el-option>
      </el-select>
      <el-divider direction="vertical" />
      <el-button size="small" @click="zoomIn" title="放大 (+)"><el-icon><ZoomIn /></el-icon></el-button>
      <el-button size="small" @click="zoomOut" title="缩小 (-)"><el-icon><ZoomOut /></el-icon></el-button>
      <el-button size="small" @click="fitToScreen" title="适应屏幕 (0)"><el-icon><FullScreen /></el-icon></el-button>
      <el-divider direction="vertical" />
      <el-button size="small" type="success" @click="$emit('ai-predict')" :loading="aiLoading">AI预标注</el-button>
      <el-button size="small" @click="deleteSelected" :disabled="!selectedShape" title="删除 (Delete)"><el-icon><Delete /></el-icon></el-button>
      <el-button size="small" @click="undo" :disabled="history.length === 0" title="撤销 (Ctrl+Z)"><el-icon><RefreshLeft /></el-icon></el-button>
    </div>

    <!-- Konva 舞台 -->
    <div class="stage-wrapper" ref="stageWrapperRef">
      <v-stage ref="stageRef" :config="stageConfig" @mousedown="onStageMouseDown" @mousemove="onStageMouseMove" @mouseup="onStageMouseUp" @wheel="onWheel">
        <v-layer>
          <!-- 底图 -->
          <v-image ref="imageRef" :config="imageConfig" @transformend="onImageTransformEnd" />
        </v-layer>
        <!-- 标注层 -->
        <v-layer ref="layerRef">
          <!-- 已完成的标注 -->
          <template v-for="(shape, i) in shapes" :key="i">
            <v-rect
              v-if="shape.shape_type === 'rectangle'"
              :config="getRectConfig(shape, i)"
              @click="selectShape(i)" @transformend="onShapeTransform(i, $event)" @dragend="onShapeDragEnd(i, $event)"
            />
            <v-line
              v-else-if="shape.shape_type === 'polygon'"
              :config="getPolygonConfig(shape, i)"
              @click="selectShape(i)"
            />
            <v-circle
              v-else-if="shape.shape_type === 'point'"
              :config="getPointConfig(shape, i)"
              @click="selectShape(i)" @dragend="onShapeDragEnd(i, $event)"
            />
            <!-- 标签文字 -->
            <v-text :config="getLabelConfig(shape)" />
          </template>
          <!-- 绘制中的临时形状 -->
          <v-rect v-if="drawing && tool === 'rect'" :config="tempRectConfig" />
          <v-line v-if="drawing && tool === 'polygon'" :config="tempLineConfig" />
        </v-layer>
      </v-stage>
    </div>

    <!-- 信息栏 -->
    <div class="canvas-status">
      <span>鼠标: ({{ Math.round(mousePos.x) }}, {{ Math.round(mousePos.y) }})</span>
      <span>缩放: {{ (stageScale * 100).toFixed(0) }}%</span>
      <span v-if="selectedShape !== null">选中: {{ shapes[selectedShape]?.label || '未命名' }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import Konva from 'konva'

const props = defineProps({
  imageUrl: { type: String, default: '' },
  classes: { type: Array, default: () => [] },  // [{name, color}]
  shapes: { type: Array, default: () => [] },     // external shape data
  aiLoading: { type: Boolean, default: false },
})

const emit = defineEmits(['shapes-update', 'ai-predict', 'shape-select'])

// ---- 状态 ----
const containerRef = ref(null)
const stageWrapperRef = ref(null)
const stageRef = ref(null)
const layerRef = ref(null)
const imageRef = ref(null)

const tool = ref('rect')
const activeClass = ref('')
const selectedShape = ref(null)
const mousePos = ref({ x: 0, y: 0 })
const drawing = ref(false)
const stageScale = ref(1)
const history = ref([])
const polygonPoints = ref([])  // current polygon being drawn

const img = ref(null)
const imgSize = ref({ w: 1, h: 1 })

// ---- 图片加载 ----
watch(() => props.imageUrl, (url) => {
  if (!url) return
  const image = new window.Image()
  image.crossOrigin = 'anonymous'
  image.onload = () => {
    img.value = image
    imgSize.value = { w: image.naturalWidth, h: image.naturalHeight }
    fitToScreen()
  }
  image.src = url
}, { immediate: true })

// ---- 舞台配置 ----
const stageConfig = computed(() => ({
  width: stageWrapperRef.value?.clientWidth || 800,
  height: stageWrapperRef.value?.clientHeight || 600,
  draggable: tool.value === 'select',
  scaleX: stageScale.value,
  scaleY: stageScale.value,
}))

const imageConfig = computed(() => ({
  image: img.value,
  x: 0, y: 0,
  draggable: false,
}))

// ---- 形状渲染 ----
const classColor = (label) => {
  const cls = props.classes.find(c => c.name === label)
  return cls?.color || '#409eff'
}

const getRectConfig = (shape, i) => {
  const [p1, p2] = shape.points
  return {
    x: Math.min(p1[0], p2[0]), y: Math.min(p1[1], p2[1]),
    width: Math.abs(p2[0] - p1[0]), height: Math.abs(p2[1] - p1[1]),
    fill: `${classColor(shape.label)}22`,
    stroke: classColor(shape.label),
    strokeWidth: selectedShape.value === i ? 3 : 1.5,
    draggable: tool.value === 'select',
    name: `shape-${i}`,
  }
}

const getPolygonConfig = (shape, i) => ({
  points: shape.points.flat(),
  fill: `${classColor(shape.label)}22`,
  stroke: classColor(shape.label),
  strokeWidth: selectedShape.value === i ? 3 : 1.5,
  closed: true,
  name: `shape-${i}`,
})

const getPointConfig = (shape, i) => ({
  x: shape.points[0][0], y: shape.points[0][1],
  radius: selectedShape.value === i ? 6 : 4,
  fill: classColor(shape.label),
  stroke: '#fff',
  strokeWidth: 1,
  draggable: tool.value === 'select',
  name: `shape-${i}`,
})

const getLabelConfig = (shape) => ({
  x: shape.points[0][0],
  y: shape.points[0][1] - 18,
  text: `${shape.label}${shape.score ? ` ${(shape.score * 100).toFixed(0)}%` : ''}`,
  fontSize: 12,
  fontFamily: 'Arial',
  fill: '#fff',
  padding: 4,
  background: classColor(shape.label),
  cornerRadius: 2,
  visible: true,
})

// 绘制中的临时形状
const tempRectConfig = computed(() => {
  if (polygonPoints.value.length < 2) return { visible: false }
  const [p1, p2] = polygonPoints.value
  return {
    x: Math.min(p1[0], p2[0]), y: Math.min(p1[1], p2[1]),
    width: Math.abs(p2[0] - p1[0]), height: Math.abs(p2[1] - p1[1]),
    stroke: classColor(activeClass.value || '默认'), strokeWidth: 2, dash: [6, 3],
  }
})

const tempLineConfig = computed(() => ({
  points: polygonPoints.value.flat(),
  stroke: classColor(activeClass.value || '默认'), strokeWidth: 2, dash: [6, 3],
}))

// ---- 鼠标交互 ----
const getStagePos = () => {
  const stage = stageRef.value?.getStage()
  if (!stage) return { x: 0, y: 0 }
  const pos = stage.getPointerPosition()
  return { x: (pos?.x || 0) / stageScale.value, y: (pos?.y || 0) / stageScale.value }
}

const onStageMouseDown = (e) => {
  const pos = getStagePos()
  if (tool.value === 'select') {
    selectedShape.value = null
    return
  }
  if (!activeClass.value) {
    ElMessage.warning('请先选择类别')
    return
  }
  drawing.value = true
  if (tool.value === 'rect') {
    polygonPoints.value = [pos, pos]
  } else if (tool.value === 'polygon') {
    polygonPoints.value = [...polygonPoints.value, pos]
    if (e.evt.button === 2) {
      // 右键完成多边形
      finishShape()
    }
  } else if (tool.value === 'point') {
    finishShape([pos])
  }
}

const onStageMouseMove = () => {
  const pos = getStagePos()
  mousePos.value = pos
  if (tool.value === 'rect' && drawing.value) {
    polygonPoints.value = [polygonPoints.value[0], pos]
  }
}

const onStageMouseUp = () => {
  if (tool.value === 'rect' && drawing.value && polygonPoints.value.length === 2) {
    finishShape(polygonPoints.value)
  }
}

const onWheel = (e) => {
  e.evt.preventDefault()
  const scaleBy = 1.08
  const oldScale = stageScale.value
  const newScale = e.evt.deltaY > 0 ? oldScale / scaleBy : oldScale * scaleBy
  stageScale.value = Math.min(Math.max(newScale, 0.1), 10)
}

// ---- 形状操作 ----
let innerShapes = []

const finishShape = (points) => {
  if (!points || points.length < 2) return
  saveHistory()
  innerShapes.push({
    label: activeClass.value,
    shape_type: tool.value === 'point' ? 'point' : tool.value === 'polygon' ? 'polygon' : 'rectangle',
    points: points,
    score: null,
  })
  polygonPoints.value = []
  drawing.value = false
  syncShapes()
}

const selectShape = (i) => {
  selectedShape.value = i
  emit('shape-select', innerShapes[i])
}

const deleteSelected = () => {
  if (selectedShape.value === null) return
  saveHistory()
  innerShapes.splice(selectedShape.value, 1)
  selectedShape.value = null
  syncShapes()
}

const onShapeTransform = (i, e) => {
  const node = e.target
  const scaleX = node.scaleX()
  const scaleY = node.scaleY()
  node.scaleX(1)
  node.scaleY(1)
  const shape = innerShapes[i]
  shape.points = [
    [node.x(), node.y()],
    [node.x() + node.width() * scaleX, node.y() + node.height() * scaleY],
  ]
  syncShapes()
}

const onShapeDragEnd = (i, e) => {
  const node = e.target
  const shape = innerShapes[i]
  const dx = node.x() - shape.points[0][0]
  const dy = node.y() - shape.points[0][1]
  shape.points = shape.points.map(p => [p[0] + dx, p[1] + dy])
  node.x(shape.points[0][0])
  node.y(shape.points[0][1])
  syncShapes()
}

const syncShapes = () => {
  emit('shapes-update', [...innerShapes])
}

// ---- 外部数据同步 ----
watch(() => props.shapes, (newShapes) => {
  if (JSON.stringify(newShapes) !== JSON.stringify(innerShapes)) {
    innerShapes = JSON.parse(JSON.stringify(newShapes))
  }
}, { deep: true })

// ---- 工具操作 ----
const setTool = (t) => { tool.value = t; selectedShape.value = null }
const zoomIn = () => { stageScale.value = Math.min(stageScale.value * 1.2, 10) }
const zoomOut = () => { stageScale.value = Math.max(stageScale.value / 1.2, 0.1) }
const fitToScreen = () => {
  const w = stageWrapperRef.value?.clientWidth || 800
  const h = stageWrapperRef.value?.clientHeight || 600
  const scale = Math.min(w / imgSize.value.w, h / imgSize.value.h) * 0.9
  stageScale.value = Math.max(scale, 0.01)
}

const saveHistory = () => history.value.push(JSON.parse(JSON.stringify(innerShapes)))
const undo = () => {
  if (history.value.length === 0) return
  innerShapes = history.value.pop()
  syncShapes()
}

// ---- 键盘快捷键 ----
const onKeydown = (e) => {
  const keyMap = {
    KeyR: 'rect', KeyP: 'polygon', KeyK: 'point', KeyS: 'select',
    Delete: 'delete', Backspace: 'delete',
  }
  if (e.ctrlKey && e.code === 'KeyZ') { undo(); return }
  if (keyMap[e.code] === 'delete') { deleteSelected(); return }
  if (['KeyR', 'KeyP', 'KeyK', 'KeyS'].includes(e.code)) { setTool(keyMap[e.code]) }
}

onMounted(() => {
  containerRef.value?.focus()
})

defineExpose({ fitToScreen, zoomIn, zoomOut, getShapes: () => innerShapes })
</script>

<style scoped>
.canvas-container { display: flex; flex-direction: column; height: 100%; outline: none; }
.canvas-toolbar { display: flex; align-items: center; padding: 6px 8px; background: #fafafa; border-bottom: 1px solid #e8e8e8; flex-wrap: wrap; gap: 4px; }
.stage-wrapper { flex: 1; overflow: hidden; background: #e0e0e0; }
.canvas-status { display: flex; gap: 16px; padding: 4px 8px; font-size: 12px; color: #999; background: #f5f5f5; border-top: 1px solid #e8e8e8; }
</style>
