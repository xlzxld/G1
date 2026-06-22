<template>
  <div class="logo" :class="{ collapsed }">
    <span v-if="!collapsed">热流道 MES</span>
    <span v-else>M</span>
  </div>
  <el-menu :default-active="route.path" :collapse="collapsed" background-color="#1d1e2c" text-color="#a3a6b4" active-text-color="#fff" router>
    <el-menu-item v-for="item in visibleItems" :key="item.path" :index="item.path">
      <el-icon><component :is="item.icon" /></el-icon>
      <template #title>{{ item.label }}</template>
    </el-menu-item>
  </el-menu>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '../stores/auth.js';

const route = useRoute();
const auth = useAuthStore();
defineProps({ collapsed: Boolean });

const menuItems = [
  { path: '/', label: '仪表台', icon: 'Odometer', page: 'dashboard' },
  { path: '/customers', label: '客户管理', icon: 'UserFilled', page: 'customers' },
  { path: '/orders', label: '订单管理', icon: 'Document', page: 'orders' },
  { path: '/process-flow', label: '工艺流程', icon: 'SetUp', page: 'process_flow' },
  { path: '/drawings', label: '图纸管理', icon: 'PictureFilled', page: 'drawings' },
  { path: '/inventory', label: '库存管理', icon: 'Box', page: 'inventory' },
  { path: '/users', label: '用户管理', icon: 'Avatar', page: 'users' },
  { path: '/notifications', label: '通知中心', icon: 'Bell', page: 'notifications' },
  { path: '/settings', label: '系统设置', icon: 'Setting', page: 'settings' },
  { path: '/outsourcing', label: '外协管理', icon: 'Van', page: 'outsourcing' },
];

const visibleItems = computed(() =>
  menuItems.filter((item) => {
    if (auth.isAdmin) return true;
    const perm = auth.permissions.find((p) => p.page_key === item.page);
    return perm?.can_view;
  })
);
</script>

<style scoped>
.logo { color: #fff; text-align: center; padding: 18px 0; font-size: 16px; font-weight: 600; letter-spacing: 1px; }
.logo.collapsed { font-size: 20px; }
</style>
