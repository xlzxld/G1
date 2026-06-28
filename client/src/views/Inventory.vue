<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">库存管理</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">物料与库存状态管理</p>
      </div>
      <el-button v-if="auth.canEdit('inventory')" type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新增物料</el-button>
    </div>

    <!-- 过滤工具栏 -->
    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-4 mb-6 flex justify-between items-center shadow-sm">
      <div class="flex items-center gap-3">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索物料名称或规格"
          clearable
          style="width: 280px"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
      </div>
    </div>

    <el-table :data="items" border stripe v-loading="loading" @sort-change="handleSortChange" :row-class-name="tableRowClassName">
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

    <el-dialog v-model="formVisible" :title="editing?'编辑物料':'新增物料'" width="440px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="规格"><el-input v-model="form.spec" /></el-form-item>
        <el-form-item label="总量" prop="total"><el-input-number v-model="form.total" :min="0" /></el-form-item>
        <el-form-item label="单位"><el-input v-model="form.unit" /></el-form-item>
        <el-form-item label="预警阈值"><el-input-number v-model="form.alert_threshold" :min="0" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="formVisible=false">取消</el-button><el-button type="primary" @click="save" :loading="saving">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="reserveVisible" title="预留物料" width="440px">
      <el-form label-width="80px">
        <el-form-item label="物料">{{ reserveItem?.name }}</el-form-item>
        <el-form-item label="订单"><el-select v-model="reserveOrderId" filterable placeholder="选择订单"><el-option v-for="o in orders" :key="o.id" :label="`${o.order_no} ${o.product_name}`" :value="o.id" /></el-select></el-form-item>
        <el-form-item label="数量"><el-input-number v-model="reserveQty" :min="1" :max="(reserveItem?.total||0)-(reserveItem?.reserved||0)" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="reserveVisible=false">取消</el-button><el-button type="primary" @click="doReserve">确认预留</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api/index.js';
import { useAuthStore } from '../stores/auth.js';

const route = useRoute();
const auth = useAuthStore();
const items = ref([]); const loading = ref(false); const orders = ref([]);
const formVisible = ref(false); const editing = ref(null); const saving = ref(false);
const formRef = ref(null);
const form = reactive({ name:'', spec:'', total:0, unit:'件', alert_threshold:5 });
const rules = {
  name: [{ required: true, message: '请输入物料名称', trigger: 'blur' }],
  total: [{ required: true, message: '总量不能为空', trigger: 'change' }]
};
const reserveVisible = ref(false); const reserveItem = ref(null); const reserveOrderId = ref(null); const reserveQty = ref(1);

// 查询与排序状态
const searchKeyword = ref('');
const sortBy = ref('created_at');
const sortOrder = ref('desc');

const highlightedId = ref(null);

onMounted(async () => { 
  if (route.query.highlight) {
    highlightedId.value = parseInt(route.query.highlight);
  }
  fetchItems(); 
  try { orders.value = (await api.get('/orders')).data.data; } catch {} 
});

watch(() => route.query.highlight, (newVal) => {
  if (newVal) {
    highlightedId.value = parseInt(newVal);
    fetchItems();
  } else {
    highlightedId.value = null;
  }
});

async function fetchItems() { 
  loading.value = true; 
  try { 
    const res = await api.get('/inventory', {
      params: {
        keyword: searchKeyword.value,
        sort_by: sortBy.value,
        sort_order: sortOrder.value
      }
    });
    items.value = res.data; 
    
    if (highlightedId.value) {
      const idx = items.value.findIndex(x => x.id === highlightedId.value);
      if (idx !== -1) {
        await nextTick();
        let attempts = 0;
        const scrollInterval = setInterval(() => {
          const el = document.querySelector('.highlight-flash-row');
          attempts++;
          if (el) {
            clearInterval(scrollInterval);
            setTimeout(() => {
              el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 100);
          } else if (attempts >= 20) {
            clearInterval(scrollInterval);
          }
        }, 100);
      } else {
        ElMessage.warning("该通知对应的物料不存在或已被删除！");
        highlightedId.value = null;
      }
    }
  } catch {} 
  finally { loading.value = false; } 
}

function tableRowClassName({ row }) {
  return row.id == highlightedId.value ? 'highlight-flash-row' : '';
}

function handleSearch() {
  highlightedId.value = null;
  fetchItems();
}

function handleSortChange({ prop, order }) {
  const newSortBy = order ? prop : 'created_at';
  const newSortOrder = order ? (order === 'ascending' ? 'asc' : 'desc') : 'desc';
  if (sortBy.value === newSortBy && sortOrder.value === newSortOrder) {
    return;
  }
  highlightedId.value = null;
  sortBy.value = newSortBy;
  sortOrder.value = newSortOrder;
  fetchItems();
}

function openCreate() { editing.value = null; Object.assign(form, { name:'', spec:'', total:0, unit:'件', alert_threshold:5 }); formVisible.value = true; }
function openEdit(row) { editing.value = row; Object.assign(form, { name:row.name, spec:row.spec, total:row.total, unit:row.unit, alert_threshold:row.alert_threshold }); formVisible.value = true; }
async function save() {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    saving.value = true;
    try { if (editing.value) await api.put(`/inventory/${editing.value.id}`, form); else await api.post('/inventory', form); formVisible.value = false; await fetchItems(); ElMessage.success('保存成功'); }
    catch (e) { ElMessage.error(e.response?.data?.error||e.response?.data?.detail||'保存失败'); } finally { saving.value = false; }
  });
}
async function confirmDelete(row) { try { await ElMessageBox.confirm(`确定删除 ${row.name}？`,'确认',{type:'warning'}); await api.delete(`/inventory/${row.id}`); await fetchItems(); ElMessage.success('已删除'); } catch {} }
function openReserve(row) { reserveItem.value = row; reserveOrderId.value = null; reserveQty.value = 1; reserveVisible.value = true; }
async function doReserve() {
  try { await api.post('/inventory/reserve', { item_id: reserveItem.value.id, order_id: reserveOrderId.value, quantity: reserveQty.value }); reserveVisible.value = false; await fetchItems(); ElMessage.success('预留成功'); }
  catch (e) { ElMessage.error(e.response?.data?.error||'预留失败'); }
}
</script>

<style scoped>
@keyframes row-flash {
  0%, 100% {
    background-color: transparent;
  }
  25%, 75% {
    background-color: rgba(64, 158, 255, 0.25);
  }
}
:deep(.el-table tbody tr.highlight-flash-row) {
  --el-table-tr-bg-color: transparent !important;
}
:deep(.el-table tbody tr.highlight-flash-row td.el-table__cell) {
  animation: row-flash 1.5s ease-in-out 3;
  border-bottom: 2px solid rgba(64, 158, 255, 0.5) !important;
  border-top: 2px solid rgba(64, 158, 255, 0.5) !important;
}
</style>
