<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">库存管理</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">物料台账 · 出入库 · 领退料 · 盘点（所有数量变更均记录流水）</p>
      </div>
      <el-button v-if="auth.isAdmin" type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新增物料</el-button>
    </div>

    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-4 mb-6 flex flex-wrap gap-3 items-center shadow-sm">
      <el-input v-model="searchKeyword" placeholder="搜索名称 / 规格 / 分类" clearable class="w-full sm:w-72" @input="debouncedSearch" @clear="handleSearch" @keyup.enter="handleSearch">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="categoryFilter" placeholder="全部分类" clearable filterable allow-create class="w-full sm:w-44" @change="handleSearch">
        <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
      </el-select>
      <el-checkbox v-model="showArchived" @change="handleSearch">显示已归档</el-checkbox>
      <el-button type="primary" @click="handleSearch" class="w-full sm:w-auto">搜索</el-button>
      <el-button @click="exportExcel" class="w-full sm:w-auto">导出 Excel</el-button>
      <el-upload v-if="auth.isAdmin" :show-file-list="false" :before-upload="importExcel" accept=".xlsx,.xlsm" class="inline-block ml-2">
        <el-button type="warning" plain>导入 Excel</el-button>
      </el-upload>
    </div>

    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl overflow-hidden shadow-md p-4">
      <!-- 桌面端表格 -->
      <el-table v-if="!isMobile" :data="items" border stripe v-loading="loading" @sort-change="handleSortChange" :row-class-name="tableRowClassName">
        <el-table-column prop="name" label="名称" min-width="130" sortable="custom" />
        <el-table-column prop="spec" label="规格" min-width="110" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="90" show-overflow-tooltip />
        <el-table-column prop="location" label="库位" width="80" />
        <el-table-column prop="total" label="总量" width="85" align="center" sortable="custom">
          <template #default="{row}">
            <span :style="{color:row.total-row.reserved<=row.min_stock?'#f56c6c':''}" :class="row.total-row.reserved<=row.min_stock?'font-bold':''">{{ row.total }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="reserved" label="已预留" width="80" align="center" />
        <el-table-column label="可用 / 安全库存" width="110" align="center">
          <template #default="{row}">
            <span :class="row.total-row.reserved<=row.min_stock ? 'text-red-500 font-bold' : 'text-green-600 font-bold'">{{ row.total - row.reserved }}</span>
            <span class="text-slate-400 text-xs"> / {{ row.min_stock }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="unit" label="单位" width="55" />
        <el-table-column label="操作" width="270" fixed="right">
          <template #default="{row}">
            <el-button v-if="!row.is_archived" size="small" type="success" @click="openMovement(row, 'INBOUND')">入库</el-button>
            <el-button v-if="!row.is_archived" size="small" type="warning" @click="openMovement(row, 'OUTBOUND')">领料</el-button>
            <el-button size="small" @click="openMovementsLog(row)">流水</el-button>
            <el-dropdown v-if="auth.isAdmin || auth.canEdit('inventory')" class="ml-2 align-middle" @command="cmd => handleRowCommand(cmd, row)">
              <el-button size="small">更多<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-if="!row.is_archived" command="RETURN">退料</el-dropdown-item>
                  <el-dropdown-item v-if="!row.is_archived" command="RESERVE">预留</el-dropdown-item>
                  <el-dropdown-item v-if="auth.isAdmin && !row.is_archived" command="STOCKTAKE" divided>盘点</el-dropdown-item>
                  <el-dropdown-item v-if="auth.isAdmin && !row.is_archived" command="EDIT">编辑主数据</el-dropdown-item>
                  <el-dropdown-item v-if="auth.isAdmin && !row.is_archived" command="ARCHIVE">归档</el-dropdown-item>
                  <el-dropdown-item v-if="auth.isAdmin" command="DELETE" class="text-red-500">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-tag v-if="row.is_archived" type="info" size="small" class="ml-2">已归档</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <!-- 移动端卡片列表 -->
      <div v-else v-loading="loading" class="space-y-3 mt-2">
        <div
          v-for="row in items"
          :key="row.id"
          :class="['rounded-xl border p-4 shadow-sm transition-colors', row.id == highlightedId ? 'border-blue-500 bg-blue-50/40 dark:bg-blue-950/40 highlight-flash-card-active highlight-target-item' : 'border-slate-200 dark:border-industrial-border bg-slate-50 dark:bg-industrial-900/50']"
        >
          <div class="flex items-start justify-between mb-2">
            <div>
              <p class="text-slate-800 dark:text-slate-100 font-semibold text-base">{{ row.name }}</p>
              <p v-if="row.spec" class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">规格：{{ row.spec }}</p>
              <p class="text-xs text-slate-400 mt-0.5">{{ row.category || '未分类' }} · {{ row.location || '未设库位' }}</p>
            </div>
            <div class="flex flex-col items-end gap-1">
              <el-tag v-if="row.is_archived" type="info" size="small">已归档</el-tag>
              <el-tag v-else-if="row.total - row.reserved <= row.min_stock" type="danger" size="small">库存预警</el-tag>
            </div>
          </div>
          <div class="grid grid-cols-3 gap-2 text-sm mb-3">
            <div class="text-center bg-white dark:bg-industrial-800 rounded-lg p-2 border border-slate-200 dark:border-industrial-border">
              <p class="font-bold text-lg text-slate-800 dark:text-slate-100">{{ row.total }}</p>
              <p class="text-xs text-slate-400 mt-0.5">总量 ({{ row.unit }})</p>
            </div>
            <div class="text-center bg-white dark:bg-industrial-800 rounded-lg p-2 border border-slate-200 dark:border-industrial-border">
              <p class="font-bold text-lg text-orange-500">{{ row.reserved }}</p>
              <p class="text-xs text-slate-400 mt-0.5">已预留</p>
            </div>
            <div class="text-center bg-white dark:bg-industrial-800 rounded-lg p-2 border border-slate-200 dark:border-industrial-border">
              <p class="font-bold text-lg text-green-500">{{ row.total - row.reserved }}</p>
              <p class="text-xs text-slate-400 mt-0.5">可用</p>
            </div>
          </div>
          <div v-if="auth.canEdit('inventory') && !row.is_archived" class="flex gap-2 border-t border-slate-200 dark:border-industrial-border pt-3">
            <el-button size="small" type="success" class="flex-1" @click="openMovement(row, 'INBOUND')">入库</el-button>
            <el-button size="small" type="warning" class="flex-1" @click="openMovement(row, 'OUTBOUND')">领料</el-button>
            <el-button size="small" class="flex-1" @click="openMovementsLog(row)">流水</el-button>
          </div>
        </div>
        <div v-if="items.length === 0" class="py-16 text-center">
          <el-empty :description="searchKeyword ? '没有匹配的物料' : '还没有物料——点击右上角「新增物料」建立第一个物料，再入库' " />
        </div>
      </div>

      <div v-if="!isMobile && items.length === 0" class="py-12">
        <el-empty :description="searchKeyword ? '没有匹配的物料' : '还没有物料——点击右上角「新增物料」建立第一个物料，再入库'" />
      </div>

      <div class="mt-4 flex justify-end overflow-x-auto">
        <el-pagination background :layout="isMobile ? 'total, prev, pager, next' : 'total, sizes, prev, pager, next'" :total="total" v-model:current-page="page" v-model:page-size="limit" :page-sizes="[10, 20, 50]" @current-change="fetchItems" @size-change="fetchItems" :small="isMobile" />
      </div>
    </div>

    <!-- 新建/编辑主数据（仅管理员；数量不在此改，走出入库/盘点） -->
    <el-dialog v-model="formVisible" :title="editing?'编辑物料主数据':'新增物料'" :width="isMobile ? '95vw' : '460px'">
      <el-form ref="formRef" :model="form" :rules="rules" :label-position="isMobile ? 'top' : 'right'" label-width="90px">
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="规格"><el-input v-model="form.spec" /></el-form-item>
        <el-form-item label="分类"><el-input v-model="form.category" placeholder="如：热嘴 / 加热元件" /></el-form-item>
        <el-form-item label="库位"><el-input v-model="form.location" placeholder="如：A区-01" /></el-form-item>
        <el-form-item v-if="!editing" label="期初数量" prop="total">
          <el-input-number v-model="form.total" :min="0" style="width:100%" />
          <p class="text-xs text-slate-400 mt-1">将以「期初入库」流水入账，可在流水中追溯</p>
        </el-form-item>
        <el-form-item label="单位"><el-input v-model="form.unit" /></el-form-item>
        <el-form-item label="安全库存"><el-input-number v-model="form.min_stock" :min="0" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="formVisible=false">取消</el-button><el-button type="primary" @click="save" :loading="saving">保存</el-button></template>
    </el-dialog>

    <!-- 出入库 / 领退料 操作框 -->
    <el-dialog v-model="movementVisible" :title="movementTitle" :width="isMobile ? '95vw' : '440px'">
      <el-form :label-position="isMobile ? 'top' : 'right'" label-width="90px">
        <el-form-item label="物料">{{ movementItem?.name }} <span class="text-xs text-slate-400 ml-2">当前可用 {{ movementItem ? movementItem.total - movementItem.reserved : 0 }} {{ movementItem?.unit }}</span></el-form-item>
        <el-form-item v-if="movementNeedsOrder" label="订单">
          <el-select v-model="movementOrderId" filterable :loading="ordersLoading" placeholder="选择订单" style="width:100%">
            <el-option v-for="o in orders" :key="o.id" :label="`${o.order_no} ${o.product_name}`" :value="o.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量"><el-input-number v-model="movementQty" :min="1" style="width:100%" /></el-form-item>
        <el-form-item v-if="movementType === 'INBOUND'" label="批次号"><el-input v-model="movementBatch" placeholder="如 B2026-0906（可空）" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="movementNote" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="movementVisible=false">取消</el-button><el-button type="primary" @click="submitMovement" :loading="movementSaving">确认</el-button></template>
    </el-dialog>

    <!-- 盘点（管理员） -->
    <el-dialog v-model="stocktakeVisible" title="库存盘点" :width="isMobile ? '95vw' : '440px'">
      <el-form :label-position="isMobile ? 'top' : 'right'" label-width="90px">
        <el-form-item label="物料">{{ stocktakeItem?.name }}</el-form-item>
        <el-form-item label="系统数量">{{ stocktakeItem?.total }} {{ stocktakeItem?.unit }}</el-form-item>
        <el-form-item label="实盘数量"><el-input-number v-model="stocktakeQty" :min="0" style="width:100%" /></el-form-item>
        <p class="text-xs text-slate-400">差额将以「盘点调整」流水入账：系统 {{ stocktakeItem?.total }} → 实盘 {{ stocktakeQty || 0 }}（差额 {{ (stocktakeQty || 0) - (stocktakeItem?.total || 0) }}）</p>
      </el-form>
      <template #footer><el-button @click="stocktakeVisible=false">取消</el-button><el-button type="primary" @click="submitStocktake" :loading="movementSaving">确认盘点</el-button></template>
    </el-dialog>

    <!-- 预留 -->
    <el-dialog v-model="reserveVisible" title="预留物料" :width="isMobile ? '95vw' : '440px'">
      <el-form :label-position="isMobile ? 'top' : 'right'" label-width="80px">
        <el-form-item label="物料">{{ reserveItem?.name }}</el-form-item>
        <el-form-item label="订单"><el-select v-model="reserveOrderId" filterable :loading="ordersLoading" placeholder="选择订单" style="width:100%"><el-option v-for="o in orders" :key="o.id" :label="`${o.order_no} ${o.product_name}`" :value="o.id" /></el-select></el-form-item>
        <el-form-item label="数量"><el-input-number v-model="reserveQty" :min="1" :max="(reserveItem?.total||0)-(reserveItem?.reserved||0)" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="reserveVisible=false">取消</el-button><el-button type="primary" @click="doReserve">确认预留</el-button></template>
    </el-dialog>

    <!-- 流水历史 -->
    <el-dialog v-model="logVisible" :title="`库存流水 · ${logItem?.name || ''}`" :width="isMobile ? '95vw' : '760px'">
      <el-table :data="movements" size="small" max-height="480" v-loading="logLoading">
        <el-table-column label="时间" width="160">
          <template #default="{row}">{{ (row.created_at || '').replace('T', ' ').slice(0, 19) }}</template>
        </el-table-column>
        <el-table-column label="类型" width="110">
          <template #default="{row}">
            <el-tag :type="movementTagType(row.type)" size="small">{{ movementLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="数量" width="90" align="center">
          <template #default="{row}">
            <span :class="row.quantity >= 0 ? 'text-green-600' : 'text-red-500'">{{ row.quantity >= 0 ? '+' : '' }}{{ row.quantity }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="balance_after" label="结余" width="80" align="center" />
        <el-table-column prop="batch_no" label="批次" width="110" show-overflow-tooltip />
        <el-table-column prop="note" label="备注" min-width="140" show-overflow-tooltip />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onUnmounted, watch, nextTick, onActivated } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api/index.js';
import { useAuthStore } from '../stores/auth.js';
import { debounce } from '../utils/debounce.js';
import { Plus, Search, ArrowDown } from '@element-plus/icons-vue';

defineOptions({ name: 'Inventory' });

const isMobile = ref(window.innerWidth < 768);
function onResize() { isMobile.value = window.innerWidth < 768; }
window.addEventListener('resize', onResize);
onUnmounted(() => window.removeEventListener('resize', onResize));
const route = useRoute();
const auth = useAuthStore();
const items = ref([]);
const total = ref(0);
const loading = ref(false);
const orders = ref([]);
const ordersLoading = ref(false);
const categoryFilter = ref('');
const categoryOptions = ref([]);
const showArchived = ref(false);
const formVisible = ref(false);
const editing = ref(null);
const saving = ref(false);
const formRef = ref(null);
const form = reactive({ name:'', spec:'', category:'', location:'', total:0, unit:'件', min_stock:5 });
const rules = {
  name: [{ required: true, message: '请输入物料名称', trigger: 'blur' }],
};
const movementVisible = ref(false);
const movementType = ref('INBOUND');
const movementItem = ref(null);
const movementQty = ref(1);
const movementOrderId = ref(null);
const movementBatch = ref('');
const movementNote = ref('');
const movementSaving = ref(false);
const stocktakeVisible = ref(false);
const stocktakeItem = ref(null);
const stocktakeQty = ref(0);
const reserveVisible = ref(false);
const reserveItem = ref(null);
const reserveOrderId = ref(null);
const reserveQty = ref(1);
const logVisible = ref(false);
const logItem = ref(null);
const movements = ref([]);
const logLoading = ref(false);
const searchKeyword = ref('');
const sortBy = ref('created_at');
const sortOrder = ref('desc');
const page = ref(1);
const limit = ref(20);
const highlightedId = ref(null);

const movementNeedsOrder = computed(() => ['OUTBOUND', 'RETURN'].includes(movementType.value));
const movementTitle = computed(() => ({ INBOUND: '入库', OUTBOUND: '领料出库', RETURN: '退料入库' }[movementType.value] || '库存操作'));

const debouncedSearch = debounce(handleSearch, 300);

onActivated(() => {
  if (items.value.length > 0) {
    fetchItems(true);
  }
});

function triggerHighlightScroll() {
  if (highlightedId.value) {
    nextTick(() => {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          const el = document.querySelector('.highlight-target-item');
          if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
      });
    });
  }
}

watch(() => route.query.highlight, async (newVal) => {
  if (newVal) {
    const targetId = parseInt(newVal);
    highlightedId.value = null;
    await nextTick();
    highlightedId.value = targetId;

    const exists = items.value.some(o => o.id === targetId);
    if (exists) {
      triggerHighlightScroll();
      locateInventoryPage(targetId).then(() => fetchItems(true));
      return;
    }

    await locateInventoryPage(targetId);
  } else {
    highlightedId.value = null;
  }
  await fetchItems(true);
  triggerHighlightScroll();
}, { immediate: true });

async function locateInventoryPage(targetId) {
  try {
    const res = await api.get(`/inventory/${targetId}/locate`, {
      params: { limit: limit.value, keyword: searchKeyword.value, sort_by: sortBy.value, sort_order: sortOrder.value }
    });
    if (res.data && res.data.page !== undefined) page.value = res.data.page;
    else highlightedId.value = null;
  } catch (e) { console.error('Locate inventory page failed:', e); }
}

async function fetchItems(silent = false) {
  if (!silent || items.value.length === 0) loading.value = true;
  try {
    const res = await api.get('/inventory', {
      params: {
        keyword: searchKeyword.value, category: categoryFilter.value || undefined,
        include_archived: showArchived.value ? 1 : 0,
        sort_by: sortBy.value, sort_order: sortOrder.value, page: page.value, limit: limit.value
      }
    });
    items.value = res.data.data;
    total.value = res.data.total;
    // 收集分类下拉选项（从当前页数据）
    const cats = new Set(categoryOptions.value);
    items.value.forEach(i => { if (i.category) cats.add(i.category); });
    categoryOptions.value = [...cats];
  } catch (e) {
    ElMessage.error(e.response?.data?.error || e.response?.data?.detail || '库存加载失败');
  } finally { loading.value = false; }
}

function tableRowClassName({ row }) {
  return row.id == highlightedId.value ? 'highlight-flash-row highlight-target-item' : '';
}
function handleSearch() { highlightedId.value = null; page.value = 1; fetchItems(); }
function handleSortChange({ prop, order }) {
  const newSortBy = order ? prop : 'created_at';
  const newSortOrder = order ? (order === 'ascending' ? 'asc' : 'desc') : 'desc';
  if (sortBy.value === newSortBy && sortOrder.value === newSortOrder) return;
  highlightedId.value = null; sortBy.value = newSortBy; sortOrder.value = newSortOrder; page.value = 1; fetchItems();
}

// ── 主数据 ──
function openCreate() { editing.value = null; Object.assign(form, { name:'', spec:'', category:categoryFilter.value||'', location:'', total:0, unit:'件', min_stock:5 }); formVisible.value = true; }
function openEdit(row) { editing.value = row; Object.assign(form, { name:row.name, spec:row.spec, category:row.category||'', location:row.location||'', total:row.total, unit:row.unit, min_stock:row.min_stock }); formVisible.value = true; }
async function save() {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    saving.value = true;
    try {
      if (editing.value) await api.put(`/inventory/${editing.value.id}`, form);
      else await api.post('/inventory', form);
      formVisible.value = false; await fetchItems(); ElMessage.success('保存成功');
    }
    catch (e) { ElMessage.error(e.response?.data?.error||e.response?.data?.detail||'保存失败'); }
    finally { saving.value = false; }
  });
}

