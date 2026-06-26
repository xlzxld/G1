import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth.js';

function placeholder(view) {
  return { template: '<div style="padding:24px"><h2>' + view + '</h2><p>模块开发中</p></div>' };
}

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { guest: true } },
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { page: 'dashboard' } },
  { path: '/customers', name: 'Customers', component: () => import('../views/Customers.vue'), meta: { page: 'customers' } },
  { path: '/customers/:id', name: 'CustomerDetail', component: () => import('../views/CustomerDetail.vue'), meta: { page: 'customers' } },
  { path: '/orders', name: 'Orders', component: () => import('../views/Orders.vue'), meta: { page: 'orders' } },
  { path: '/orders/:id', name: 'OrderDetail', component: () => import('../views/OrderDetail.vue'), meta: { page: 'orders' } },
  { path: '/process-flow', name: 'ProcessFlow', component: () => import('../views/ProcessFlow.vue'), meta: { page: 'process_flow' } },
  { path: '/inventory', name: 'Inventory', component: () => import('../views/Inventory.vue'), meta: { page: 'inventory' } },
  { path: '/users', name: 'Users', component: () => import('../views/Users.vue'), meta: { page: 'users' } },
  { path: '/notifications', name: 'Notifications', component: () => import('../views/Notifications.vue'), meta: { page: 'notifications' } },
  { path: '/settings', name: 'Settings', component: () => import('../views/Settings.vue'), meta: { page: 'settings' } },
  { path: '/outsourcing', name: 'Outsourcing', component: () => import('../views/Outsourcing.vue'), meta: { page: 'outsourcing' } },
];

const router = createRouter({ history: createWebHistory(), routes });

router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore();
  if (to.meta.guest) return next();
  if (!auth.user && auth.token) { try { await auth.fetchMe(); } catch { auth.logout(); return next('/login'); } }
  if (!auth.user) return next('/login');
  if (auth.isAdmin) return next();
  const page = to.meta.page;
  if (page) {
    if (!auth.canView(page)) {
      const first = auth.permissions.find((p) => p.can_view);
      if (first) { const path = '/' + (first.page_key === 'dashboard' ? '' : first.page_key.replace(/_/g, '-')); return next(path); }
      return next('/login');
    }
  }
  next();
});

export default router;
