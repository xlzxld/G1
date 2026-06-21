<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>通知中心</h2>
      <div>
        <el-button @click="sendVisible = true" type="primary"><el-icon><Promotion /></el-icon> 派发通知</el-button>
        <el-button @click="markAllRead" v-if="unreadCount > 0">全部已读</el-button>
      </div>
    </div>
    <el-timeline v-if="notifs.length">
      <el-timeline-item v-for="n in notifs" :key="n.id" :color="n.is_read?'#c0c4cc':'#409eff'" :timestamp="n.created_at">
        <div style="display:flex;align-items:center;gap:8px">
          <el-tag size="small" :type="n.source==='auto'?'warning':''">{{ n.source==='auto'?'自动':'手动' }}</el-tag>
          <strong>{{ n.title }}</strong>
          <el-tag v-if="!n.is_read" size="small" type="danger" effect="dark">NEW</el-tag>
        </div>
        <p style="color:#909399;margin-top:4px">{{ n.body }}</p>
        <div style="margin-top:4px;display:flex;gap:8px">
          <router-link v-if="n.link" :to="n.link" style="color:#409eff;font-size:13px">查看详情</router-link>
          <el-button v-if="!n.is_read" size="small" text @click="markRead(n.id)">标为已读</el-button>
        </div>
      </el-timeline-item>
    </el-timeline>
    <el-empty v-else description="暂无通知" />

    <el-dialog v-model="sendVisible" title="派发通知" width="440px">
      <el-form label-width="70px">
        <el-form-item label="接收人"><el-select v-model="sendTo" filterable placeholder="选择用户"><el-option v-for="u in users" :key="u.id" :label="`${u.display_name} (${u.username})`" :value="u.id" /></el-select></el-form-item>
        <el-form-item label="标题"><el-input v-model="sendTitle" /></el-form-item>
        <el-form-item label="内容"><el-input v-model="sendBody" type="textarea" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="sendVisible=false">取消</el-button><el-button type="primary" @click="doSend" :loading="sending">发送</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import api from '../api/index.js';

const notifs = ref([]); const unreadCount = ref(0); const users = ref([]);
const sendVisible = ref(false); const sendTo = ref(null); const sendTitle = ref(''); const sendBody = ref(''); const sending = ref(false);

onMounted(async () => { await fetchNotifs(); try { users.value = (await api.get('/users')).data; } catch {} });
async function fetchNotifs() { try { notifs.value = (await api.get('/notifications')).data; unreadCount.value = notifs.value.filter(n=>!n.is_read).length; } catch {} }
async function markRead(id) { await api.put(`/notifications/${id}/read`); await fetchNotifs(); }
async function markAllRead() { await api.put('/notifications/read-all'); await fetchNotifs(); ElMessage.success('全部已读'); }
async function doSend() {
  sending.value = true;
  try { await api.post('/notifications', { to_user_id: sendTo.value, title: sendTitle.value, body: sendBody.value }); sendVisible.value = false; sendTo.value = null; sendTitle.value = ''; sendBody.value = ''; ElMessage.success('已发送'); }
  catch (e) { ElMessage.error(e.response?.data?.error||'发送失败'); } finally { sending.value = false; }
}
</script>
