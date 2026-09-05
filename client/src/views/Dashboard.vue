<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">运营驾驶舱</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
          今天什么会出事 · 每 60 秒自动刷新
          <span v-if="lastUpdated" class="ml-2 text-xs">（更新于 {{ lastUpdated }}）</span>
        </p>
      </div>
      <el-button size="small" @click="fetchStats()" :loading="loading">立即刷新</el-button>
    </div>

    <template v-if="loadError">
      <el-alert type="error" :closable="false" :title="'驾驶舱加载失败：' + loadError">
        <el-button size="small" class="mt-2" @click="fetchStats()">重试</el-button>
      </el-alert>
    </template>

    <!-- 指标带 -->
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4" v-loading="loading">
      <div v-for="card in cards" :key="card.key" @click="cardClick(card)"
        :class="['bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-5 flex flex-col justify-center items-center transition-all duration-200 shadow-sm',
          card.link ? 'cursor-pointer hover:bg-slate-50 dark:hover:bg-industrial-700/50 hover:border-blue-400 hover:-translate-y-1 shadow-lg' : '']">
        <div :class="['text-3xl font-black mb-2', card.colorClass || 'text-industrial-accent']">{{ card.value }}</div>
        <div class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider text-center">
          {{ card.label }}
        </div>
        <div class="text-[10px] text-slate-400 mt-1 text-center leading-tight">{{ card.hint }}</div>
      </div>
    </div>

    <!-- 风险清单：第一屏回答"今天什么会出事" -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- 缺料风险 -->
      <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl shadow-sm">
        <div class="px-5 py-3.5 border-b border-slate-200 dark:border-industrial-border flex items-center justify-between bg-slate-50/60 dark:bg-industrial-900/50 rounded-t-xl">
          <h3 class="font-semibold text-slate-800 dark:text-slate-200">
            <span class="inline-block w-2 h-2 rounded-full bg-red-500 mr-2"></span>缺料风险
          </h3>
          <el-tag v-if="risks.low_stock.count" type="danger" size="small">{{ risks.low_stock.count }}</el-tag>
        </div>
        <div class="divide-y divide-slate-100 dark:divide-industrial-border/60 max-h-64 overflow-y-auto">
          <router-link v-for="it in risks.low_stock.items" :key="it.id" :to="`/inventory?highlight=${it.id}`"
            class="px-5 py-2.5 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-industrial-700/30">
            <span class="text-sm text-slate-700 dark:text-slate-300">{{ it.name }}</span>
            <span class="text-xs font-mono"><span class="text-red-500 font-bold">可用 {{ it.available }}</span><span class="text-slate-400"> / 安全 {{ it.min_stock }} {{ it.unit }}</span></span>
          </router-link>
          <div v-if="!risks.low_stock.count" class="px-5 py-6 text-center text-sm text-slate-400">无缺料风险 ✓</div>
        </div>
      </div>

      <!-- 逾期订单 -->
      <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl shadow-sm">
        <div class="px-5 py-3.5 border-b border-slate-200 dark:border-industrial-border flex items-center justify-between bg-slate-50/60 dark:bg-industrial-900/50 rounded-t-xl">
          <h3 class="font-semibold text-slate-800 dark:text-slate-200">
            <span class="inline-block w-2 h-2 rounded-full bg-orange-500 mr-2"></span>逾期订单
          </h3>
          <el-tag v-if="risks.overdue_orders.count" type="danger" size="small">{{ risks.overdue_orders.count }}</el-tag>
        </div>
        <div class="divide-y divide-slate-100 dark:divide-industrial-border/60 max-h-64 overflow-y-auto">
          <router-link v-for="it in risks.overdue_orders.items" :key="it.id" :to="`/orders?highlight=${it.id}`"
            class="px-5 py-2.5 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-industrial-700/30">
            <span class="text-sm text-slate-700 dark:text-slate-300 font-mono">{{ it.order_no }} <span class="font-sans text-slate-400">{{ it.product_name }}</span></span>
            <span class="text-xs text-red-500 font-bold">逾期 {{ it.days }} 天</span>
          </router-link>
          <div v-if="!risks.overdue_orders.count" class="px-5 py-6 text-center text-sm text-slate-400">无逾期 ✓</div>
        </div>
      </div>

      <!-- 停滞工序 -->
      <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl shadow-sm">
        <div class="px-5 py-3.5 border-b border-slate-200 dark:border-industrial-border flex items-center justify-between bg-slate-50/60 dark:bg-industrial-900/50 rounded-t-xl">
          <h3 class="font-semibold text-slate-800 dark:text-slate-200">
            <span class="inline-block w-2 h-2 rounded-full bg-yellow-500 mr-2"></span>停滞工序（&gt; 3 天未完成）
          </h3>
          <el-tag v-if="risks.stalled_steps.count" type="warning" size="small">{{ risks.stalled_steps.count }}</el-tag>
        </div>
        <div class="divide-y divide-slate-100 dark:divide-industrial-border/60 max-h-64 overflow-y-auto">
          <router-link v-for="it in risks.stalled_steps.items" :key="it.step_id" :to="`/orders/${it.order_id}`"
            class="px-5 py-2.5 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-industrial-700/30">
            <span class="text-sm text-slate-700 dark:text-slate-300 font-mono">{{ it.order_no }} <span class="font-sans text-slate-400">{{ it.step_name }}</span></span>
            <span class="text-xs text-yellow-600 font-bold">已 {{ it.days }} 天</span>
          </router-link>
          <div v-if="!risks.stalled_steps.count" class="px-5 py-6 text-center text-sm text-slate-400">无停滞 ✓</div>
        </div>
      </div>

      <!-- 已完成未领料 -->
      <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl shadow-sm">
        <div class="px-5 py-3.5 border-b border-slate-200 dark:border-industrial-border flex items-center justify-between bg-slate-50/60 dark:bg-industrial-900/50 rounded-t-xl">
          <h3 class="font-semibold text-slate-800 dark:text-slate-200">
            <span class="inline-block w-2 h-2 rounded-full bg-blue-500 mr-2"></span>已完成未领料
          </h3>
          <el-tag v-if="risks.completed_unpicked.count" type="info" size="small">{{ risks.completed_unpicked.count }}</el-tag>
        </div>
        <div class="divide-y divide-slate-100 dark:divide-industrial-border/60 max-h-64 overflow-y-auto">
          <router-link v-for="it in risks.completed_unpicked.items" :key="it.order_id" :to="`/orders/${it.order_id}`"
            class="px-5 py-2.5 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-industrial-700/30">
            <span class="text-sm text-slate-700 dark:text-slate-300 font-mono">{{ it.order_no }} <span class="font-sans text-slate-400">{{ it.product_name }}</span></span>
            <span class="text-xs text-slate-500">{{ it.materials }} 项预留未领</span>
          </router-link>
          <div v-if="!risks.completed_unpicked.count" class="px-5 py-6 text-center text-sm text-slate-400">无遗留预留 ✓</div>
        </div>
      </div>
    </div>

    <!-- 趋势带：近 14 天完成订单（CSS 柱图，零依赖） -->
    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl shadow-sm p-5">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-semibold text-slate-800 dark:text-slate-200">近 14 天完成订单</h3>
        <span class="text-xs text-slate-400">合计 {{ trendTotal }} 单</span>
      </div>
      <div class="flex items-end gap-1.5 h-28" v-if="trendTotal > 0">
        <div v-for="t in stats.trend" :key="t.date" class="flex-1 flex flex-col items-center justify-end h-full group">
          <span class="text-[10px] text-slate-400 mb-1 opacity-0 group-hover:opacity-100">{{ t.completed }}</span>
          <div class="w-full rounded-t bg-industrial-accent/70 hover:bg-industrial-accent transition-colors"
            :style="{ height: (trendMax > 0 ? (t.completed / trendMax) * 100 : 0) + '%', minHeight: t.completed > 0 ? '4px' : '1px' }"></div>
          <span class="text-[9px] text-slate-400 mt-1 rotate-45 origin-top-left translate-y-2">{{ t.date }}</span>
        </div>
      </div>
      <div v-else class="py-8 text-center text-sm text-slate-400">
        近 14 天暂无完成订单——趋势数据基于订单完成记录
      </div>
      <div class="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-center" v-if="risks.due_soon.count">
        <div class="col-span-full text-left text-xs text-slate-400 mb-1">交期临近（3 天内 {{ risks.due_soon.count }} 单）：</div>
        <router-link v-for="it in risks.due_soon.items" :key="it.id" :to="`/orders?highlight=${it.id}`"
          class="text-xs bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400 rounded px-2 py-1 hover:bg-orange-100">
          {{ it.order_no }} · {{ it.days }}天后
        </router-link>
      </div>
    </div>

    <!-- 最近新增客户 -->
    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl overflow-hidden shadow-sm" v-if="stats.recent_customers?.length">
      <div class="px-6 py-4 border-b border-slate-200 dark:border-industrial-border bg-slate-50 dark:bg-industrial-900/50">
        <h3 class="text-slate-800 dark:text-slate-200 font-semibold">最近新增客户</h3>
      </div>
      <div class="divide-y divide-slate-200 dark:divide-industrial-border">
        <div v-for="c in stats.recent_customers" :key="c.id" class="px-6 py-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-industrial-700/30 transition-colors">
          <div class="flex items-center space-x-4">
            <router-link :to="`/customers/${c.id}`" class="text-industrial-accent font-medium hover:underline">{{ c.name }}</router-link>
            <span class="text-sm text-slate-400">{{ c.contact }}</span>
          </div>
          <span class="text-xs text-slate-500 font-mono">{{ c.created_at?.slice(0,10) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api/index.js';

const router = useRouter();
const loading = ref(false);
const loadError = ref('');
const lastUpdated = ref('');
let pollTimer = null;

const stats = reactive({
  today_pending: 0, in_progress: 0, inventory_alert: 0, today_done: 0,
  recent_customers: [], risks: null, trend: [],
});

const risks = computed(() => stats.risks || {
  overdue_orders: { count: 0, items: [] }, due_soon: { count: 0, items: [] },
  low_stock: { count: 0, items: [] }, stalled_steps: { count: 0, items: [] },
  completed_unpicked: { count: 0, items: [] },
});
const trendMax = computed(() => Math.max(1, ...(stats.trend || []).map(t => t.completed)));
const trendTotal = computed(() => (stats.trend || []).reduce((a, t) => a + t.completed, 0));

const cards = computed(() => [
  { key: 'pending', label: '待处理订单', value: stats.today_pending, link: '/orders?status=paused', colorClass: 'text-industrial-accent', hint: '暂停中的订单' },
  { key: 'progress', label: '生产中', value: stats.in_progress, link: '/orders?status=in_progress', colorClass: 'text-industrial-orange', hint: '进行中订单' },
  { key: 'alert', label: '库存预警', value: stats.inventory_alert, link: '/inventory', colorClass: stats.inventory_alert > 0 ? 'text-red-500' : 'text-slate-400', hint: '可用 ≤ 安全库存' },
  { key: 'done', label: '今日完成', value: stats.today_done, link: '/orders?status=completed', colorClass: 'text-green-500', hint: '按完成时间' },
]);

async function fetchStats(silent = false) {
  if (!silent) loading.value = true;
  try {
    const r = await api.get('/dashboard/stats');
    Object.assign(stats, r.data);
    loadError.value = '';
    lastUpdated.value = new Date().toLocaleTimeString('zh-CN', { hour12: false });
  } catch (e) {
    loadError.value = e.response?.data?.error || e.response?.data?.detail || e.message || '网络异常';
  } finally { loading.value = false; }
}

function cardClick(card) { if (card.link) router.push(card.link); }

onMounted(() => {
  fetchStats();
  pollTimer = setInterval(() => fetchStats(true), 60000);
});
onUnmounted(() => { if (pollTimer) clearInterval(pollTimer); });
</script>
