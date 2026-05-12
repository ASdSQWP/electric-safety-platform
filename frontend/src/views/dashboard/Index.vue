<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6" v-for="card in statsCards" :key="card.title">
        <div class="stat-card" :style="{ '--accent': card.color }">
          <div class="stat-icon-box" :style="{ background: card.color }">
            <el-icon :size="26"><component :is="card.icon" /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-value">
              <span ref="countRefs">{{ card.value }}</span>
              <small>{{ card.unit || '' }}</small>
            </div>
            <div class="stat-label">{{ card.title }}</div>
          </div>
          <div class="stat-trend" :class="card.trend > 0 ? 'up' : 'down'">
            <el-icon><component :is="card.trend > 0 ? 'Top' : 'Bottom'" /></el-icon>
            {{ Math.abs(card.trend) }}%
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <div class="card-title-row">
              <span class="card-title">检测趋势</span>
              <el-radio-group v-model="chartPeriod" size="small">
                <el-radio-button value="week">近7天</el-radio-button>
                <el-radio-button value="month">近30天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="trendChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>
            <div class="card-title-row">
              <span class="card-title">缺陷类别分布</span>
            </div>
          </template>
          <div ref="pieChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 底部：最近活动 + 快捷入口 -->
    <el-row :gutter="20" class="bottom-row">
      <el-col :span="16">
        <el-card shadow="never">
          <template #header><span class="card-title">最近活动</span></template>
          <el-timeline>
            <el-timeline-item
              v-for="(item, i) in activities"
              :key="i"
              :timestamp="item.time"
              placement="top"
              :color="item.color"
            >
              {{ item.content }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <template #header><span class="card-title">快捷入口</span></template>
          <div class="quick-links">
            <div class="quick-link" @click="$router.push('/annotation')">
              <el-icon :size="22" color="#3b82f6"><Edit /></el-icon>
              <div class="ql-info">
                <div class="ql-title">新建标注任务</div>
                <div class="ql-desc">上传图片开始数据标注</div>
              </div>
              <el-icon color="#ccc"><ArrowRight /></el-icon>
            </div>
            <div class="quick-link" @click="$router.push('/training')">
              <el-icon :size="22" color="#10b981"><Cpu /></el-icon>
              <div class="ql-info">
                <div class="ql-title">启动模型训练</div>
                <div class="ql-desc">微调AI检测模型</div>
              </div>
              <el-icon color="#ccc"><ArrowRight /></el-icon>
            </div>
            <div class="quick-link" @click="$router.push('/drawing-review')">
              <el-icon :size="22" color="#f59e0b"><Document /></el-icon>
              <div class="ql-info">
                <div class="ql-title">上传图纸评审</div>
                <div class="ql-desc">AI分析工程图纸问题</div>
              </div>
              <el-icon color="#ccc"><ArrowRight /></el-icon>
            </div>
            <div class="quick-link" @click="$router.push('/plan-review')">
              <el-icon :size="22" color="#ef4444"><Notebook /></el-icon>
              <div class="ql-info">
                <div class="ql-title">施工方案审查</div>
                <div class="ql-desc">RAG+LLM智能方案评审</div>
              </div>
              <el-icon color="#ccc"><ArrowRight /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { PictureFilled, Cpu, Document, DataAnalysis, Edit, Notebook, Top, Bottom, ArrowRight } from '@element-plus/icons-vue'

const chartPeriod = ref('week')
const trendChartRef = ref(null)
const pieChartRef = ref(null)
let trendChart = null
let pieChart = null

const statsCards = [
  { title: '数据集', value: 12, unit: '', icon: PictureFilled, color: '#3b82f6', trend: 8 },
  { title: '训练模型', value: 5, unit: '', icon: Cpu, color: '#10b981', trend: 15 },
  { title: '图纸评审', value: 42, unit: '', icon: Document, color: '#f59e0b', trend: -3 },
  { title: '方案评审', value: 18, unit: '', icon: DataAnalysis, color: '#ef4444', trend: 12 },
]

const activities = [
  { time: '2026-05-12 14:30', content: '训练任务 #a3f2 已完成 — YOLOv8s mAP50=0.87', color: '#10b981' },
  { time: '2026-05-12 10:15', content: '数据集「输电线路缺陷v3」审核通过，含1,280张照片', color: '#3b82f6' },
  { time: '2026-05-11 16:00', content: '图纸评审 #B2025-0042 已完成，发现3处问题', color: '#f59e0b' },
  { time: '2026-05-11 09:30', content: '知识库新增文档《电力安全工作规程2025版》', color: '#8b5cf6' },
  { time: '2026-05-10 11:00', content: '施工方案「铁塔组立方案v2」审查通过', color: '#10b981' },
]

function initTrendChart() {
  if (!trendChartRef.value) return
  trendChart = echarts.init(trendChartRef.value)
  const data = chartPeriod.value === 'week'
    ? { dates: ['5/6','5/7','5/8','5/9','5/10','5/11','5/12'], inspections: [28,35,42,38,30,45,52], issues: [3,5,4,2,6,3,4] }
    : { dates: Array.from({length:30},(_,i)=>`4/${13+i}`), inspections: Array.from({length:30},()=>Math.floor(Math.random()*40+20)), issues: Array.from({length:30},()=>Math.floor(Math.random()*8+1)) }
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['检测次数','发现问题'], bottom: 0 },
    grid: { left: 16, right: 16, top: 8, bottom: 32 },
    xAxis: { type: 'category', data: data.dates, axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f0f0f0' } } },
    series: [
      { name: '检测次数', type: 'bar', data: data.inspections, itemStyle: { borderRadius: [6,6,0,0], color: '#3b82f6' }, barWidth: '40%' },
      { name: '发现问题', type: 'line', data: data.issues, smooth: true, lineStyle: { color: '#ef4444', width: 2 }, itemStyle: { color: '#ef4444' }, symbolSize: 6 },
    ],
  })
}