async function confirmArchive(row) {
  try {
    await ElMessageBox.confirm(`归档「${row.name}」后不再出现在默认列表，但流水完整保留。确认归档？`, '归档确认', { type: 'warning' });
    await api.post(`/inventory/${row.id}/archive`);
    await fetchItems(); ElMessage.success('已归档');
  } catch (e) { if (e !== 'cancel') ElMessage.error(e.response?.data?.error || '归档失败'); }
}
async function confirmDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.name}」？有流水/引用的物料会被拒绝，请改用归档。`, '删除确认', { type: 'warning' });
    await api.delete(`/inventory/${row.id}`);
    await fetchItems(); ElMessage.success('已删除');
  } catch (e) { if (e !== 'cancel') ElMessage.error(e.response?.data?.error || '删除失败'); }
}

// ── 出入库 / 领退料 / 盘点 ──
async function ensureOrders() {
  ordersLoading.value = true;
  try {
    const res = await api.get('/orders');
    orders.value = res.data.data || [];
  } catch (e) {
    ElMessage.error('订单列表加载失败');
  } finally { ordersLoading.value = false; }
}
function openMovement(row, type) {
  movementItem.value = row; movementType.value = type;
  movementQty.value = 1; movementBatch.value = ''; movementNote.value = ''; movementOrderId.value = null;
  if (['OUTBOUND', 'RETURN', 'RESERVE'].includes(type)) ensureOrders();
  movementVisible.value = true;
}
function handleRowCommand(cmd, row) {
  if (cmd === 'RETURN') openMovement(row, 'RETURN');
  else if (cmd === 'RESERVE') openReserve(row);
  else if (cmd === 'STOCKTAKE') openStocktake(row);
  else if (cmd === 'EDIT') openEdit(row);
  else if (cmd === 'ARCHIVE') confirmArchive(row);
  else if (cmd === 'DELETE') confirmDelete(row);
}
async function submitMovement() {
  movementSaving.value = true;
  try {
    const res = await api.post(`/inventory/${movementItem.value.id}/movements`, {
      type: movementType.value,
      quantity: movementQty.value,
      batch_no: movementBatch.value,
      note: movementNote.value,
      order_id: ['OUTBOUND', 'RETURN'].includes(movementType.value) ? movementOrderId.value : null,
    });
    movementVisible.value = false;
    await fetchItems(true);
    ElMessage.success(`操作成功，当前可用 ${res.data.available} ${movementItem.value.unit}`);
  } catch (e) {
    ElMessage.error(e.response?.data?.error || e.response?.data?.detail || '操作失败');
  } finally { movementSaving.value = false; }
}
function openStocktake(row) { stocktakeItem.value = row; stocktakeQty.value = row.total; stocktakeVisible.value = true; }
async function submitStocktake() {
  movementSaving.value = true;
  try {
    const res = await api.post(`/inventory/${stocktakeItem.value.id}/movements`, {
      type: 'ADJUSTMENT', quantity: stocktakeQty.value, note: '库存盘点',
    });
    stocktakeVisible.value = false;
    await fetchItems(true);
    ElMessage.success(`盘点完成，当前可用 ${res.data.available} ${stocktakeItem.value.unit}`);
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '盘点失败');
  } finally { movementSaving.value = false; }
}

// ── Excel 导入导出（D9/D11） ──
async function exportExcel() {
  try {
    const res = await api.get('/inventory/export', {
      params: { keyword: searchKeyword.value || undefined },
      responseType: 'blob',
    });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement('a');
    a.href = url; a.download = 'inventory.xlsx'; a.click();
    URL.revokeObjectURL(url);
  } catch (e) { ElMessage.error(e.response?.data?.error || '导出失败'); }
}
async function importExcel(file) {
  const fd = new FormData();
  fd.append('file', file);
  try {
    const res = await api.post('/inventory/import', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
    const d = res.data;
    await fetchItems(true);
    if (d.failed_count > 0) {
      const listHtml = d.failed.map(f => `<li>第 ${f.row} 行：${f.reason}</li>`).join('');
      ElMessageBox.alert(
        `<p>成功导入 <b>${d.imported}</b> 条；失败 <b>${d.failed_count}</b> 条（好数据已入库，修正后可重传）：</p><ul style="max-height:220px;overflow:auto;font-size:12px;padding-left:16px">${listHtml}</ul>`,
        '导入结果（部分成功）',
        { dangerouslyUseHTMLString: true, confirmButtonText: '知道了' }
      ).catch(() => {});
    } else {
      ElMessage.success(`导入成功 ${d.imported} 条`);
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.error || e.response?.data?.detail || '导入失败');
  }
  return false; // 阻止 el-upload 默认行为
}

// ── 预留 ──
async function openReserve(row) {
  reserveItem.value = row;
  reserveOrderId.value = null;
  reserveQty.value = 1;
  reserveVisible.value = true;
  ensureOrders();
}
async function doReserve() {
  try {
    const res = await api.post('/inventory/reserve', { item_id: reserveItem.value.id, order_id: reserveOrderId.value, quantity: reserveQty.value });
    reserveVisible.value = false; await fetchItems(true);
    ElMessage.success(`预留成功，当前可用 ${res.data.available} ${reserveItem.value.unit}`);
  }
  catch (e) { ElMessage.error(e.response?.data?.error||'预留失败'); }
}

// ── 流水 ──
function movementLabel(t) { return { OPENING: '期初', INBOUND: '入库', OUTBOUND: '领料', RETURN: '退料', ADJUSTMENT: '盘点调整' }[t] || t; }
function movementTagType(t) { return { OPENING: 'info', INBOUND: 'success', OUTBOUND: 'warning', RETURN: 'primary', ADJUSTMENT: 'danger' }[t] || 'info'; }
async function openMovementsLog(row) {
  logItem.value = row; logVisible.value = true; logLoading.value = true;
  try {
    const res = await api.get(`/inventory/${row.id}/movements`);
    movements.value = res.data;
  } catch (e) {
    ElMessage.error('流水加载失败');
  } finally { logLoading.value = false; }
}
</script>

<style scoped>
</style>
