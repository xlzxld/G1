<template>
  <div class="min-h-screen bg-slate-100 dark:bg-industrial-900 text-slate-800 dark:text-slate-200 p-6 font-sans">
    <div v-if="order" class="max-w-7xl mx-auto space-y-6">
      
      <!-- Top Header Area -->
      <div class="flex justify-between items-center mb-4 border-b border-slate-200 dark:border-industrial-border pb-4">
        <div>
          <h1 class="text-3xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">订单详情 <span class="text-blue-600 dark:text-industrial-accent">#{{ order.order_no }}</span></h1>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">实时生产进度与工程图纸管理</p>
        </div>
        <div class="flex gap-3">
          <button v-if="(isAdmin || auth.canEdit('orders')) && order.status === 'in_progress'" @click="setOrderStatus('paused')" class="px-4 py-2 bg-yellow-600/20 text-yellow-500 border border-yellow-600/50 rounded hover:bg-yellow-600/30 transition shadow-sm">暂停生产</button>
          <button v-if="(isAdmin || auth.canEdit('orders')) && order.status === 'paused'" @click="setOrderStatus('in_progress')" class="px-4 py-2 bg-green-600/20 text-green-500 border border-green-600/50 rounded hover:bg-green-600/30 transition shadow-sm">恢复生产</button>
          <router-link v-if="route.query.from_customer" :to="`/customers/${route.query.from_customer}`" class="px-4 py-2 bg-blue-50 dark:bg-industrial-800 text-blue-600 dark:text-blue-300 border border-blue-200 dark:border-industrial-border rounded hover:bg-blue-100 dark:hover:bg-industrial-700 transition shadow-sm">返回客户详情</router-link>
          <router-link to="/orders" class="px-4 py-2 bg-slate-100 dark:bg-industrial-800 text-slate-800 dark:text-slate-300 border border-slate-300 dark:border-industrial-border rounded hover:bg-slate-200 dark:hover:bg-industrial-700 transition shadow-sm">返回订单列表</router-link>
        </div>
      </div>

      <!-- Bento Grid System -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
        
        <!-- Left Column: Order Meta & Status (Span 1) -->
        <div class="lg:col-span-1 flex flex-col space-y-6">
          <!-- Meta Info Card -->
          <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-5 shadow-lg backdrop-blur-sm relative overflow-hidden">
            <div class="absolute top-0 left-0 w-1 h-full bg-industrial-accent"></div>
            <h2 class="text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 mb-4 font-semibold">基本信息</h2>
            <div class="space-y-4 text-sm">
              <div class="flex justify-between items-center border-b border-slate-200 dark:border-industrial-700 pb-2">
                <span class="text-slate-500 dark:text-slate-400">产品名称</span>
                <span class="font-medium text-slate-800 dark:text-slate-200">{{ order.product_name }}</span>
              </div>
              <div class="border-b border-slate-200 dark:border-industrial-700 pb-2">
                <div class="flex justify-between items-center mb-1">
                  <span class="text-slate-500 dark:text-slate-400">客户</span>
                  <span class="font-medium text-slate-800 dark:text-slate-200">{{ order.customer_name || '—' }}</span>
                </div>
                <div v-if="order.customer && (order.customer.contact || order.customer.phone || order.customer.wechat || order.customer.address)" class="text-xs text-slate-500 mt-2 bg-slate-50 dark:bg-industrial-900/50 p-2 rounded">
                  <div v-if="order.customer.contact" class="flex justify-between mb-1"><span class="text-slate-400">联系人：</span><span class="text-right">{{ order.customer.contact }}</span></div>
                  <div v-if="order.customer.phone" class="flex justify-between mb-1"><span class="text-slate-400">电话：</span><span class="text-right">{{ order.customer.phone }}</span></div>
                  <div v-if="order.customer.wechat" class="flex justify-between mb-1"><span class="text-slate-400">微信：</span><span class="text-right">{{ order.customer.wechat }}</span></div>
                  <div v-if="order.customer.address" class="flex justify-between"><span class="text-slate-400">地址：</span><span class="text-right break-words max-w-[150px]">{{ order.customer.address }}</span></div>
                </div>
              </div>
              <div class="flex justify-between items-center border-b border-slate-200 dark:border-industrial-700 pb-2">
                <span class="text-slate-500 dark:text-slate-400">优先级</span>
                <span :class="prioClass(order.priority)" class="px-2 py-0.5 rounded text-xs font-bold">{{ ['普通','紧急','特急'][order.priority] || '普通' }}</span>
              </div>
              <div class="flex justify-between items-center border-b border-slate-200 dark:border-industrial-700 pb-2">
                <span class="text-slate-500 dark:text-slate-400">交付日期</span>
                <span class="font-medium text-slate-800 dark:text-slate-200">{{ order.shipment_date?.slice(0, 10) || '待定' }}</span>
              </div>
              <div>
                <span class="text-slate-500 dark:text-slate-400 block mb-1">工程备注</span>
                <p class="text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-industrial-900/50 p-2 rounded border border-slate-200 dark:border-industrial-700 text-xs leading-relaxed">{{ order.notes || '暂无备注信息。' }}</p>
              </div>
            </div>
          </div>

          <!-- Materials Info Card (Left Bottom) -->
          <OrderMaterials
            v-if="order"
            :order-id="order.id"
            :order-status="order.status"
            class="flex-1"
          />
        </div>

        <!-- Middle & Right Column: Process Engine (Span 2) -->
        <div class="lg:col-span-2">
          <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-5 shadow-lg h-full flex flex-col">
            <div class="flex justify-between items-center mb-6">
              <h2 class="text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 font-semibold flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                生产流转时间线
              </h2>
              <span :class="statusBadge(order.status)" class="px-3 py-1 rounded-full text-xs font-bold border">{{ statusLabel(order.status) }}</span>
            </div>
            
            <div class="flex-1 overflow-auto pr-2">
              <div v-if="order.steps?.length" class="relative border-l-2 border-slate-200 dark:border-industrial-700 ml-4 space-y-8 pb-4">
                <div v-for="(step, idx) in order.steps" :key="step.id" class="relative pl-8">
                  <!-- Timeline Node -->
                  <div :class="nodeColor(step)" class="absolute -left-[9px] w-4 h-4 rounded-full border-2 border-industrial-800 z-10 transition-colors" style="top: 26px;"></div>
                  
                  <div class="bg-slate-50 dark:bg-industrial-900/50 border border-slate-200 dark:border-industrial-700 rounded-xl p-5 hover:border-blue-400 dark:hover:border-industrial-accent transition-colors group shadow-sm">
                    <div class="flex justify-between items-start">
                      <div>
                        <div class="flex items-center gap-3 mb-1.5">
                          <span class="text-xl font-bold text-slate-800 dark:text-slate-200 group-hover:text-blue-500 dark:group-hover:text-industrial-accent transition-colors">{{ idx + 1 }}. {{ step.name }}</span>
                          <span v-if="step.required" class="px-2 py-0.5 rounded text-[10px] font-bold bg-red-900/40 text-red-400 border border-red-800">必做</span>
                          <span v-if="step.outsourced" class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-900/40 text-indigo-400 border border-indigo-800">外协</span>
                        </div>
                        <div class="text-sm text-slate-600 dark:text-slate-400 flex items-center gap-2 font-medium">
                          <span>负责人: {{ step.assignee || '未分配' }}</span>
                          <span v-if="completionInfo(step)">• {{ completionInfo(step) }}</span>
                        </div>
                      </div>
                      
                      <!-- Action Panel for Active Step -->
                      <div v-if="canAct(step) && auth.canEdit('orders')" class="flex gap-2">
                        <button v-if="step.status !== 'completed'" @click="doAdvance(step)" class="px-4 py-2 bg-blue-50 dark:bg-industrial-accent/20 text-blue-600 dark:text-industrial-accent border border-blue-200 dark:border-industrial-accent/50 rounded-lg hover:bg-blue-600 hover:text-white dark:hover:bg-industrial-accent dark:hover:text-industrial-900 transition text-xs font-bold shadow-sm">完成工序</button>
                        <button v-if="step.status === 'completed'" @click="doRollback(step)" class="px-4 py-2 bg-red-500/10 text-red-500 border border-red-500/30 rounded-lg hover:bg-red-500/20 transition text-xs font-medium shadow-sm">撤回</button>
                        <button v-if="!step.required && step.status === 'pending'" @click="doSkip(step)" class="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition text-xs font-medium shadow-sm">跳过</button>
                      </div>
                      <div v-else>
                        <span :class="stepBadgeText(step)" class="text-xs font-bold uppercase tracking-wider">{{ step.status }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="text-center text-slate-500 py-10">此订单暂无工艺流程。</div>
            </div>
          </div>
        </div>

      </div>

      <!-- Bottom Full Width: Drawing Panel Component (Moved outside of the grid to prevent layout overlapping) -->
      <div class="mt-6">
        <DrawingPanel
          v-if="order"
          :order-id="order.id"
          :order-no="order.order_no"
          :documents="order.documents || []"
          @refresh="fetchOrder"
        />
      </div>
    </div>
    
    <!-- Image Preview Modal (legacy fullscreen, kept for order steps) -->
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useAuthStore } from '../stores/auth.js';
import api from '../api/index.js';
import DrawingPanel from '../components/DrawingPanel.vue';
import OrderMaterials from '../components/OrderMaterials.vue';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const order = ref(null);
const isAdmin = auth.isAdmin;

