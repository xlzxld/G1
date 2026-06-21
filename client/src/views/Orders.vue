<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>订单管理</h2>
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建订单</el-button>
    </div>
    <div class="search-bar">
      <el-input v-model="params.keyword" placeholder="搜索订单号/产品/客户" clearable style="width:240px" @keyup.enter="search" />
      <el-select v-model="params.status" placeholder="状态" clearable style="width:140px;margin-left:8px">
        <el-option label="草稿" value="draft" /><el-option label="进行中" value="progress" /><el-option label="客户确认" value="customer_confirm" /><el-option label="已完成" value="completed" /><el-option label="暂停" value="paused" />
      </el-select>
      <el-input v-model="params.customer_name" placeholder="客户筛选" clearable style="width:160px;margin-left:8px" @keyup.enter="search" />
      <el-select v-model="params.priority" placeholder="优先级" clearable style="width:120px;margin-left:8px">
        <el-option label="普通" :value="0" /><el-option label="紧急" :value="1" /><el-option label="特急" :value="2" />
      </el-select>
      <el-button type="primary" style="margin-left:8px" @click="search">搜索</el-button>
      <el-button @click="reset">重置</el-button>
    </div>
    <el-table :data="orders" border stripe v-loading="loading" style="margin-top:12px" @sort-change="onSort" :default-sort="{prop:'created_at',order:'descending'}">
      <el-table-column prop="order_no" label="订单号" sortable="custom" width="120">
        <template #default="{ row }"><router-link :to="`/orders/${row.id}`" style="color:#409eff">{{ row.order_no }}</router-link></template>
      </el-table-column>
      <el-table-column prop="product_name" label="产品名称" sortable="custom" min-width="140" />
      <el-table-column prop="customer_name" label="客户" sortable="custom" width="120" />
      <el-table-column prop="current_step_name" label="当前工序" width="120" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }"><el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag></template>
      </el-table-column>
      <el-table-column label="优先级" width="80" align="center">
        <template #default="{ row }"><el-tag :type="prioType(row.priority)" size="small">{{ ['普通','紧急','特急'][row.priority] || '普通' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="shipment_date" label="交货日期" sortable="custom" width="120" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }"><el-button size="small" type="danger" @click="confirmDelete(row)">删除</el-button></template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:16px;justify-content:flex-end" background layout="total, sizes, prev, pager, next" :total="total" v-model:current-page="params.page" v-model:page-size="params.limit" :page-sizes="[10,20,50]" @change="fetchOrders" />

    <el-dialog v-model="dialogVisible" title="新建订单" width="500px">
      <el-form :model="newOrder" label-width="100px">
        <el-form-item label="订单号"><el-input v-model="newOrder.order_no" /></el-form-item>
        <el-form-item label="产品名称"><el-input v-model="newOrder.product_name" /></el-form-item>
        <el-form-item label="客户"><el-input v-model="newOrder.customer_name" /></el-form-item>
        <el-form-item label="工艺模板">
          <el-select v-model="newOrder.template_flow_id" placeholder="选择模板(可选)" clearable>
            <el-option v-for="f in templates" :key="f.id" :label="f.name" :value="f.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级"><el-select v-model="newOrder.priority"><el-option label="普通" :value="0" /><el-option label="紧急" :value="1" /><el-option label="特急" :value="2" /></el-select></el-form-item>
        <el-form-item label="交货日期"><el-input v-model="newOrder.shipment_date" placeholder="可选" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="newOrder.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createOrder" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api/index.js';

const orders = ref([]);
const total = ref(0);
const loading = ref(false);
const dialogVisible = ref(false);
const creating = ref(false);
const templates = ref([]);
const params = reactive({ keyword: '', status: '', customer_name: '', priority: '', sort_by: 'created_at', sort_order: 'desc', page: 1, limit: 20 });
const newOrder = reactive({ order_no: '', product_name: '', customer_name: '', template_flow_id: null, priority: 0, shipment_date: '', notes: '' });

const sortMap = { descending: 'desc', ascending: 'asc' };

onMounted(() => { fetchOrders(); fetchTemplates(); });
async function fetchOrders() {
  loading.value = true;
  try { const r = await api.get('/orders', { params }); orders.value = r.data.data; total.value = r.data.total; }
  catch {} finally { loading.value = false; }
}
async function fetchTemplates() { try { const r = await api.get('/process-flows'); templates.value = r.data; } catch {} }

function search() { params.page = 1; fetchOrders(); }
function reset() { Object.assign(params, { keyword: '', status: '', customer_name: '', priority: '', page: 1 }); fetchOrders(); }
function onSort({ prop, order }) { params.sort_by = prop; params.sort_order = sortMap[order] || 'desc'; params.page = 1; fetchOrders(); }

function openCreate() { Object.assign(newOrder, { order_no: '', product_name: '', customer_name: '', template_flow_id: null, priority: 0, shipment_date: '', notes: '' }); dialogVisible.value = true; }

async function createOrder() {
  creating.value = true;
  try { await api.post('/orders', newOrder); dialogVisible.value = false; await fetchOrders(); ElMessage.success('创建成功'); }
  catch (e) { ElMessage.error(e.response?.data?.error || '创建失败'); }
  finally { creating.value = false; }
}

async function confirmDelete(row) {
  try { await ElMessageBox.confirm(`确定删除订单 ${row.order_no}？`, '确认', { type: 'warning' }); await api.delete(`/orders/${row.id}`); await fetchOrders(); ElMessage.success('已删除'); } catch {}
}

function statusType(s) { if (s === 'completed') return 'success'; if (s === 'paused') return 'danger'; if (s.includes('draft')) return 'info'; return 'warning'; }
function prioType(p) { return p === 2 ? 'danger' : p === 1 ? 'warning' : 'info'; }
</script>

<style scoped>
.search-bar { display: flex; align-items: center; flex-wrap: wrap; gap: 0; }
</style>
