<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">订单管理</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">生产订单调度与跟踪</p>
      </div>
      <el-button v-if="auth.canEdit('orders')" type="primary" @click="openCreate" color="#7aa2f7" dark><el-icon><Plus /></el-icon> 新建订单</el-button>
    </div>

    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-4 flex flex-wrap gap-3 items-center shadow-md">
      <el-input v-model="params.keyword" placeholder="搜索订单号/产品/客户" clearable style="width:240px" @keyup.enter="search" />
      <el-select v-model="params.status" placeholder="状态" clearable style="width:140px">
        <el-option label="进行中" value="in_progress" /><el-option label="已完成" value="completed" /><el-option label="暂停" value="paused" />
      </el-select>
      <el-select v-model="params.priority" placeholder="优先级" clearable style="width:120px">
        <el-option label="普通" :value="0" /><el-option label="紧急" :value="1" /><el-option label="特急" :value="2" />
      </el-select>
      <el-button type="primary" @click="search" color="#7aa2f7" dark>搜索</el-button>
      <el-button @click="reset" plain>重置</el-button>
    </div>
    
    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl overflow-hidden shadow-md p-4">
    <el-table :data="orders" border stripe v-loading="loading" style="margin-top:12px" @sort-change="onSort" :default-sort="{prop:'created_at',order:'descending'}">
      <el-table-column prop="order_no" label="订单号" sortable="custom" width="120">
        <template #default="{ row }"><router-link :to="`/orders/${row.id}`" style="color:#409eff">{{ row.order_no }}</router-link></template>
      </el-table-column>
      <el-table-column prop="product_name" label="产品名称" sortable="custom" min-width="140" />
      <el-table-column label="客户" sortable="custom" width="120">
        <template #default="{ row }">
          <router-link v-if="row.customer_id" :to="`/customers/${row.customer_id}`" style="color:#409eff">{{ row.customer_name }}</router-link>
          <span v-else>{{ row.customer_name || '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="current_step_name" label="当前工序" width="120" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }"><el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column label="优先级" width="80" align="center">
        <template #default="{ row }"><el-tag :type="prioType(row.priority)" size="small">{{ ['普通','紧急','特急'][row.priority] || '普通' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="notes" label="备注" min-width="120">
        <template #default="{ row }"><span :title="row.notes">{{ row.notes ? (row.notes.length > 20 ? row.notes.slice(0,20)+'…' : row.notes) : '—' }}</span></template>
      </el-table-column>
      <el-table-column prop="shipment_date" label="交付日期" sortable="custom" width="160">
        <template #default="{ row }">{{ formatDateTime(row.shipment_date) }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" sortable="custom" width="160">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button v-if="auth.canEdit('orders')" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="auth.canEdit('orders')" size="small" type="danger" @click="confirmDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="mt-4 flex justify-end">
      <el-pagination background layout="total, sizes, prev, pager, next" :total="total" v-model:current-page="params.page" v-model:page-size="params.limit" :page-sizes="[10,20,50]" @change="fetchOrders" />
    </div>
    </div>

    <el-dialog v-model="dialogVisible" title="新建订单" width="500px">
      <el-form ref="createFormRef" :model="newOrder" :rules="formRules" label-width="100px">
        <el-form-item label="订单号" prop="order_no"><el-input v-model="newOrder.order_no" placeholder="必填" /></el-form-item>
        <el-form-item label="产品名称" prop="product_name"><el-input v-model="newOrder.product_name" placeholder="必填" /></el-form-item>
        <el-form-item label="客户" prop="customer_id">
          <el-select v-model="newOrder.customer_id" filterable clearable placeholder="选择客户">
            <el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="工艺模板" prop="template_flow_id">
          <el-select v-model="newOrder.template_flow_id" placeholder="选择模板">
            <el-option v-for="f in templates" :key="f.id" :label="f.name" :value="f.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priority"><el-select v-model="newOrder.priority"><el-option label="普通" :value="0" /><el-option label="紧急" :value="1" /><el-option label="特急" :value="2" /></el-select></el-form-item>
        <el-form-item label="交付日期"><el-date-picker v-model="newOrder.shipment_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width:100%" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="newOrder.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createOrder" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editDialogVisible" title="编辑订单" width="500px">
      <el-form ref="editFormRef" :model="editingOrder" :rules="formRules" label-width="100px">
        <el-form-item label="订单号" prop="order_no"><el-input v-model="editingOrder.order_no" placeholder="必填" /></el-form-item>
        <el-form-item label="产品名称" prop="product_name"><el-input v-model="editingOrder.product_name" placeholder="必填" /></el-form-item>
        <el-form-item label="客户" prop="customer_id">
          <el-select v-model="editingOrder.customer_id" filterable clearable placeholder="选择客户">
            <el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priority"><el-select v-model="editingOrder.priority"><el-option label="普通" :value="0" /><el-option label="紧急" :value="1" /><el-option label="特急" :value="2" /></el-select></el-form-item>
        <el-form-item label="交付日期"><el-date-picker v-model="editingOrder.shipment_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width:100%" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="editingOrder.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api/index.js';
import { useAuthStore } from '../stores/auth.js';

const route = useRoute();
const auth = useAuthStore();
const orders = ref([]);
const total = ref(0);
const loading = ref(false);
const dialogVisible = ref(false);
const creating = ref(false);
const saving = ref(false);
const editDialogVisible = ref(false);
const editingOrder = reactive({ id: null, order_no: '', product_name: '', customer_id: null, priority: 0, shipment_date: '', notes: '' });
const createFormRef = ref(null);
const editFormRef = ref(null);
const templates = ref([]);
const customers = ref([]);
const params = reactive({ keyword: '', status: '', priority: '', sort_by: 'created_at', sort_order: 'desc', page: 1, limit: 20 });
const newOrder = reactive({ order_no: '', product_name: '', customer_id: null, template_flow_id: null, priority: 0, shipment_date: '', notes: '' });

const formRules = {
  order_no: [{ required: true, message: '请输入订单号', trigger: 'blur' }],
  product_name: [{ required: true, message: '请输入产品名称', trigger: 'blur' }],
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
  template_flow_id: [{ required: true, message: '请选择工艺流程', trigger: 'change' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }]
};
const sortMap = { descending: 'desc', ascending: 'asc' };

onMounted(() => { 
  if (route.query.status) params.status = route.query.status;
  fetchOrders(); 
  fetchTemplates(); 
  fetchCustomers(); 
});
async function fetchOrders() {
  loading.value = true;
  try { const r = await api.get('/orders', { params }); orders.value = r.data.data; total.value = r.data.total; }
  catch {} finally { loading.value = false; }
}
async function fetchTemplates() { try { const r = await api.get('/process-flows'); templates.value = r.data; } catch {} }
async function fetchCustomers() { try { const r = await api.get('/customers'); customers.value = r.data; } catch {} }

function search() { params.page = 1; fetchOrders(); }
function reset() { Object.assign(params, { keyword: '', status: '', priority: '', page: 1 }); fetchOrders(); }
function onSort({ prop, order }) { params.sort_by = prop; params.sort_order = sortMap[order] || 'desc'; params.page = 1; fetchOrders(); }

function openCreate() { Object.assign(newOrder, { order_no: '', product_name: '', customer_id: null, template_flow_id: null, priority: 0, shipment_date: '', notes: '' }); dialogVisible.value = true; }

async function createOrder() {
  const valid = await createFormRef.value?.validate().catch(() => false);
  if (!valid) return;
  creating.value = true;
  try {
    const payload = { ...newOrder };
    if (!payload.shipment_date) payload.shipment_date = null;
    await api.post('/orders', payload);
    dialogVisible.value = false;
    await fetchOrders();
    ElMessage.success('创建成功');
  }
  catch (e) { ElMessage.error(e.response?.data?.detail || e.response?.data?.error || '创建失败'); }
  finally { creating.value = false; }
}

function openEdit(row) {
  Object.assign(editingOrder, {
    id: row.id,
    order_no: row.order_no,
    product_name: row.product_name,
    customer_id: row.customer_id || null,
    priority: row.priority || 0,
    shipment_date: row.shipment_date || '',
    notes: row.notes || ''
  });
  editDialogVisible.value = true;
}
async function saveEdit() {
  const valid = await editFormRef.value?.validate().catch(() => false);
  if (!valid) return;
  saving.value = true;
  try {
    await api.put(`/orders/${editingOrder.id}`, {
      order_no: editingOrder.order_no,
      product_name: editingOrder.product_name,
      customer_id: editingOrder.customer_id,
      priority: editingOrder.priority,
      shipment_date: editingOrder.shipment_date || null,
      notes: editingOrder.notes
    });
    editDialogVisible.value = false;
    await fetchOrders();
    ElMessage.success('保存成功');
  } catch (e) { ElMessage.error(e.response?.data?.error || '保存失败'); }
  finally { saving.value = false; }
}

async function confirmDelete(row) {
  try { await ElMessageBox.confirm(`确定删除订单 ${row.order_no}？`, '确认', { type: 'warning' }); await api.delete(`/orders/${row.id}`); await fetchOrders(); ElMessage.success('已删除'); } catch {}
}

function statusLabel(s) {
  const m = { in_progress: '进行中', completed: '已完成', paused: '暂停' };
  return m[s] || s;
}
function statusType(s) { if (s === 'completed') return 'success'; if (s === 'paused') return 'danger'; if (s === 'in_progress') return 'warning'; return 'info'; }
function prioType(p) { return p === 2 ? 'danger' : p === 1 ? 'warning' : 'info'; }
function formatDateTime(val) {
  if (!val) return '—';
  return val.slice(0, 16).replace('T', ' ');
}
</script>

<style scoped>
.search-bar { display: flex; align-items: center; flex-wrap: wrap; gap: 0; }
</style>
