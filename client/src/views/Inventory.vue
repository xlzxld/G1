<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>库存管理</h2>
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新增物料</el-button>
    </div>
    <el-table :data="items" border stripe v-loading="loading">
      <el-table-column prop="name" label="名称" min-width="140" />
      <el-table-column prop="spec" label="规格" width="120" />
      <el-table-column label="总量" width="80" align="center"><template #default="{row}"><span :style="{color:row.total<=row.alert_threshold?'#f56c6c':''}">{{ row.total }}</span></template></el-table-column>
      <el-table-column prop="reserved" label="已预留" width="80" align="center" />
      <el-table-column label="可用" width="80" align="center"><template #default="{row}">{{ row.total - row.reserved }}</template></el-table-column>
      <el-table-column prop="unit" label="单位" width="60" />
      <el-table-column label="操作" width="240">
        <template #default="{row}">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="warning" @click="openReserve(row)">预留</el-button>
          <el-button size="small" type="danger" @click="confirmDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="formVisible" :title="editing?'编辑物料':'新增物料'" width="440px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="规格"><el-input v-model="form.spec" /></el-form-item>
        <el-form-item label="总量"><el-input-number v-model="form.total" :min="0" /></el-form-item>
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
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api/index.js';

const items = ref([]); const loading = ref(false); const orders = ref([]);
const formVisible = ref(false); const editing = ref(null); const saving = ref(false);
const form = reactive({ name:'', spec:'', total:0, unit:'件', alert_threshold:5 });
const reserveVisible = ref(false); const reserveItem = ref(null); const reserveOrderId = ref(null); const reserveQty = ref(1);

onMounted(async () => { fetchItems(); try { orders.value = (await api.get('/orders')).data.data; } catch {} });
async function fetchItems() { loading.value = true; try { items.value = (await api.get('/inventory')).data; } catch {} finally { loading.value = false; } }

function openCreate() { editing.value = null; Object.assign(form, { name:'', spec:'', total:0, unit:'件', alert_threshold:5 }); formVisible.value = true; }
function openEdit(row) { editing.value = row; Object.assign(form, { name:row.name, spec:row.spec, total:row.total, unit:row.unit, alert_threshold:row.alert_threshold }); formVisible.value = true; }
async function save() {
  saving.value = true;
  try { if (editing.value) await api.put(`/inventory/${editing.value.id}`, form); else await api.post('/inventory', form); formVisible.value = false; await fetchItems(); ElMessage.success('保存成功'); }
  catch (e) { ElMessage.error(e.response?.data?.error||'保存失败'); } finally { saving.value = false; }
}
async function confirmDelete(row) { try { await ElMessageBox.confirm(`确定删除 ${row.name}？`,'确认',{type:'warning'}); await api.delete(`/inventory/${row.id}`); await fetchItems(); ElMessage.success('已删除'); } catch {} }
function openReserve(row) { reserveItem.value = row; reserveOrderId.value = null; reserveQty.value = 1; reserveVisible.value = true; }
async function doReserve() {
  try { await api.post('/inventory/reserve', { item_id: reserveItem.value.id, order_id: reserveOrderId.value, quantity: reserveQty.value }); reserveVisible.value = false; await fetchItems(); ElMessage.success('预留成功'); }
  catch (e) { ElMessage.error(e.response?.data?.error||'预留失败'); }
}
</script>
