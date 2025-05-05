import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'home',
    component: () => import(/* webpackChunkName: "home" */ '../views/HomeView.vue')
  },
  {
    path: '/about',
    name: 'about',
    component: () => import(/* webpackChunkName: "about" */ '../views/AboutView.vue')
  },
  {
    path: '/hosts',
    name: 'host-list',
    component: () => import(/* webpackChunkName: "host-list" */ '../views/HostListView.vue')
  },
  {
    path: '/hosts/:id',
    name: 'host-detail',
    component: () => import(/* webpackChunkName: "host-detail" */ '../views/HostDetailView.vue'),
    props: true
  },
  {
    path: '/explore',
    name: 'explore',
    component: () => import(/* webpackChunkName: "explore" */ '../views/ExploreView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
