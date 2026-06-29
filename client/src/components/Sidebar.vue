<template>
  <div class="flex flex-col h-full bg-white dark:bg-industrial-800">
    <!-- Logo Area -->
    <div class="flex items-center justify-center h-16 border-b border-slate-200 dark:border-industrial-border shrink-0">
      <span v-if="!collapsed" class="text-slate-800 dark:text-slate-100 font-bold tracking-widest whitespace-nowrap overflow-hidden">汇易通热流道管理系统</span>
      <span v-else class="text-blue-500 dark:text-industrial-accent font-bold text-xl">M</span>
      
      <!-- Mobile Close Button -->
      <button @click="$emit('close-mobile')" class="lg:hidden absolute right-4 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white">
        <el-icon :size="20"><Close /></el-icon>
      </button>
    </div>

    <!-- Scrollable Menu Area -->
    <div class="flex-1 overflow-y-auto no-scrollbar py-4">
      <el-menu 
        :default-active="route.path" 
        :collapse="collapsed" 
        background-color="transparent" 
        text-color="inherit" 
        active-text-color="var(--el-color-primary)" 
        router
        class="border-r-0! custom-menu"
      >
        <el-menu-item v-for="item in visibleItems" :key="item.path" :index="item.path" class="hover:bg-slate-100! dark:hover:bg-industrial-700/50! text-slate-600 dark:text-slate-400">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.label }}</template>
        </el-menu-item>
      </el-menu>
    </div>

    <!-- Bottom User Greeting Profile Panel -->
    <div class="border-t border-slate-200 dark:border-industrial-border p-4 shrink-0 bg-slate-50/50 dark:bg-industrial-900/10">
      <div v-if="!collapsed" class="flex items-center gap-3">
        <!-- Avatar/Initials Circle -->
        <div class="w-9 h-9 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold shadow-sm shrink-0 uppercase select-none">
          {{ auth.user?.display_name?.slice(0, 1) || auth.user?.username?.slice(0, 1) || 'U' }}
        </div>
        <!-- Text & Greeting -->
        <div class="flex flex-col min-w-0">
          <span class="text-[10px] text-slate-400 dark:text-slate-500 font-semibold tracking-wider uppercase truncate">{{ auth.user?.role_label || '用户' }}</span>
          <span class="text-xs font-semibold text-slate-700 dark:text-slate-300 truncate mt-0.5" :title="`${auth.user?.display_name || auth.user?.username}，${greetingText}`">
            {{ auth.user?.display_name || auth.user?.username }}，{{ greetingText }}
          </span>
        </div>
      </div>
      <div v-else class="flex justify-center">
        <!-- Minimalist Avatar when collapsed -->
        <el-tooltip :content="`${auth.user?.display_name || auth.user?.username}，${greetingText}`" placement="right">
          <div class="w-9 h-9 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold shadow-sm shrink-0 uppercase cursor-pointer select-none">
            {{ auth.user?.display_name?.slice(0, 1) || auth.user?.username?.slice(0, 1) || 'U' }}
          </div>
        </el-tooltip>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '../stores/auth.js';

const route = useRoute();
const auth = useAuthStore();
defineProps({ collapsed: Boolean });
defineEmits(['close-mobile']);

const menuItems = [
  { path: '/', label: '仪表台', icon: 'Odometer', page: 'dashboard' },
  { path: '/customers', label: '客户管理', icon: 'UserFilled', page: 'customers' },
  { path: '/orders', label: '订单管理', icon: 'Document', page: 'orders' },
  { path: '/process-flow', label: '工艺管理', icon: 'Setting', page: 'process_flow' },
  { path: '/inventory', label: '库存管理', icon: 'Box', page: 'inventory' },
  { path: '/users', label: '用户管理', icon: 'Avatar', page: 'users', requiresAdmin: true },
  { path: '/notifications', label: '通知中心', icon: 'Bell', page: 'notifications' },
  { path: '/outsourcing', label: '外协管理', icon: 'Van', page: 'outsourcing' },
  { path: '/settings', label: '系统设置', icon: 'Setting', page: 'settings' },
];

const visibleItems = computed(() =>
  menuItems.filter((item) => {
    if (item.requiresAdmin) {
      return auth.isAdmin;
    }
    return auth.canView(item.page);
  })
);

// 根据时间自动返回问候词
const greetingText = computed(() => {
  const hr = new Date().getHours();
  if (hr >= 0 && hr < 6) return '凌晨好';
  if (hr >= 6 && hr < 9) return '早上好';
  if (hr >= 9 && hr < 11) return '上午好';
  if (hr >= 11 && hr < 13) return '中午好';
  if (hr >= 13 && hr < 18) return '下午好';
  return '晚上好';
});
</script>

<style scoped>
/* Hide scrollbar for a cleaner industrial look */
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
.el-menu { border-right: none !important; }
</style>
