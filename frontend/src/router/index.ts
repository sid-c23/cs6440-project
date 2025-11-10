import { createRouter, createWebHistory } from 'vue-router'
//import HomeView from '../views/HomeView.vue'
import UsersView from '../views/UsersView.vue'
import DashboardView from '../views/DashboardView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/users',
      name: 'users',
      component: UsersView,
    },
    {
      path: '/dashboard/:userId',
      name: 'dashboard',
      component: DashboardView,
      props: true,
    },
    {
      path: '/',
      redirect: '/users'
    }
  ],
})

export default router
