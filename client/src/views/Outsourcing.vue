<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">外协管理</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">外协加工与供应商调度</p>
      </div>
      <el-button v-if="auth.canEdit('outsourcing')" type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新增厂商</el-button>
    </div>

    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-4 flex flex-wrap gap-3 items-center shadow-md">
      <el-input v-model="keyword" placeholder="搜索厂商" clearable class="w-full sm:w-60" @keyup.enter="handleSearch" />
      <el-button type="primary" @click="handleSearch" class="w-full sm:w-auto">搜索</el-button>
    </div>
    
    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl overflow-hidden shadow-md p-4">
      <!-- 桌面端表格 -->
      <el-table v-if="!isMobile" :data="vendors" border stripe v-loading="loading" :row-class-name="tableRowClassName">
        <el-table-column prop="name" label="厂商名称" min-width="160" />
        <el-table-column label="联系方式" min-width="200">
          <template #default="{ row }">
            <span v-for="(m, i) in parseMethods(row.contact_methods)" :key="i" style="margin-right:8px;">
              <el-tag size="small" type="info">{{ m.type }}</el-tag> <span class="text-slate-500 dark:text-slate-300 ml-1">{{ m.value }}</span>
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="address" label="地址" width="120" />
        <el-table-column prop="notes" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button v-if="auth.canEdit('outsourcing')" size="small" @click.stop="openEdit(row)">编辑</el-button>
            <el-button v-if="auth.canEdit('outsourcing')" size="small" type="danger" @click.stop="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 移动端卡片列表 -->
      <div v-else v-loading="loading" class="space-y-3 mt-2">
        <div
          v-for="row in vendors"
          :key="row.id"
          :class="['rounded-xl border p-4 shadow-sm transition-all', row.id == highlightedId ? 'highlight-flash-card-active highlight-target-item' : 'border-slate-200 dark:border-industrial-border bg-slate-50 dark:bg-industrial-900/50']"
        >
          <p class="text-slate-800 dark:text-slate-100 font-semibold text-base mb-2">{{ row.name }}</p>
          <div class="flex flex-wrap gap-1.5 mb-2">
            <span v-for="(m, i) in parseMethods(row.contact_methods)" :key="i" class="flex items-center gap-1">
              <el-tag size="small" type="info">{{ m.type }}</el-tag>
              <span class="text-xs text-slate-500 dark:text-slate-400">{{ m.value }}</span>
            </span>
          </div>
          <p v-if="row.address" class="text-xs text-slate-400 mb-1">地址：{{ row.address }}</p>
          <p v-if="row.notes" class="text-xs text-slate-400 mb-3">备注：{{ row.notes }}</p>
          <div v-if="auth.canEdit('outsourcing')" class="flex gap-2 border-t border-slate-200 dark:border-industrial-border pt-3">
            <el-button size="small" @click="openEdit(row)" class="flex-1">编辑</el-button>
            <el-button size="small" type="danger" @click="confirmDelete(row)" class="flex-1">删除</el-button>
          </div>
        </div>
        <div v-if="vendors.length === 0" class="py-16 text-center">
          <el-empty description="暂无厂商数据" />
        </div>
      </div>
    </div>

    <el-dialog v-model="formVisible" :title="editing ? '编辑厂商' : '新增厂商'" :width="isMobile ? '95vw' : '500px'">
      <el-form ref="formRef" :model="form" :rules="rules" :label-position="isMobile ? 'top' : 'right'" label-width="70px">
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" /></el-form-item>
        <el-divider content-position="left">联系方式 <span style="color:#f56c6c">*</span></el-divider>
        <div v-for="(m, i) in form.contact_methods" :key="i" style="display:flex;gap:8px;margin-bottom:12px;align-items:start">
          <el-form-item :prop="'contact_methods.' + i + '.type'" :rules="{ required: true, message: '类型必填', trigger: ['blur', 'change'] }">
            <el-select v-model="m.type" style="width:120px" placeholder="类型" allow-create filterable>
              <el-option v-for="t in contactTypes" :key="t" :value="t" :label="t" />
            </el-select>
          </el-form-item>
          <el-form-item :prop="'contact_methods.' + i + '.value'" :rules="{ required: true, message: '值必填', trigger: 'blur' }" style="flex:1">
            <el-input v-model="m.value" placeholder="值" />
          </el-form-item>
          <el-button :disabled="form.contact_methods.length <= 1" @click="form.contact_methods.splice(i,1)" type="danger" size="small" circle style="margin-top:2px;">×</el-button>
        </div>
        <el-button size="small" @click="form.contact_methods.push({type:'电话',value:''})">+ 添加联系方式</el-button>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" @click="save" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api/index.js';
