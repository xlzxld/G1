<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">采购管理</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">补货清单 → 采购单 → 到货入库（自动生成库存流水）</p>
      </div>
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建采购单</el-button>
    </div>

    <!-- 补货意向清单 -->
    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-4 mb-6 shadow-sm" v-if="replenish.length">
      <div class="flex items-center justify-between mb-3">
        <h3 class="font-semibold text-slate-800 dark:text-slate-200">
          <span class="inline-block w-2 h-2 rounded-full bg-red-500 mr-2"></span>补货意向（可用 ≤ 安全库存）
        </h3>
        <span class="text-xs text-slate-400">{{ replenish.length }} 项</span>
      </div>
      <div class="flex flex-wrap gap-2">
        <el-button v-for="it in replenish" :key="it.id" size="small" type="danger" plain
          @click="openCreate(it)">
          {{ it.name }} · 可用 {{ it.available || (it.total - it.reserved) }} / {{ it.min_stock }} {{ it.unit }}
        </el-button>
      </div>
    </div>

    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl shadow-md p-4">
      <div class="flex flex-wrap gap-3 items-center mb-4">
        <el-radio-group v-model="statusFilter" @change="fetchList">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="draft">草稿</el-radio-button>
          <el-radio-button value="ordered">已下单</el-radio-button>
          <el-radio-button value="closed">已完结</el-radio-button>
        </el-radio-group>
        <el-input v-model="keyword" placeholder="按物料名搜索" clearable class="w-full sm:w-56" @keyup.enter="fetchList" @clear="fetchList" />
      </div>

      <el-table :data="list" border stripe v-loading="loading">
        <el-table-column prop="po_no" label="采购单号" width="170" />
        <el-table-column prop="item_name" label="物料" min-width="130" />
        <el-table-column prop="vendor_name" label="供应商" width="120" show-overflow-tooltip />
        <el-table-column label="采购/已收" width="110" align="center">
          <template #default="{row}">{{ row.quantity }} / {{ row.received_quantity }} {{ row.item_unit }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{row}">
            <el-tag :type="{draft:'info', ordered:'warning', closed:'success'}[row.status]" size="small">
              {{ {draft:'草稿', ordered:'已下单', closed:'已完结'}[row.status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="交期" width="110">
          <template #default="{row}">{{ (row.expected_date || '—').slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="{row}">
            <el-button v-if="row.status === 'draft'" size="small" type="primary" @click="confirmOrder(row)">确认下单</el-button>
            <el-button v-if="row.status === 'ordered'" size="small" type="success" @click="openReceive(row)">到货入库</el-button>
            <el-button v-if="row.status === 'draft'" size="small" type="danger" @click="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="list.length === 0" class="py-12">
        <el-empty description="暂无采购单——从上方补货意向一键创建，或手动新建" />
      </div>
    </div>

    <el-dialog v-model="createVisible" title="新建采购单" :width="isMobile ? '95vw' : '480px'">
      <el-form :label-position="isMobile ? 'top' : 'right'" label-width="90px">
        <el-form-item label="物料" required>
          <el-select v-model="form.item_id" filterable style="width:100%">
            <el-option v-for="i in itemOptions" :key="i.id" :label="`${i.name}（可用 ${i.total - i.reserved} ${i.unit}）`" :value="i.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量" required><el-input-number v-model="form.quantity" :min="1" style="width:100%" /></el-form-item>
        <el-form-item label="供应商">
          <el-select v-model="form.vendor_id" clearable filterable style="width:100%">
            <el-option v-for="v in vendors" :key="v.id" :label="v.name" :value="v.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="期望交期"><el-date-picker v-model="form.expected_date" type="date" style="width:100%" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.note" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="createVisible=false">取消</el-button><el-button type="primary" @click="save" :loading="saving">保存为草稿</el-button></template>
    </el-dialog>

    <el-dialog v-model="receiveVisible" title="到货入库" :width="isMobile ? '95vw' : '440px'">
      <el-form :label-position="isMobile ? 'top' : 'right'" label-width="90px">
        <el-form-item label="采购单">{{ receivePo?.po_no }} · {{ receivePo?.item_name }}</el-form-item>
        <el-form-item label="未收数量">{{ (receivePo?.quantity || 0) - (receivePo?.received_quantity || 0) }} {{ receivePo?.item_unit }}</el-form-item>
        <el-form-item label="本次到货" required><el-input-number v-model="receiveQty" :min="1" :max="(receivePo?.quantity || 0) - (receivePo?.received_quantity || 0)" style="width:100%" /></el-form-item>
        <p class="text-xs text-slate-400">到货即生成入库流水并解除对应库存预警；分批到货可多次录入，满额自动完结。</p>
      </el-form>
      <template #footer><el-button @click="receiveVisible=false">取消</el-button><el-button type="primary" @click="submitReceive" :loading="saving">确认入库</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api/index.js';
import { useAuthStore } from '../stores/auth.js';
import { Plus } from '@element-plus/icons-vue';

defineOptions({ name: 'Purchases' });

const isMobile = ref(window.innerWidth < 768);
const auth = useAuthStore();
const list = ref([]);
const replenish = ref([]);
const itemOptions = ref([]);
const vendors = ref([]);
const loading = ref(false);
const saving = ref(false);
const statusFilter = ref('');
const keyword = ref('');
const createVisible = ref(false);
const receiveVisible = ref(false);
const receivePo = ref(null);
const receiveQty = ref(1);
const form = reactive({ item_id: null, vendor_id: null, quantity: 1, expected_date: null, note: '' });

async function fetchList() {
  loading.value = true;
  try {
    const res = await api.get('/purchases', { params: { status: statusFilter.value || undefined, keyword: keyword.value || undefined } });
    list.value = res.data;
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '采购单加载失败');
  } finally { loading.value = false; }
}
async function fetchReplenish() {
  try { replenish.value = (await api.get('/inventory/replenish')).data; } catch (e) { console.error(e); }
}
async function fetchOptions() {
  try {
    const res = await api.get('/inventory', { params: { limit: 1000 } });
    itemOptions.value = Array.isArray(res.data) ? res.data : res.data.data;
    vendors.value = (await api.get('/vendors')).data;
  } catch (e) { console.error(e); }
}
function openCreate(prefill = null) {
  Object.assign(form, {
    item_id: prefill ? prefill.id : null,
    vendor_id: null,
    quantity: prefill ? Math.max(1, (prefill.min_stock || 5) - (prefill.total - prefill.reserved)) : 1,
    expected_date: null, note: prefill ? '补货意向自动带入' : '',
  });
  fetchOptions();
  createVisible.value = true;
}
async function save() {
  if (!form.item_id) return ElMessage.error('请选择物料');
  saving.value = true;
  try {
    await api.post('/purchases', form);
    createVisible.value = false;
    await Promise.all([fetchList(), fetchReplenish()]);
    ElMessage.success('采购单已创建（草稿）');
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '创建失败');
  } finally { saving.value = false; }
}
async function confirmOrder(row) {
  try {
    await ElMessageBox.confirm(`确认下单「${row.item_name} × ${row.quantity}」？`, '下单确认', { type: 'info' });
    await api.put(`/purchases/${row.id}/order`);
    await fetchList();
    ElMessage.success('已下单');
  } catch (e) { if (e !== 'cancel') ElMessage.error(e.response?.data?.error || '操作失败'); }
}
function openReceive(row) {
  receivePo.value = row;
  receiveQty.value = (row.quantity - row.received_quantity) || 1;
  receiveVisible.value = true;
}
async function submitReceive() {
  saving.value = true;
  try {
    await api.post(`/purchases/${receivePo.value.id}/receive`, { received_quantity: receiveQty.value });
    receiveVisible.value = false;
    await Promise.all([fetchList(), fetchReplenish()]);
    ElMessage.success('到货入库成功，库存流水已生成');
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '入库失败');
  } finally { saving.value = false; }
}
async function confirmDelete(row) {
  try {
    await ElMessageBox.confirm(`删除草稿采购单「${row.po_no}」？`, '确认', { type: 'warning' });
    await api.delete(`/purchases/${row.id}`);
    await fetchList();
    ElMessage.success('已删除');
  } catch (e) { if (e !== 'cancel') ElMessage.error(e.response?.data?.error || '删除失败'); }
}

onMounted(() => { fetchList(); fetchReplenish(); });
</script>
