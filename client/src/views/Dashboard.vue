<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">仪表台</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">实时生产数据与指标</p>
      </div>
    </div>

    <!-- Bento Grid -->
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <div 
        v-for="card in cards" 
        :key="card.key"
        @click="cardClick(card)"
        :class="[
          'bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-5 flex flex-col justify-center items-center transition-all duration-200 shadow-sm',
          card.link ? 'cursor-pointer hover:bg-slate-50 dark:hover:bg-industrial-700/50 hover:border-blue-400 dark:hover:border-industrial-accent hover:-translate-y-1 shadow-lg' : ''
        ]"
      >
        <div :class="['text-3xl font-black mb-2', card.colorClass || 'text-industrial-accent']">
          {{ card.value }}
        </div>
        <div class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider text-center">
          {{ card.label }}
        </div>
      </div>
    </div>

    <!-- Recent Customers List -->
    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl overflow-hidden mt-6 shadow-sm" v-if="stats.recent_customers?.length">
      <div class="px-6 py-4 border-b border-slate-200 dark:border-industrial-border bg-slate-50 dark:bg-industrial-900/50">
        <h3 class="text-slate-800 dark:text-slate-200 font-semibold">最近新增客户</h3>
      </div>
      <div class="divide-y divide-slate-200 dark:divide-industrial-border">
        <div v-for="c in stats.recent_customers" :key="c.id" class="px-6 py-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-industrial-700/30 transition-colors">
          <div class="flex items-center space-x-4">
            <router-link :to="`/customers/${c.id}`" class="text-industrial-accent font-medium hover:underline">
              {{ c.name }}
            </router-link>
            <span class="text-sm text-slate-400">{{ c.contact }}</span>
          </div>
          <span class="text-xs text-slate-500 font-mono">{{ c.created_at?.slice(0,10) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api/index.js';

const router = useRouter();
const stats = reactive({ today_pending: 0, in_progress: 0, customer_confirm: 0, inventory_alert: 0, today_done: 0, recent_customers: [], my_todos: 0 });

const cards = ref([]);

onMounted(async () => {
  try {
    const r = await api.get('/dashboard/stats');
    Object.assign(stats, r.data);
    cards.value = [
      { key: 'pending', label: '待处理订单', value: stats.today_pending, link: '/orders?status=paused', colorClass: 'text-industrial-accent' },
      { key: 'progress', label: '生产中', value: stats.in_progress, link: '/orders?status=in_progress', colorClass: 'text-industrial-orange' },
      { key: 'alert', label: '库存预警', value: stats.inventory_alert, link: '/inventory', colorClass: 'text-red-500' },
      { key: 'done', label: '今日完成', value: stats.today_done, link: '/orders?status=completed', colorClass: 'text-green-500' },
    ];
  } catch {}
});

function cardClick(card) { if (card.link) router.push(card.link); }
</script>
