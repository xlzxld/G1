<template>
  <router-view v-if="$route.meta.guest" />
  <div v-else class="flex h-screen bg-industrial-900 overflow-hidden relative">
    
    <!-- Mobile Overlay -->
    <div 
      v-if="mobileSidebarOpen" 
      class="fixed inset-0 bg-black/60 z-40 lg:hidden"
      @click="mobileSidebarOpen = false"
    ></div>

    <!-- Sidebar -->
    <aside 
      :class="[
        'fixed lg:static inset-y-0 left-0 z-50 flex flex-col bg-white dark:bg-industrial-800 transition-all duration-300 ease-in-out border-r border-slate-200 dark:border-industrial-border shadow-md',
        collapsed && !mobileSidebarOpen ? 'w-16' : 'w-64',
        mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      ]"
    >
      <Sidebar :collapsed="collapsed && !mobileSidebarOpen" @close-mobile="mobileSidebarOpen = false" />
    </aside>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col min-w-0 bg-slate-100 dark:bg-industrial-900">
      <!-- Topbar -->
      <header class="h-16 flex items-center justify-between px-4 lg:px-6 bg-white dark:bg-industrial-800 border-b border-slate-200 dark:border-industrial-border z-10 shadow-sm">
        <!-- Hamburger / Toggle -->
        <div class="flex items-center">
          <button @click="mobileSidebarOpen = true" class="lg:hidden text-slate-500 hover:text-slate-800 dark:text-slate-300 dark:hover:text-white mr-4 focus:outline-none">
            <el-icon :size="24"><Menu /></el-icon>
          </button>
          <button @click="collapsed = !collapsed" class="hidden lg:block text-slate-500 hover:text-slate-800 dark:text-slate-300 dark:hover:text-white focus:outline-none">
            <el-icon :size="20"><component :is="collapsed ? 'Expand' : 'Fold'" /></el-icon>
          </button>
        </div>

        <!-- Right Side -->
        <div class="flex items-center gap-4">
          <!-- Theme Toggle -->
          <el-switch
            v-model="isDark"
            inline-prompt
            style="--el-switch-on-color: #414868; --el-switch-off-color: #e2e8f0"
            active-text="🌙"
            inactive-text="☀️"
            @change="toggleTheme"
          />

          <el-popover
            v-model:visible="popoverVisible"
            placement="bottom-end"
            :width="320"
            trigger="click"
            popper-style="padding: 0; border-radius: 8px; overflow: hidden;"
          >
            <template #reference>
              <div class="cursor-pointer flex items-center justify-center p-1.5 rounded-full hover:bg-slate-100 dark:hover:bg-industrial-700 transition-colors">
                <el-badge :value="auth.unreadCount" :max="99" :hidden="auth.unreadCount === 0">
                  <el-icon :size="20" class="text-slate-500 dark:text-slate-300"><Bell /></el-icon>
                </el-badge>
              </div>
            </template>
            
            <div class="flex flex-col bg-white dark:bg-industrial-800 text-slate-800 dark:text-slate-200">
              <!-- Header -->
              <div class="px-4 py-2.5 border-b border-slate-100 dark:border-industrial-border flex justify-between items-center bg-slate-50/50 dark:bg-industrial-700/30">
                <span class="text-xs font-bold text-slate-800 dark:text-slate-200">未读通知 ({{ auth.unreadCount }})</span>
                <button 
                  v-if="auth.unreadCount > 0"
                  @click="handleMarkAllRead" 
                  class="text-[11px] text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300 font-medium bg-transparent border-0 cursor-pointer"
                >
                  全部已读
                </button>
              </div>
              
              <!-- Content List -->
              <div class="max-h-60 overflow-y-auto py-1 divide-y divide-slate-100 dark:divide-industrial-border/60">
                <div v-if="auth.unreadNotifications.length === 0" class="py-8 text-center text-slate-400 dark:text-slate-500 text-xs">
                  <el-empty :image-size="40" description="暂无未读通知" />
                </div>
                <div v-else>
                  <div 
                    v-for="item in auth.unreadNotifications" 
                    :key="item.id" 
                    class="p-3 hover:bg-slate-50 dark:hover:bg-industrial-700/50 transition-colors flex flex-col gap-1 cursor-pointer"
                    @click="handleNotificationClick(item)"
                  >
                    <div class="flex items-center gap-1.5">
                      <span class="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0"></span>
                      <span class="text-xs font-semibold text-slate-800 dark:text-slate-100 truncate flex-1">{{ item.title }}</span>
                      <span class="text-[10px] text-slate-400 dark:text-slate-500 shrink-0">{{ formatTimeShort(item.created_at) }}</span>
                    </div>
                    <p class="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 pl-3 m-0 leading-relaxed">{{ item.body }}</p>
                  </div>
                </div>
              </div>
              
              <!-- Footer -->
              <div class="border-t border-slate-100 dark:border-industrial-border p-2 bg-slate-50/30 dark:bg-industrial-700/10 text-center">
                <button 
                  @click="goToNotificationCenter"
                  class="w-full text-xs text-slate-600 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 font-medium py-1.5 rounded hover:bg-slate-100 dark:hover:bg-industrial-700 transition-colors flex items-center justify-center gap-1 bg-transparent border-0 cursor-pointer"
                >
                  <span>通知中心</span>
                  <el-icon :size="12"><ArrowRight /></el-icon>
                </button>
              </div>
            </div>
          </el-popover>
          <el-dropdown trigger="click">
            <span class="cursor-pointer text-slate-800 dark:text-slate-200 flex items-center">
              {{ auth.user?.display_name }}
              <el-icon class="ml-1"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- Main Scrollable Area -->
      <main class="flex-1 overflow-auto p-4 lg:p-6 bg-slate-100 dark:bg-industrial-900 text-slate-800 dark:text-slate-200">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from './stores/auth.js';
import Sidebar from './components/Sidebar.vue';

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();
const collapsed = ref(false);
const mobileSidebarOpen = ref(false);
const isDark = ref(true);

const popoverVisible = ref(false);
let poller = null;

onMounted(() => {
  isDark.value = document.documentElement.classList.contains('dark');
});

// Watch token to start/stop polling
watch(() => auth.token, (newVal) => {
  if (newVal) {
    auth.fetchNotifications();
    if (!poller) {
      poller = setInterval(() => {
        auth.fetchNotifications();
      }, 30000);
    }
  } else {
    if (poller) {
      clearInterval(poller);
      poller = null;
    }
  }
}, { immediate: true });

onUnmounted(() => {
  if (poller) clearInterval(poller);
});

function toggleTheme(val) {
  isDark.value = val;
  if (val) {
    document.documentElement.classList.add('dark');
    localStorage.setItem('theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark');
    localStorage.setItem('theme', 'light');
  }
}

// Close mobile sidebar on route change
watch(() => route.path, () => {
  mobileSidebarOpen.value = false;
});

function handleLogout() { auth.logout(); router.push('/login'); }

function formatTimeShort(val) {
  if (!val) return '';
  return val.slice(5, 16).replace('T', ' '); // returns "MM-DD HH:mm"
}

async function handleNotificationClick(item) {
  popoverVisible.value = false;
  await auth.markNotificationRead(item.id);
  router.push(`/notifications?highlight=${item.id}`);
}

async function handleMarkAllRead() {
  await auth.markAllNotificationsRead();
}

function goToNotificationCenter() {
  popoverVisible.value = false;
  router.push('/notifications');
}
</script>

<style>
/* Tailwind CSS handles all our layouts now! */
</style>
