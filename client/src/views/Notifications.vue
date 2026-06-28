<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">通知中心</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">消息通知与自动化规则</p>
      </div>
      <div>
        <el-button v-if="auth.canEdit('notifications')" @click="sendVisible = true" type="primary"><el-icon><Promotion /></el-icon> 派发通知</el-button>
        <el-button @click="markAllRead" v-if="unreadCount > 0">全部已读</el-button>
      </div>
    </div>
    <el-timeline v-if="notifs.length">
      <el-timeline-item v-for="n in notifs" :key="n.id" :color="n.is_read?'#c0c4cc':'#409eff'" :timestamp="formatDateTime(n.created_at)">
        <div 
          :id="`notif-item-${n.id}`"
          :class="['p-3 rounded-lg transition-all duration-300', highlightedId === n.id ? 'highlight-flash' : '']"
        >
          <div style="display:flex;align-items:center;gap:8px">
            <el-tag size="small" :type="n.source==='auto'?'warning':'info'">{{ n.source==='auto'?'自动':'手动' }}</el-tag>
            <strong>{{ n.title }}</strong>
            <el-tag v-if="!n.is_read" size="small" type="danger" effect="dark">NEW</el-tag>
          </div>
          <p style="color:#909399;margin-top:4px">{{ n.body }}</p>
          <div style="margin-top:4px;display:flex;gap:8px">
            <router-link v-if="n.link" :to="getFriendlyLink(n.link)" style="color:#409eff;font-size:13px">查看详情</router-link>
            <el-button v-if="!n.is_read" size="small" text @click="markRead(n.id)">标为已读</el-button>
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>
    <el-empty v-else description="暂无通知" />

    <el-dialog v-model="sendVisible" title="派发通知" width="440px">
      <el-form ref="sendFormRef" :model="form" :rules="rules" label-width="70px">
        <el-form-item label="接收人" prop="to_user_id"><el-select v-model="form.to_user_id" filterable placeholder="选择用户"><el-option v-for="u in users" :key="u.id" :label="`${u.username}`" :value="u.id" /></el-select></el-form-item>
        <el-form-item label="标题" prop="title"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="内容"><el-input v-model="form.body" type="textarea" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="sendVisible=false">取消</el-button><el-button type="primary" @click="doSend" :loading="sending">发送</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import api from '../api/index.js';
import { useAuthStore } from '../stores/auth.js';

const auth = useAuthStore();
const route = useRoute();
const notifs = computed(() => auth.notifications);
const unreadCount = computed(() => auth.unreadCount);
const users = ref([]);
const sendVisible = ref(false); const sending = ref(false);
const sendFormRef = ref(null);
const form = reactive({ to_user_id: null, title: '', body: '' });
const rules = {
  to_user_id: [{ required: true, message: '请选择接收人', trigger: 'change' }],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }]
};

const highlightedId = ref(null);

onMounted(async () => {
  await fetchNotifs();
  try {
    users.value = (await api.get('/users')).data;
  } catch {}
  
  if (route.query.highlight) {
    const id = parseInt(route.query.highlight);
    highlightedId.value = id;
    setTimeout(() => {
      const el = document.getElementById(`notif-item-${id}`);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 300);
  }
});

watch(() => route.query.highlight, (newVal) => {
  if (newVal) {
    const id = parseInt(newVal);
    highlightedId.value = id;
    setTimeout(() => {
      const el = document.getElementById(`notif-item-${id}`);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
  } else {
    highlightedId.value = null;
  }
});

async function fetchNotifs() { await auth.fetchNotifications(); }
async function markRead(id) { await auth.markNotificationRead(id); }
async function markAllRead() { await auth.markAllNotificationsRead(); ElMessage.success('全部已读'); }
async function doSend() {
  if (!sendFormRef.value) return;
  await sendFormRef.value.validate(async (valid) => {
    if (!valid) return;
    sending.value = true;
    try {
      await api.post('/notifications', form);
      sendVisible.value = false;
      form.to_user_id = null;
      form.title = '';
      form.body = '';
      ElMessage.success('已发送');
      await fetchNotifs();
    }
    catch (e) { ElMessage.error(e.response?.data?.error||e.response?.data?.detail||'发送失败'); } finally { sending.value = false; }
  });
}
function formatDateTime(val) {
  if (!val) return '—';
  return val.slice(0, 16).replace('T', ' ');
}
function getFriendlyLink(link) {
  if (!link) return '';
  // 兼容老数据：如果 link 为 /orders/123，自动转换为列表页高亮形式 /orders?highlight=123
  const orderMatch = link.match(/^\/orders\/(\d+)$/);
  if (orderMatch) {
    return `/orders?highlight=${orderMatch[1]}`;
  }
  return link;
}
</script>

<style scoped>
@keyframes flash {
  0%, 100% {
    background-color: transparent;
  }
  25%, 75% {
    background-color: rgba(64, 158, 255, 0.25);
    box-shadow: 0 0 12px rgba(64, 158, 255, 0.3);
  }
}
.highlight-flash {
  animation: flash 1.2s ease-in-out 3;
  border: 1px solid rgba(64, 158, 255, 0.4);
}
</style>
