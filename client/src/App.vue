<template>
  <router-view v-if="$route.meta.guest" />
  <el-container v-else style="min-height:100vh">
    <el-aside :width="collapsed ? '64px' : '220px'" class="sidebar">
      <Sidebar :collapsed="collapsed" @toggle="collapsed = !collapsed" />
    </el-aside>
    <el-container>
      <el-header class="topbar">
        <div class="topbar-right">
          <el-badge :value="0" :hidden="true">
            <el-icon :size="20"><Bell /></el-icon>
          </el-badge>
          <el-dropdown trigger="click">
            <span class="user-name">{{ auth.user?.display_name }}</span>
            <template #dropdown>
              <el-dropdown-item @click="handleLogout">
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-dropdown-item>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from './stores/auth.js';
import Sidebar from './components/Sidebar.vue';

const auth = useAuthStore();
const router = useRouter();
const collapsed = ref(false);

function handleLogout() { auth.logout(); router.push('/login'); }
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
.sidebar { background: #1d1e2c; transition: width 0.2s; overflow: hidden; }
.topbar { background: #fff; border-bottom: 1px solid #e4e7ed; display: flex; align-items: center; justify-content: flex-end; padding: 0 24px; }
.topbar-right { display: flex; align-items: center; gap: 20px; }
.user-name { cursor: pointer; color: #303133; }
.el-main { background: #f5f7fa; padding: 20px; }
</style>
