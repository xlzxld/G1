<template>
  <div>
    <div class="flex items-start sm:items-center justify-between mb-6 flex-col sm:flex-row gap-3">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">通知中心</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">消息通知与自动化规则</p>
      </div>
      <div class="flex gap-2">
        <el-button v-if="auth.canEdit('notifications')" @click="sendVisible = true" type="primary"><el-icon><Promotion /></el-icon> 派发通知</el-button>
        <el-button @click="markAllRead" v-if="unreadCount > 0">全部已读</el-button>
      </div>
    </div>
    <el-timeline v-if="pagedNotifs.length">
      <el-timeline-item v-for="n in pagedNotifs" :key="n.id" :color="n.is_read?'#c0c4cc':'#409eff'" :timestamp="formatDateTime(n.created_at)">
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
            <a v-if="n.link" href="javascript:void(0)" style="color:#409eff;font-size:13px" @click="goToDetail(n)">查看详情</a>
            <el-button v-if="!n.is_read" size="small" text @click="markRead(n.id)">标为已读</el-button>
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>
    <el-empty v-else description="暂无通知" />

    <div v-if="notifs.length > pageSize" class="mt-4 flex justify-end">
      <el-pagination
        background
        layout="total, prev, pager, next"
        :total="notifs.length"
        v-model:current-page="notifPage"
        :page-size="pageSize"
        @current-change="handleNotifPageChange"
      />
    </div>

    <el-dialog v-model="sendVisible" title="派发通知" :width="isMobile ? '95vw' : '440px'">
      <el-form ref="sendFormRef" :model="form" :rules="rules" :label-position="isMobile ? 'top' : 'right'" label-width="70px">
        <el-form-item label="接收人" prop="to_user_id"><el-select v-model="form.to_user_id" filterable placeholder="选择用户" style="width:100%"><el-option v-for="u in users" :key="u.id" :label="`${u.username}`" :value="u.id" /></el-select></el-form-item>
        <el-form-item label="标题" prop="title"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="内容"><el-input v-model="form.body" type="textarea" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="sendVisible=false">取消</el-button><el-button type="primary" @click="doSend" :loading="sending">发送</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import api from '../api/index.js';

const isMobile = ref(window.innerWidth < 768);
function onResize() { isMobile.value = window.innerWidth < 768; }
window.addEventListener('resize', onResize);
onUnmounted(() => window.removeEventListener('resize', onResize));
import { useAuthStore } from '../stores/auth.js';

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();
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
const notifPage = ref(1);
const pageSize = 10;

const pagedNotifs = computed(() => {
  const start = (notifPage.value - 1) * pageSize;
  return notifs.value.slice(start, start + pageSize);
});

// 根据通知 id 计算它在第几页
function getPageOfNotif(id) {
  const idx = notifs.value.findIndex(n => n.id === id);
  if (idx === -1) return 1;
  return Math.floor(idx / pageSize) + 1;
}

function handleNotifPageChange() {
  // 翻页后若有 highlight，检查是否在当前页，若是则滚动
  if (highlightedId.value) {
    setTimeout(() => {
      const el = document.getElementById(`notif-item-${highlightedId.value}`);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
  }
}

onMounted(async () => {
  await fetchNotifs();
  try {
    users.value = (await api.get('/users')).data;
  } catch {}
  
  if (route.query.highlight) {
    const id = parseInt(route.query.highlight);
    highlightedId.value = id;
    notifPage.value = getPageOfNotif(id);
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
    notifPage.value = getPageOfNotif(id);
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
  // 如果服务端下发的是旧格式 /orders/123，可将其转化为新格式 /orders?highlight=123 (备用兼容)
  const orderMatch = link.match(/^\/orders\/(\d+)$/);
  if (orderMatch) {
    return `/orders?highlight=${orderMatch[1]}`;
  }
  const inventoryMatch = link.match(/^\/inventory\/(\d+)$/);
  if (inventoryMatch) {
    return `/inventory?highlight=${inventoryMatch[1]}`;
  }
  return link;
}

async function goToDetail(n) {
  // 先标已读，再跳转，确保目标页面接收到 highlight 参数时数据状态一致
  if (!n.is_read) {
    await markRead(n.id);
  }
  const target = getFriendlyLink(n.link);
  if (!target) return;
  // 解析目标路径与 query
  const [path, queryStr] = target.split('?');
  const query = {};
  if (queryStr) {
    queryStr.split('&').forEach(pair => {
      const [k, v] = pair.split('=');
      if (k) query[k] = v;
    });
  }
  router.push({ path, query });
}
</script>

