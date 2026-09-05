<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">BOM 用料模板</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">建单时按产品类型自动带出用料并批量预留</p>
      </div>
      <el-button v-if="auth.isAdmin" type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建模板</el-button>
    </div>

    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-4 mb-6 flex flex-wrap gap-3 items-center shadow-sm">
      <el-input v-model="keyword" placeholder="搜索模板名称" clearable class="w-full sm:w-64" @keyup.enter="fetchBoms" @clear="fetchBoms">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button type="primary" @click="fetchBoms">搜索</el-button>
    </div>

    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl shadow-md p-4" v-loading="loading">
      <el-table :data="boms" border stripe>
        <el-table-column prop="name" label="模板名称" min-width="160" />
        <el-table-column prop="product_type" label="产品类型" width="140">
          <template #default="{row}"><el-tag size="small">{{ row.product_type }}</el-tag></template>
        </el-table-column>
        <el-table-column label="用料" min-width="260">
          <template #default="{row}">
            <span class="text-xs text-slate-500">{{ (row.items || []).map(i => `${i.item_name}×${i.quantity_per_set}`).join('、') || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{row}">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" v-if="auth.isAdmin">
          <template #default="{row}">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="boms.length === 0" class="py-12">
        <el-empty description="还没有 BOM 模板——新建一个，建单时即可自动带出用料" />
      </div>
    </div>

    <el-dialog v-model="formVisible" :title="editing ? '编辑模板' : '新建模板'" :width="isMobile ? '95vw' : '720px'">
      <el-form :model="form" :label-position="isMobile ? 'top' : 'right'" label-width="90px">
        <el-form-item label="模板名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="产品类型" required>
          <el-select v-model="form.product_type" filterable allow-create default-first-option placeholder="选择已有类型或输入新类型" style="width:100%">
            <el-option v-for="t in productTypes" :key="t" :label="t" :value="t" />
          </el-select>
          <p class="text-xs text-slate-400 mt-1">类型在 BOM 与订单两端统一管理，避免自由文本导致的静默失配</p>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.note" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.is_active" /></el-form-item>
        <el-form-item label="用料清单">
          <div class="w-full space-y-2">
            <div v-for="(it, idx) in form.items" :key="idx" class="flex gap-2 items-center">
              <el-select v-model="it.item_id" filterable placeholder="选择物料" style="flex:2">
                <el-option v-for="i in itemOptions" :key="i.id" :label="`${i.name}（可用 ${i.total - i.reserved} ${i.unit}）`" :value="i.id" :disabled="i.is_archived" />
              </el-select>
              <el-input-number v-model="it.quantity_per_set" :min="1" style="width:120px" />
              <el-button type="danger" text @click="form.items.splice(idx, 1)">移除</el-button>
            </div>
            <el-button size="small" @click="form.items.push({ item_id: null, quantity_per_set: 1, note: '' })">+ 添加一行</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="formVisible=false">取消</el-button><el-button type="primary" @click="save" :loading="saving">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api/index.js';
import { useAuthStore } from '../stores/auth.js';
import { Plus, Search } from '@element-plus/icons-vue';

defineOptions({ name: 'Bom' });

const isMobile = ref(window.innerWidth < 768);
const auth = useAuthStore();
const boms = ref([]);
const loading = ref(false);
const keyword = ref('');
const formVisible = ref(false);
const editing = ref(null);
const saving = ref(false);
const productTypes = ref([]);
const itemOptions = ref([]);
const form = reactive({ name: '', product_type: '', note: '', is_active: true, items: [] });

async function fetchBoms() {
  loading.value = true;
  try {
    const res = await api.get('/boms', { params: { keyword: keyword.value } });
    boms.value = res.data;
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '模板加载失败');
  } finally { loading.value = false; }
}
async function fetchProductTypes() {
  try { productTypes.value = (await api.get('/boms/product-types')).data; } catch (e) { console.error(e); }
}
async function fetchItems() {
  try {
    const res = await api.get('/inventory', { params: { limit: 1000 } });
    itemOptions.value = Array.isArray(res.data) ? res.data : res.data.data;
  } catch (e) { console.error(e); }
}
function openCreate() {
  editing.value = null;
  Object.assign(form, { name: '', product_type: '', note: '', is_active: true, items: [{ item_id: null, quantity_per_set: 1, note: '' }] });
  fetchProductTypes(); fetchItems();
  formVisible.value = true;
}
function openEdit(row) {
  editing.value = row;
  Object.assign(form, {
    name: row.name, product_type: row.product_type, note: row.note || '',
    is_active: !!row.is_active,
    items: (row.items || []).map(i => ({ item_id: i.item_id, quantity_per_set: i.quantity_per_set, note: i.note || '' })),
  });
  fetchProductTypes(); fetchItems();
  formVisible.value = true;
}
async function save() {
  if (!form.name.trim()) return ElMessage.error('请填写模板名称');
  if (!form.product_type.trim()) return ElMessage.error('请选择产品类型');
  if (!form.items.length || form.items.some(i => !i.item_id)) return ElMessage.error('用料清单存在未选择物料的行');
  saving.value = true;
  try {
    const payload = { ...form, items: form.items };
    if (editing.value) await api.put(`/boms/${editing.value.id}`, payload);
    else await api.post('/boms', payload);
    formVisible.value = false;
    await fetchBoms();
    ElMessage.success('保存成功');
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '保存失败');
  } finally { saving.value = false; }
}
async function confirmDelete(row) {
  try {
    await ElMessageBox.confirm(`删除模板「${row.name}」？`, '确认', { type: 'warning' });
    await api.delete(`/boms/${row.id}`);
    await fetchBoms();
    ElMessage.success('已删除');
  } catch (e) { if (e !== 'cancel') ElMessage.error(e.response?.data?.error || '删除失败'); }
}

onMounted(fetchBoms);
</script>
