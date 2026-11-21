import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import DayView from '../views/DayView.vue'
import WeekView from '../views/WeekView.vue'

const router = createRouter({
  history: createWebHashHistory(),
  scrollBehavior() {
    return { top: 0 }
  },
  routes: [
    { path: '/', name: 'home', component: HomeView, meta: { title: 'A股每日复盘' } },
    { path: '/day/:date', name: 'day', component: DayView, meta: { title: '每日复盘' } },
    { path: '/week', name: 'week', component: WeekView, meta: { title: '一周复盘' } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.afterEach((to) => {
  const date = to.params.date
  document.title = date ? `A股每日复盘 · ${date}` : (to.meta.title || 'A股每日复盘')
})

export default router
