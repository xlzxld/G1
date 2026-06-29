<template>
  <div v-if="customer" class="min-h-screen bg-slate-100 dark:bg-industrial-900 p-3 sm:p-6 text-slate-800 dark:text-slate-200">
    <div class="max-w-7xl mx-auto space-y-6">
      
      <!-- Top Title and Back Button -->
      <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-4 sm:p-6 shadow-md">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 border-b border-slate-200 dark:border-industrial-border pb-4">
          <h2 class="text-xl sm:text-2xl font-bold text-slate-900 dark:text-slate-100">{{ customer.name }}</h2>
          <router-link to="/customers" class="w-full sm:w-auto">
            <el-button plain class="w-full sm:w-auto">返回客户列表</el-button>
          </router-link>
        </div>
        <el-descriptions border :column="isMobile ? 1 : 3">
          <el-descriptions-item label="地址">{{ customer.address || '—' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(customer.created_at) }}</el-descriptions-item>
          
          <el-descriptions-item v-for="(method, idx) in parsedMethods" :key="idx" :label="method.type">
            {{ method.value || '—' }}
          </el-descriptions-item>

          <el-descriptions-item label="备注" :span="isMobile ? 1 : 3">{{ customer.notes || '—' }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- Statistics Grid -->
      <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-5 shadow-md">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-base sm:text-lg font-semibold text-slate-800 dark:text-slate-200">订单统计</h3>
          <span class="text-xs text-slate-400 dark:text-slate-500">* 点击下方卡片可快速筛选订单列表</span>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div 
            class="bg-slate-50 dark:bg-industrial-900/50 p-4 rounded-xl border transition-all duration-200 cursor-pointer text-center select-none"
            :class="[searchStatus === '' ? 'border-blue-500 shadow-md ring-1 ring-blue-500/30' : 'border-slate-100 dark:border-industrial-border hover:bg-slate-100 dark:hover:bg-industrial-700/50']"
            @click="filterByStatus('')"
          >
            <p class="text-xs text-slate-400 mb-1">总订单</p>
            <p class="text-2xl font-bold text-slate-800 dark:text-slate-100">{{ stats.total }}</p>
          </div>
          <div 
            class="bg-slate-50 dark:bg-industrial-900/50 p-4 rounded-xl border transition-all duration-200 cursor-pointer text-center select-none"
            :class="[searchStatus === 'completed' ? 'border-green-500 shadow-md ring-1 ring-green-500/30' : 'border-slate-100 dark:border-industrial-border hover:bg-green-50 dark:hover:bg-green-950/20']"
            @click="filterByStatus('completed')"
          >
            <p class="text-xs text-slate-400 mb-1">已完成</p>
            <p class="text-2xl font-bold text-green-500">{{ stats.completed }}</p>
          </div>
          <div 
            class="bg-slate-50 dark:bg-industrial-900/50 p-4 rounded-xl border transition-all duration-200 cursor-pointer text-center select-none"
            :class="[searchStatus === 'in_progress' ? 'border-orange-500 shadow-md ring-1 ring-orange-500/30' : 'border-slate-100 dark:border-industrial-border hover:bg-orange-50 dark:hover:bg-orange-950/20']"
            @click="filterByStatus('in_progress')"
          >
            <p class="text-xs text-slate-400 mb-1">生产中</p>
            <p class="text-2xl font-bold text-orange-500">{{ stats.in_progress }}</p>
          </div>
          <div 
            class="bg-slate-50 dark:bg-industrial-900/50 p-4 rounded-xl border transition-all duration-200 cursor-pointer text-center select-none"
            :class="[searchStatus === 'paused' ? 'border-red-500 shadow-md ring-1 ring-red-500/30' : 'border-slate-100 dark:border-industrial-border hover:bg-red-50 dark:hover:bg-red-950/20']"
            @click="filterByStatus('paused')"
          >
            <p class="text-xs text-slate-400 mb-1">暂停</p>
            <p class="text-2xl font-bold text-red-500">{{ stats.paused }}</p>
          </div>
        </div>
      </div>

      <!-- Orders List Section -->
      <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-4 sm:p-6 shadow-md space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-base sm:text-lg font-semibold text-slate-800 dark:text-slate-200">订单列表</h3>
          <span v-if="searchStatus" class="text-xs">
            正在筛选：<el-tag :type="statusType(searchStatus)" size="small" closable @close="filterByStatus('')">{{ statusLabel(searchStatus) }}</el-tag>
          </span>
        </div>

        <!-- 搜索与筛选栏 -->
        <div class="bg-slate-50 dark:bg-industrial-900/50 border border-slate-200 dark:border-industrial-border rounded-xl p-4 flex flex-wrap gap-3 items-center">
          <el-input v-model="searchKeyword" placeholder="搜索订单号/产品" clearable class="w-full sm:w-60" @keyup.enter="handleSearch" />
          <el-select v-model="searchStatus" placeholder="状态" clearable class="w-full sm:w-36" @change="handleSearch">
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="暂停" value="paused" />
          </el-select>
          <el-select v-model="searchPriority" placeholder="优先级" clearable class="w-full sm:w-32" @change="handleSearch">
            <el-option label="普通" :value="0" />
            <el-option label="紧急" :value="1" />
            <el-option label="特急" :value="2" />
          </el-select>
          <div class="flex gap-2 w-full sm:w-auto">
            <el-button type="primary" @click="handleSearch" class="flex-1 sm:flex-none">搜索</el-button>
            <el-button @click="handleReset" class="flex-1 sm:flex-none">重置</el-button>
          </div>
        </div>
        
        <!-- Desktop Table -->
        <el-table v-if="!isMobile" :data="orderList" border stripe v-loading="orderLoading">
          <el-table-column prop="order_no" label="订单号" width="130">
            <template #default="{ row }"><router-link :to="`/orders/${row.id}?from_customer=${customer.id}`" style="color:#409eff">{{ row.order_no }}</router-link></template>
          </el-table-column>
          <el-table-column prop="product_name" label="产品" />
          <el-table-column prop="priority" label="优先级" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="prioType(row.priority)" size="small">
                {{ ['普通','紧急','特急'][row.priority] || '普通' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }"><el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="current_step_name" label="当前工艺" min-width="140">
            <template #default="{ row }">
              <span class="text-slate-700 dark:text-slate-300 font-medium text-xs">{{ row.current_step_name || '已完成 / 无' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="shipment_date" label="交货日期" width="160">
            <template #default="{ row }">{{ formatDateTime(row.shipment_date) }}</template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="160">
            <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
          </el-table-column>
        </el-table>

        <!-- Mobile Card List -->
        <div v-else v-loading="orderLoading" class="space-y-3">
          <div
            v-for="row in orderList"
            :key="row.id"
            class="rounded-xl border border-slate-200 dark:border-industrial-border bg-slate-50 dark:bg-industrial-900/50 p-4 shadow-sm"
            @click="router.push(`/orders/${row.id}?from_customer=${customer.id}`)"
          >
            <div class="flex items-start justify-between mb-2">
              <div>
                <span class="text-blue-500 font-bold text-sm">#{{ row.order_no }}</span>
                <p class="text-slate-800 dark:text-slate-100 font-semibold text-base mt-0.5">{{ row.product_name }}</p>
              </div>
              <div class="flex flex-col items-end gap-1.5 shrink-0">
                <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
                <el-tag :type="prioType(row.priority)" size="small">{{ ['普通','紧急','特急'][row.priority] || '普通' }}</el-tag>
              </div>
            </div>
            
            <div class="py-2 border-t border-slate-200 dark:border-industrial-border mt-2 space-y-1 text-xs">
              <p class="text-slate-500 dark:text-slate-400">
                当前工艺：<span class="text-slate-700 dark:text-slate-300 font-semibold">{{ row.current_step_name || '已完成 / 无' }}</span>
              </p>
              <p class="text-slate-500 dark:text-slate-400" v-if="row.shipment_date">
                交货日期：<span class="text-slate-700 dark:text-slate-300">{{ formatDateTime(row.shipment_date) }}</span>
              </p>
            </div>
          </div>
          <div v-if="orderList.length === 0" class="py-10 text-center">
            <el-empty description="暂无关联订单" />
          </div>
        </div>

        <!-- Pagination Section -->
        <div v-if="totalOrders > pageSize" class="mt-4 flex justify-end">
          <el-pagination
            background
            layout="total, prev, pager, next"
            :total="totalOrders"
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :small="isMobile"
            @current-change="fetchOrders"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, watch, onActivated } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import api from '../api/index.js';

defineOptions({ name: 'CustomerDetail' });

const route = useRoute();
const router = useRouter();
const customer = ref(null);
const orderList = ref([]);
const orderLoading = ref(false);
const stats = reactive({ total: 0, completed: 0, in_progress: 0, paused: 0 });

// 分页与筛选
const totalOrders = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);

const searchKeyword = ref('');
const searchStatus = ref('');
const searchPriority = ref('');
const lastLoadedId = ref(null);

const isMobile = ref(window.innerWidth < 768);
function onResize() { isMobile.value = window.innerWidth < 768; }
onMounted(() => window.addEventListener('resize', onResize));
onUnmounted(() => window.removeEventListener('resize', onResize));

const parsedMethods = computed(() => {
  if (!customer.value) return [];
  try {
    const raw = customer.value.contact_methods;
    return typeof raw === 'string' ? JSON.parse(raw) : (raw || []);
  } catch {
    return [];
  }
});

async function loadData() {
  if (!route.params.id || route.params.id === lastLoadedId.value) return;
  lastLoadedId.value = route.params.id;
  try { 
    const r = await api.get(`/customers/${route.params.id}`); 
    customer.value = r.data; 
  } catch (e) {
    ElMessage.error("该客户已不存在或已被删除！");
    router.push('/customers');
    return;
  }
  fetchStats();
  fetchOrders();
}

onMounted(loadData);

onActivated(() => {
  if (route.params.id && route.params.id !== lastLoadedId.value) {
    loadData();
  } else {
    // 静默刷新数据，保证最新状态
    if (customer.value) {
      fetchStats();
      fetchOrders(true);
    }
  }
});

watch(() => route.params.id, (newId) => {
  if (newId && route.name === 'CustomerDetail') {
    loadData();
  }
});

async function fetchStats() {
  if (!route.params.id) return;
  try { 
    const r = await api.get(`/customers/${route.params.id}/stats`);
    Object.assign(stats, r.data); 
  } catch {}
}

async function fetchOrders(silent = false) {
  if (!route.params.id) return;
  if (!silent || orderList.value.length === 0) {
    orderLoading.value = true;
  }
  try {
    const res = await api.get('/orders', {
      params: {
        customer_id: route.params.id,
        page: currentPage.value,
        limit: pageSize.value,
        keyword: searchKeyword.value,
        status: searchStatus.value,
        priority: searchPriority.value
      }
    });
    orderList.value = res.data.data || [];
    totalOrders.value = res.data.total || 0;
  } catch (e) {
    console.error("加载客户订单失败", e);
  } finally {
    orderLoading.value = false;
  }
}

function handleSearch() {
  currentPage.value = 1;
  fetchOrders();
}

function handleReset() {
  searchKeyword.value = '';
  searchStatus.value = '';
  searchPriority.value = '';
  currentPage.value = 1;
  fetchOrders();
}

function filterByStatus(status) {
  searchStatus.value = status;
  currentPage.value = 1;
  fetchOrders();
}

function statusType(s) { if (s === 'completed') return 'success'; if (s === 'paused') return 'danger'; if (s === 'in_progress') return 'warning'; return 'info'; }
function statusLabel(s) {
  const m = { in_progress: '进行中', completed: '已完成', paused: '暂停' };
  return m[s] || s;
}
function formatDateTime(val) {
  if (!val) return '—';
  return val.slice(0, 16).replace('T', ' ');
}

function prioType(p) { return p === 2 ? 'danger' : p === 1 ? 'warning' : 'info'; }
</script>
