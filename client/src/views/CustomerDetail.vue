<template>
  <div v-if="customer">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>{{ customer.name }}</h2>
      <router-link to="/customers"><el-button>返回客户列表</el-button></router-link>
    </div>
    <el-descriptions border :column="3">
      <el-descriptions-item label="联系人">{{ customer.contact || '—' }}</el-descriptions-item>
      <el-descriptions-item label="电话">{{ customer.phone || '—' }}</el-descriptions-item>
      <el-descriptions-item label="地址">{{ customer.address || '—' }}</el-descriptions-item>
      <el-descriptions-item label="微信">{{ customer.wechat || '—' }}</el-descriptions-item>
      <el-descriptions-item label="邮箱">{{ customer.email || '—' }}</el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ customer.created_at?.slice(0,10) }}</el-descriptions-item>
      <el-descriptions-item label="备注" :span="3">{{ customer.notes || '—' }}</el-descriptions-item>
    </el-descriptions>

    <el-divider />
    <h3 style="margin-bottom:12px">订单统计</h3>
    <el-row :gutter="16">
      <el-col :span="6"><el-statistic title="总订单" :value="stats.total" /></el-col>
      <el-col :span="6"><el-statistic title="已完成" :value="stats.completed" /></el-col>
      <el-col :span="6"><el-statistic title="生产中" :value="stats.in_progress" /></el-col>
      <el-col :span="6"><el-statistic title="暂停/中止" :value="stats.paused + stats.aborted" /></el-col>
    </el-row>

    <el-divider />
    <h3 style="margin-bottom:12px">订单列表</h3>
    <el-table :data="orderList" border stripe v-loading="orderLoading">
      <el-table-column prop="order_no" label="订单号" width="120">
        <template #default="{ row }"><router-link :to="`/orders/${row.id}`" style="color:#409eff">{{ row.order_no }}</router-link></template>
      </el-table-column>
      <el-table-column prop="product_name" label="产品" />
      <el-table-column label="状态" width="120"><template #default="{ row }"><el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag></template></el-table-column>
      <el-table-column prop="shipment_date" label="交货日期" width="120" />
      <el-table-column prop="created_at" label="创建时间" width="120" />
    </el-table>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import api from '../api/index.js';

const route = useRoute();
const customer = ref(null);
const orderList = ref([]);
const orderLoading = ref(false);
const stats = reactive({ total: 0, completed: 0, in_progress: 0, paused: 0, aborted: 0 });

onMounted(async () => {
  try { const r = await api.get(`/customers/${route.params.id}`); customer.value = r.data; } catch {}
  orderLoading.value = true;
  try { orderList.value = (await api.get(`/customers/${route.params.id}/orders`)).data; } catch {} finally { orderLoading.value = false; }
  try { Object.assign(stats, (await api.get(`/customers/${route.params.id}/stats`)).data); } catch {}
});

function statusType(s) { if (s === 'completed') return 'success'; if (s === 'paused' || s === 'aborted') return 'danger'; if (s === 'draft') return 'info'; return 'warning'; }
</script>