onMounted(fetchOrder);

async function fetchOrder() { 
  try { 
    const r = await api.get(`/orders/${route.params.id}`); 
    order.value = r.data; 
    // Fallback if API doesn't return documents array yet
    if (!order.value.documents) order.value.documents = [];
  } catch (e) {
    console.error("Fetch failed", e);
    ElMessage.error("该订单已不存在或已被删除！");
    router.push('/orders');
  } 
}

// Visual Helpers
function nodeColor(s) { 
  if (s.status === 'completed') return 'bg-industrial-accent border-industrial-900 shadow-[0_0_10px_rgba(56,189,248,0.8)]'; 
  if (s.status === 'in_progress') return 'bg-blue-500 border-industrial-900 shadow-[0_0_10px_rgba(59,130,246,0.6)] animate-pulse'; 
  if (s.status === 'skipped') return 'bg-slate-600 border-slate-800'; 
  return 'bg-industrial-700 border-industrial-800'; 
}

function stepBadgeText(s) {
  if (s.status === 'completed') return 'text-industrial-accent';
  if (s.status === 'skipped') return 'text-slate-500';
  return 'text-slate-600';
}

function statusBadge(s) {
  if (s === 'completed') return 'bg-industrial-accent/10 text-industrial-accent border-industrial-accent/50 shadow-[0_0_8px_rgba(56,189,248,0.3)]';
  if (s === 'paused') return 'bg-red-500/10 text-red-400 border-red-500/50';
  if (s === 'in_progress') return 'bg-blue-500/10 text-blue-400 border-blue-500/50';
  return 'bg-slate-700 text-slate-300 border-slate-600';
}

