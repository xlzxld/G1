<template>
  <div v-if="order">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>订单 {{ order.order_no }}</h2>
      <div style="display:flex;gap:8px">
        <el-button v-if="isAdmin" @click="setOrderStatus('paused')" type="warning" :disabled="order.status==='paused'||order.status==='terminated'||order.status==='completed'">暂停</el-button>
        <el-button v-if="isAdmin" @click="setOrderStatus('terminated')" type="danger" :disabled="order.status==='terminated'">终止</el-button>
        <router-link to="/orders"><el-button>返回列表</el-button></router-link>
      </div>
    </div>
    <el-descriptions border :column="3">
      <el-descriptions-item label="订单号">{{ order.order_no }}</el-descriptions-item>
      <el-descriptions-item label="产品名称">{{ order.product_name }}</el-descriptions-item>
      <el-descriptions-item label="客户">{{ order.customer_name || '—' }}</el-descriptions-item>
      <el-descriptions-item label="状态"><el-tag :type="statusType(order.status)">{{ statusLabel(order.status) }}</el-tag></el-descriptions-item>
      <el-descriptions-item label="优先级"><el-tag :type="prioType(order.priority)">{{ ['普通','紧急','特急'][order.priority] || '普通' }}</el-tag></el-descriptions-item>
      <el-descriptions-item label="交货日期">{{ order.shipment_date || '—' }}</el-descriptions-item>
      <el-descriptions-item label="备注" :span="3">{{ order.notes || '—' }}</el-descriptions-item>
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
async function setOrderStatus(status) {
  const label = { paused: '暂停', terminated: '终止' }[status];
  try {
    await ElMessageBox.confirm(`确定将订单状态改为「${label}」？`, '确认', { type: 'warning' });
    await api.put(`/orders/${order.value.id}/status`, { status });
    await fetchOrder();
    ElMessage.success('状态已更新');
  } catch {}
}

function statusLabel(s) {
  const m = { draft: '草稿', in_progress: '进行中', progress: '进行中', completed: '已完成', paused: '暂停', terminated: '终止' };
  return m[s] || s;
}
function statusType(s) { if (s === 'completed') return 'success'; if (s === 'paused' || s === 'terminated') return 'danger'; if (s === 'in_progress' || s === 'progress') return 'warning'; return 'info'; }
function prioType(p) { return p === 2 ? 'danger' : p === 1 ? 'warning' : 'info'; }
</script>
import { ElMessage, ElMessageBox } from 'element-plus';
