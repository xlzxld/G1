<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">库存管理</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">物料与库存状态管理</p>
      </div>
      <el-button v-if="auth.canEdit('inventory')" type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新增物料</el-button>
    </div>

    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-4 mb-6 flex flex-wrap gap-3 items-center shadow-sm">
      <el-input v-model="searchKeyword" placeholder="搜索物料名称或规格" clearable class="w-full sm:w-72" @input="debouncedSearch" @clear="handleSearch" @keyup.enter="handleSearch">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button type="primary" @click="handleSearch" class="w-full sm:w-auto">搜索</el-button>
    </div>

    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl overflow-hidden shadow-md p-4">
      <!-- 桌面端表格 -->
      <el-table v-if="!isMobile" :data="items" border stripe v-loading="loading" @sort-change="handleSortChange" :row-class-name="tableRowClassName">
        <el-table-column prop="name" label="名称" min-width="140" sortable="custom" />
        <el-table-column prop="spec" label="规格" width="120" sortable="custom" />
        <el-table-column prop="total" label="总量" width="95" align="center" sortable="custom">
          <template #default="{row}">
            <span :style="{color:row.total<=row.alert_threshold?'#f56c6c':''}" :class="row.total<=row.alert_threshold?'font-bold':''">{{ row.total }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="reserved" label="已预留" width="95" align="center" sortable="custom" />
        <el-table-column label="可用" width="90" align="center">
          <template #default="{row}">{{ row.total - row.reserved }}</template>
        </el-table-column>
        <el-table-column prop="unit" label="单位" width="60" />
        <el-table-column label="操作" width="240">
          <template #default="{row}">
            <el-button v-if="auth.canEdit('inventory')" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="auth.canEdit('inventory')" size="small" type="warning" @click="openReserve(row)">预留</el-button>
            <el-button v-if="auth.canEdit('inventory')" size="small" type="danger" @click="confirmDelete(row)">删除</el-button>
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
            </div>
            <el-tag v-if="row.total <= row.alert_threshold" type="danger" size="small">库存预警</el-tag>
          </div>
          <div class="grid grid-cols-3 gap-2 text-sm mb-3">
            <div class="text-center bg-white dark:bg-industrial-800 rounded-lg p-2 border border-slate-200 dark:border-industrial-border">
              <p :class="['font-bold text-lg', row.total <= row.alert_threshold ? 'text-red-500' : 'text-slate-800 dark:text-slate-100']">{{ row.total }}</p>
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
          <div v-if="auth.canEdit('inventory')" class="flex gap-2 border-t border-slate-200 dark:border-industrial-border pt-3">
            <el-button size="small" @click="openEdit(row)" class="flex-1">编辑</el-button>
            <el-button size="small" type="warning" @click="openReserve(row)" class="flex-1">预留</el-button>
            <el-button size="small" type="danger" @click="confirmDelete(row)" class="flex-1">删除</el-button>
          </div>
        </div>
        <div v-if="items.length === 0" class="py-16 text-center">
          <el-empty description="暂无物料数据" />
        </div>
      </div>

      <div class="mt-4 flex justify-end overflow-x-auto">
        <el-pagination background :layout="isMobile ? 'total, prev, pager, next' : 'total, sizes, prev, pager, next'" :total="total" v-model:current-page="page" v-model:page-size="limit" :page-sizes="[10, 20, 50]" @current-change="fetchItems" @size-change="fetchItems" :small="isMobile" />
      </div>
    </div>

    <el-dialog v-model="formVisible" :title="editing?'编辑物料':'新增物料'" :width="isMobile ? '95vw' : '440px'">
      <el-form ref="formRef" :model="form" :rules="rules" :label-position="isMobile ? 'top' : 'right'" label-width="80px">
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="规格"><el-input v-model="form.spec" /></el-form-item>
        <el-form-item label="总量" prop="total"><el-input-number v-model="form.total" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="单位"><el-input v-model="form.unit" /></el-form-item>
        <el-form-item label="预警阈値"><el-input-number v-model="form.alert_threshold" :min="0" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="formVisible=false">取消</el-button><el-button type="primary" @click="save" :loading="saving">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="reserveVisible" title="预留物料" :width="isMobile ? '95vw' : '440px'">
      <el-form :label-position="isMobile ? 'top' : 'right'" label-width="80px">
        <el-form-item label="物料">{{ reserveItem?.name }}</el-form-item>
        <el-form-item label="订单"><el-select v-model="reserveOrderId" filterable :loading="ordersLoading" placeholder="选择订单" style="width:100%"><el-option v-for="o in orders" :key="o.id" :label="`${o.order_no} ${o.product_name}`" :value="o.id" /></el-select></el-form-item>
        <el-form-item label="数量"><el-input-number v-model="reserveQty" :min="1" :max="(reserveItem?.total||0)-(reserveItem?.reserved||0)" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="reserveVisible=false">取消</el-button><el-button type="primary" @click="doReserve">确认预留</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch, nextTick, onActivated } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api/index.js';