import { useAuthStore } from '../stores/auth.js';

defineOptions({ name: 'Outsourcing' });

const isMobile = ref(window.innerWidth < 768);
function onResize() { isMobile.value = window.innerWidth < 768; }
window.addEventListener('resize', onResize);
onUnmounted(() => window.removeEventListener('resize', onResize));

const auth = useAuthStore();
const route = useRoute();
const vendors = ref([]); const loading = ref(false); const keyword = ref('');
const formVisible = ref(false); const editing = ref(null); const saving = ref(false);
const formRef = ref(null);
const highlightedId = ref(null);
const form = reactive({ name: '', address: '', notes: '', contact_methods: [{type:'电话',value:''}] });
const rules = { name: [{ required: true, message: '请输入厂商名称', trigger: 'blur' }] };
const contactTypes = ['电话', '微信', 'QQ', '邮箱', '传真'];

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

    const exists = vendors.value.some(o => o.id === targetId);
    if (exists) {
      triggerHighlightScroll();
      fetchData(true);
      return;
    }
  } else {
    highlightedId.value = null;
  }
  await fetchData(true);
  triggerHighlightScroll();
}, { immediate: true });

function tableRowClassName({ row }) {
  return row.id == highlightedId.value ? 'highlight-flash-row highlight-target-item' : '';
}

async function fetchData(silent = false) { 
  if (!silent || vendors.value.length === 0) {
    loading.value = true; 
  }
  try { 
    const r = await api.get('/vendors', { params: { keyword: keyword.value } }); 
    vendors.value = r.data; 
  } 
  catch {} 
  finally { loading.value = false; } 
}

function handleSearch() {
  highlightedId.value = null;
  fetchData();
}

function parseMethods(raw) { try { return typeof raw === 'string' ? JSON.parse(raw) : (raw || []); } catch { return []; } }
function openCreate() { editing.value = null; Object.assign(form, { name: '', address: '', notes: '', contact_methods: [{type:'电话',value:''}] }); formVisible.value = true; }
function openEdit(row) { editing.value = row; Object.assign(form, { name: row.name, address: row.address, notes: row.notes, contact_methods: parseMethods(row.contact_methods) }); if (form.contact_methods.length === 0) form.contact_methods.push({type:'电话',value:''}); formVisible.value = true; }
async function save() {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    saving.value = true;
    try {
      const body = { name: form.name, address: form.address, notes: form.notes, contact_methods: form.contact_methods.filter(m => m.value.trim()) };
      if (editing.value) { await api.put(`/vendors/${editing.value.id}`, body); } else { await api.post('/vendors', body); }
      formVisible.value = false; await fetchData(); ElMessage.success('保存成功');
    } catch (e) { ElMessage.error(e.response?.data?.error || e.response?.data?.detail || '保存失败'); }
    finally { saving.value = false; }
  });
}
async function confirmDelete(row) { try { await ElMessageBox.confirm(`确定删除厂商 ${row.name}？`, '确认', { type: 'warning' }); await api.delete(`/vendors/${row.id}`); await fetchData(); ElMessage.success('已删除'); } catch {} }
function formatDateTime(val) {
  if (!val) return '—';
  return val.slice(0, 16).replace('T', ' ');
}
</script>
