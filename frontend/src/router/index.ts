import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import BlogView from '@/views/BlogView.vue'
import BlogDetailView from '@/views/BlogDetailView.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'home',
    component: () => import(/* webpackChunkName: "home" */ '../views/HomeView.vue')
  },
  {
    path: '/hosts/:id',
    name: 'host-detail',
    component: () => import(/* webpackChunkName: "host-detail" */ '../views/HostDetailView.vue'),
    props: true
  },
  {
    path: '/hosts',
    name: 'hosts',
    component: () => import(/* webpackChunkName: "hosts" */ '../views/HostsView.vue')
  },
  {
    path: '/blog',
    name: 'blog',
    component: BlogView
  },
  {
    path: '/blog/:id',
    name: 'blog-detail',
    component: BlogDetailView
  },
  {
    path: '/api',
    name: 'api',
    component: () => import(/* webpackChunkName: "api" */ '../views/ApiView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
