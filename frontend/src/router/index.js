import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: '/dashboard', name: 'Dashboard', component: () => import('@/views/dashboard/Index.vue'), meta: { title: '工作台' } },
      { path: '/annotation', name: 'Annotation', component: () => import('@/views/annotation/Index.vue'), meta: { title: '数据标注' } },
      { path: '/annotation/:datasetId', name: 'AnnotationWorkspace', component: () => import('@/views/annotation/Workspace.vue'), meta: { title: '标注工作区' } },
      { path: '/training', name: 'Training', component: () => import('@/views/training/Index.vue'), meta: { title: '模型训练' } },
      { path: '/inference', name: 'Inference', component: () => import('@/views/inference/Index.vue'), meta: { title: '模型推理' } },
      { path: '/drawing-review', name: 'DrawingReview', component: () => import('@/views/drawing-review/Index.vue'), meta: { title: '图纸评审' } },
      { path: '/plan-review', name: 'PlanReview', component: () => import('@/views/plan-review/Index.vue'), meta: { title: '施工方案评审' } },
    ]
  },
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue'), meta: { title: '登录' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