import { useAuthStore } from '../stores/auth.js';
import { debounce } from '../utils/debounce.js';

defineOptions({ name: 'Inventory' });

const isMobile = ref(window.innerWidth < 768);
function onResize() { isMobile.value = window.innerWidth < 768; }
window.addEventListener('resize', onResize);
const route = useRoute();
const auth = useAuthStore();
const items = ref([]);
const total = ref(0);
const loading = ref(false);
const orders = ref([]);
const ordersLoading = ref(false);
const formVisible = ref(false);
const editing = ref(null);
const saving = ref(false);
const formRef = ref(null);
const form = reactive({ name:'', spec:'', total:0, unit:'件', alert_threshold:5 });
const rules = {
  name: [{ required: true, message: '请输入物料名称', trigger: 'blur' }],
  total: [{ required: true, message: '总量不能为空', trigger: 'change' }]
};
const reserveVisible = ref(false);
const reserveItem = ref(null);
const reserveOrderId = ref(null);
const reserveQty = ref(1);
const searchKeyword = ref('');
const sortBy = ref('created_at');
const sortOrder = ref('desc');
const page = ref(1);
const limit = ref(20);
const highlightedId = ref(null);

const debouncedSearch = debounce(handleSearch, 300);

onMounted(() => {
  // 首屏依赖下沉至 watch immediate
});

onActivated(() => {
  if (items.value.length > 0) {
    fetchItems(true); // 切换页面时背景静默刷新，不阻塞页面也不出遮罩
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
    // 重置 highlight 触发 DOM 重新挂载动画，解决动画不重放的问题
    highlightedId.value = null;
    await nextTick();
    highlightedId.value = targetId;

    const exists = items.value.some(o => o.id === targetId);
    if (exists) {
      triggerHighlightScroll(); // 0 延迟立刻滚动并高亮
      locateInventoryPage(targetId).then(() => fetchItems(true)); // 后台静默兜底刷新
      return;
    }
    
    await locateInventoryPage(targetId);
  } else {
    highlightedId.value = null;
  }
  await fetchItems(true); // 使用静默加载，确保首屏及切换没有多余的转圈闪烁
  triggerHighlightScroll();
}, { immediate: true });

async function locateInventoryPage(targetId) {
  try {
    const res = await api.get(`/inventory/${targetId}/locate`, {
      params: {
        limit: limit.value,
        keyword: searchKeyword.value,
        sort_by: sortBy.value,
        sort_order: sortOrder.value
      }
    });
    if (res.data && res.data.page !== undefined) {
      page.value = res.data.page;
    } else {
      highlightedId.value = null;
    }
  } catch (e) {
    console.error('Locate inventory page failed:', e);
  }
}

async function fetchItems(silent = false) {
  if (!silent || items.value.length === 0) {
    loading.value = true;
  }
  try {
    const res = await api.get('/inventory', {
      params: { keyword: searchKeyword.value, sort_by: sortBy.value, sort_order: sortOrder.value, page: page.value, limit: limit.value }
    });
    if (res.data && res.data.data !== undefined) {
      items.value = res.data.data;
      total.value = res.data.total;
    } else {
      items.value = res.data;
      total.value = res.data.length;
    }
  } catch {}
  finally { loading.value = false; }
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
function openCreate() { editing.value = null; Object.assign(form, { name:'', spec:'', total:0, unit:'件', alert_threshold:5 }); formVisible.value = true; }
function openEdit(row) { editing.value = row; Object.assign(form, { name:row.name, spec:row.spec, total:row.total, unit:row.unit, alert_threshold:row.alert_threshold }); formVisible.value = true; }
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
async function confirmDelete(row) {
  try { await ElMessageBox.confirm(`确定删除 ${row.name}？`,'确认',{type:'warning'}); await api.delete(`/inventory/${row.id}`); await fetchItems(); ElMessage.success('已删除'); } catch {}
}
async function openReserve(row) { 
  reserveItem.value = row; 
  reserveOrderId.value = null; 
  reserveQty.value = 1; 
  reserveVisible.value = true;
  
  ordersLoading.value = true;
  try {
    const res = await api.get('/orders');
    orders.value = res.data.data || [];
  } catch (e) {
    console.error("加载订单失败", e);
  } finally {
    ordersLoading.value = false;
  }
}
async function doReserve() {
  try { await api.post('/inventory/reserve', { item_id: reserveItem.value.id, order_id: reserveOrderId.value, quantity: reserveQty.value }); reserveVisible.value = false; await fetchItems(); ElMessage.success('预留成功'); }
  catch (e) { ElMessage.error(e.response?.data?.error||'预留失败'); }
}
</script>

<style scoped>
</style>