function prioClass(p) { 
  return p === 2 ? 'bg-red-900/40 text-red-400 border border-red-800' : 
         p === 1 ? 'bg-orange-900/40 text-orange-400 border border-orange-800' : 
         'bg-slate-800 text-slate-400 border border-slate-700'; 
}

function statusLabel(s) {
  const m = { in_progress: '进行中', completed: '已完成', paused: '暂停' };
  return m[s] || (s ? s.toUpperCase() : '');
}

function completionInfo(s) { 
  if (s.completed_at) return `完成于：${formatDateTime(s.completed_at)}`; 
  if (s.started_at) return `开始于：${formatDateTime(s.started_at)}`; 
  return ''; 
}

function canAct(s) { return s.status === 'pending' || s.status === 'in_progress' || s.status === 'completed'; }

// Actions
async function doAdvance(step) {
  try { await api.post(`/orders/${order.value.id}/steps/${step.id}/advance`); await fetchOrder(); ElMessage.success('工序已完成'); }
  catch (e) { ElMessage.error(e.response?.data?.error || '操作失败'); }
}
async function doRollback(step) {
  try { await api.post(`/orders/${order.value.id}/steps/${step.id}/rollback`); await fetchOrder(); ElMessage.success('已撤回'); }
  catch (e) { ElMessage.error(e.response?.data?.error || '操作失败'); }
}
async function doSkip(step) {
  try { await api.post(`/orders/${order.value.id}/steps/${step.id}/skip`); await fetchOrder(); ElMessage.success('工序已跳过'); }
  catch (e) { ElMessage.error(e.response?.data?.error || '操作失败'); }
}
async function setOrderStatus(status) {
  try {
    const statusText = status === 'paused' ? '暂停' : '进行中';
    await ElMessageBox.confirm(`确定要将订单状态更改为 ${statusText} 吗？`, '确认', { type: 'warning' });
    await api.put(`/orders/${order.value.id}/status`, { status });
    await fetchOrder();
    ElMessage.success('状态已更新');
  } catch {}
}

function formatDateTime(val) {
  if (!val) return '—';
  return val.slice(0, 16).replace('T', ' ');
}
</script>

<style scoped>
/* Any highly custom styles that Tailwind can't easily express */
.backdrop-blur {
  backdrop-filter: blur(8px);
}
</style>
