<template>
  <div v-if="order">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>订单 {{ order.order_no }}</h2>
      <div>
        <el-button @click="forceStatusVisible = true" v-if="isAdmin">强制改状态</el-button>
        <router-link to="/orders"><el-button>返回列表</el-button></router-link>
      </div>
    </div>
    <el-descriptions border :column="3">
      <el-descriptions-item label="订单号">{{ order.order_no }}</el-descriptions-item>
      <el-descriptions-item label="产品名称">{{ order.product_name }}</el-descriptions-item>
      <el-descriptions-item label="客户">{{ order.customer_name || '—' }}</el-descriptions-item>
      <el-descriptions-item label="状态"><el-tag :type="statusType(order.status)">{{ order.status }}</el-tag></el-descriptions-item>
      <el-descriptions-item label="优先级"><el-tag :type="prioType(order.priority)">{{ ['普通','紧急','特急'][order.priority] || '普通' }}</el-tag></el-descriptions-item>
      <el-descriptions-item label="交货日期">{{ order.shipment_date || '—' }}</el-descriptions-item>
    </el-descriptions>

    <el-divider />
    <h3 style="margin-bottom:12px">工序进度</h3>
    <el-timeline v-if="order.steps?.length">
      <el-timeline-item
        v-for="(step, idx) in order.steps" :key="step.id"
        :color="stepColor(step)" :timestamp="completionInfo(step)"
        placement="top"
      >
        <div style="display:flex;align-items:center;gap:12px">
          <el-tag :type="stepTagType(step)" size="small">{{ stepStatusLabel(step) }}</el-tag>
          <strong>{{ idx + 1 }}. {{ step.name }}</strong>
          <el-tag v-if="step.required" type="danger" size="small" effect="plain">必做</el-tag>
          <el-tag v-if="step.outsourced" size="small" effect="plain" type="info">外协</el-tag>
        </div>
        <div style="margin-top:6px" v-if="step.assignee">负责人: {{ step.assignee }}</div>
        <div style="margin-top:6px;display:flex;gap:8px" v-if="canAct(step)">
          <el-button size="small" type="primary" @click="doAdvance(step)">完成</el-button>
          <el-button v-if="step.status === 'completed'" size="small" @click="doRollback(step)">退回</el-button>
          <el-button v-if="!step.required && step.status === 'pending'" size="small" type="warning" @click="doSkip(step)">跳过</el-button>
        </div>
      </el-timeline-item>
    </el-timeline>
    <el-empty v-else description="暂无工序" />

    <el-dialog v-model="forceStatusVisible" title="强制修改状态" width="300px">
      <el-select v-model="forceStatus" placeholder="选择状态">
        <el-option label="草稿" value="draft" /><el-option label="进行中" value="in_progress" /><el-option label="客户确认" value="customer_confirm" /><el-option label="已完成" value="completed" /><el-option label="暂停" value="paused" />
      </el-select>
      <template #footer>
        <el-button @click="forceStatusVisible = false">取消</el-button>
        <el-button type="primary" @click="doForceStatus">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useAuthStore } from '../stores/auth.js';
import api from '../api/index.js';

const route = useRoute();
const auth = useAuthStore();
const order = ref(null);
const forceStatusVisible = ref(false);
const forceStatus = ref('');
const isAdmin = auth.isAdmin;

onMounted(fetchOrder);
async function fetchOrder() { try { const r = await api.get(`/orders/${route.params.id}`); order.value = r.data; } catch {} }

function stepColor(s) { if (s.status === 'completed') return '#67c23a'; if (s.status === 'in_progress') return '#409eff'; if (s.status === 'skipped') return '#909399'; return '#c0c4cc'; }
function stepTagType(s) { if (s.status === 'completed') return 'success'; if (s.status === 'in_progress') return ''; if (s.status === 'skipped') return 'info'; return ''; }
function stepStatusLabel(s) { const m = { pending: '待执行', in_progress: '进行中', completed: '已完成', skipped: '已跳过' }; return m[s.status] || s.status; }
function completionInfo(s) { if (s.completed_at) return `完成于 ${s.completed_at}`; if (s.started_at) return `开始于 ${s.started_at}`; return ''; }
function canAct(s) { return s.status === 'pending' || s.status === 'in_progress' || s.status === 'completed'; }

async function doAdvance(step) {
  try { await api.post(`/orders/${order.value.id}/steps/${step.id}/advance`); await fetchOrder(); ElMessage.success('已完成'); }
  catch (e) { ElMessage.error(e.response?.data?.error || '操作失败'); }
}
async function doRollback(step) {
  try { await api.post(`/orders/${order.value.id}/steps/${step.id}/rollback`); await fetchOrder(); ElMessage.success('已退回'); }
  catch (e) { ElMessage.error(e.response?.data?.error || '操作失败'); }
}
async function doSkip(step) {
  try { await api.post(`/orders/${order.value.id}/steps/${step.id}/skip`); await fetchOrder(); ElMessage.success('已跳过'); }
  catch (e) { ElMessage.error(e.response?.data?.error || '操作失败'); }
}
async function doForceStatus() {
  try { await api.put(`/orders/${order.value.id}/status`, { status: forceStatus.value }); forceStatusVisible.value = false; await fetchOrder(); ElMessage.success('状态已更新'); }
  catch (e) { ElMessage.error(e.response?.data?.error || '操作失败'); }
}

function statusType(s) { if (s === 'completed') return 'success'; if (s === 'paused') return 'danger'; if (s === 'draft') return 'info'; return 'warning'; }
function prioType(p) { return p === 2 ? 'danger' : p === 1 ? 'warning' : 'info'; }
</script>
