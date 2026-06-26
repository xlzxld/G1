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

          <el-badge :value="0" :hidden="true">
            <el-icon :size="20" class="text-slate-500 dark:text-slate-300"><Bell /></el-icon>
          </el-badge>
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
import { ref, watch, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from './stores/auth.js';
import Sidebar from './components/Sidebar.vue';

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();
const collapsed = ref(false);
const mobileSidebarOpen = ref(false);

const isDark = ref(true);

onMounted(() => {
  isDark.value = document.documentElement.classList.contains('dark');
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
</script>

<style>
/* Tailwind CSS handles all our layouts now! */
</style>