function initPieChart() {
  if (!pieChartRef.value) return
  pieChart = echarts.init(pieChartRef.value)
  pieChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', right: 0, top: 'center', itemWidth: 10, itemHeight: 10 },
    series: [{
      type: 'pie', radius: ['55%','80%'], center: ['35%','50%'], avoidLabelOverlap: false,
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      data: [
        { value: 35, name: '绝缘子缺陷', itemStyle: { color: '#ef4444' } },
        { value: 25, name: '导线断股', itemStyle: { color: '#f59e0b' } },
        { value: 18, name: '安全帽未佩戴', itemStyle: { color: '#3b82f6' } },
        { value: 12, name: '安全带违规', itemStyle: { color: '#8b5cf6' } },
        { value: 10, name: '其他', itemStyle: { color: '#6b7280' } },
      ],
    }],
  })
}

watch(chartPeriod, () => {
  if (trendChart) { trendChart.dispose(); initTrendChart(); }
})

onMounted(() => {
  nextTick(() => { initTrendChart(); initPieChart(); })
})
</script>

<style scoped>
.dashboard { max-width: 1280px; }

.stats-row { margin-bottom: 20px; }

.stat-card {
  background: #fff;
  border-radius: var(--radius-md);
  border: 1px solid var(--gray-200);
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all .25s;
  cursor: default;
  position: relative;
  overflow: hidden;
}
.stat-card::after {
  content: '';
  position: absolute;
  top: 0; right: 0;
  width: 80px; height: 80px;
  background: var(--accent);
  opacity: .04;
  border-radius: 0 0 0 80px;
  transition: all .3s;
}
.stat-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
.stat-card:hover::after { width: 100px; height: 100px; opacity: .07; }

.stat-icon-box {
  width: 52px; height: 52px;
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.stat-body { flex: 1; }
.stat-value { font-size: 26px; font-weight: 700; color: var(--gray-900); line-height: 1.1; }
.stat-value small { font-size: 14px; font-weight: 400; color: var(--gray-500); }
.stat-label { font-size: 13px; color: var(--gray-500); margin-top: 2px; }
.stat-trend { font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 2px; }
.stat-trend.up { color: #10b981; }
.stat-trend.down { color: #ef4444; }

.charts-row { margin-bottom: 20px; }
.chart-box { height: 280px; }

.card-title-row { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-size: 15px; font-weight: 600; color: var(--gray-900); }

.bottom-row { }
.bottom-row .el-card { height: 100%; }

/* 快捷入口 */
.quick-links { display: flex; flex-direction: column; }
.quick-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 12px;
  border-radius: var(--radius);
  cursor: pointer;
  transition: background .2s;
}
.quick-link:hover { background: var(--gray-50); }
.ql-info { flex: 1; }
.ql-title { font-size: 14px; font-weight: 500; color: var(--gray-800); }
.ql-desc { font-size: 12px; color: var(--gray-400); margin-top: 2px; }
</style>
