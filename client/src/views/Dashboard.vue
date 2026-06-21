<template>
  <div>
    <h2 style="margin-bottom:16px">仪表台</h2>
    <el-row :gutter="16">
      <el-col :xs="24" :sm="12" :md="8" v-for="card in cards" :key="card.key" style="margin-bottom:16px">
        <el-card shadow="hover" @click="cardClick(card)" :body-style="{ padding: '20px', cursor: card.link ? 'pointer' : 'default' }">
          <div style="text-align:center">
            <div style="font-size:32px;font-weight:700;color:#409eff">{{ card.value }}</div>
            <div style="margin-top:8px;color:#909399">{{ card.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-card shadow="never" style="margin-top:16px" v-if="stats.recent_customers?.length">
      <template #header>最近新增客户</template>
      <div v-for="c in stats.recent_customers" :key="c.id" style="padding:8px 0;border-bottom:1px solid #f0f0f0">
        <router-link :to="`/customers/${c.id}`" style="color:#409eff">{{ c.name }}</router-link>
        <span style="color:#909399;margin-left:8px">{{ c.contact }}</span>
        <span style="float:right;color:#909399">{{ c.created_at?.slice(0,10) }}</span>
      </div>
    </el-card>
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
      { key: 'pending', label: '待处理订单', value: stats.today_pending, link: '/orders' },
      { key: 'progress', label: '生产中', value: stats.in_progress, link: '/orders' },
      { key: 'confirm', label: '待客户确认', value: stats.customer_confirm, link: '/orders' },
      { key: 'alert', label: '库存预警', value: stats.inventory_alert, link: '/inventory' },
      { key: 'done', label: '今日完成', value: stats.today_done, link: '/orders' },
      { key: 'todos', label: '我的待办', value: stats.my_todos, link: '/orders' },
    ];
  } catch {}
});

function cardClick(card) { if (card.link) router.push(card.link); }
</script>
