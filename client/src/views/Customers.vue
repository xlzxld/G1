<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">客户管理</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">客户与联系人管理</p>
      </div>
      <el-button v-if="auth.canEdit('customers')" type="primary" @click="openCreate" color="#7aa2f7" dark><el-icon><Plus /></el-icon> 新建客户</el-button>
    </div>

    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-4 flex flex-wrap gap-3 items-center shadow-md">
      <el-input v-model="keyword" placeholder="搜索客户" clearable style="width:240px" @keyup.enter="fetchData" />
      <el-button type="primary" @click="fetchData" color="#7aa2f7" dark>搜索</el-button>
    </div>
    
    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl overflow-hidden shadow-md p-4">
    <el-table :data="customers" border stripe v-loading="loading" @row-click="row => router.push(`/customers/${row.id}`)" style="cursor:pointer">
      <el-table-column prop="name" label="客户名称" min-width="160" />
      <el-table-column label="联系方式" min-width="200">
        <template #default="{ row }">
          <span v-for="(m, i) in parseMethods(row.contact_methods)" :key="i" style="margin-right:8px;">
            <el-tag size="small" type="info">{{ m.type }}</el-tag> <span class="text-slate-300 ml-1">{{ m.value }}</span>
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="address" label="地址" width="120" />
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button v-if="auth.canEdit('customers')" size="small" @click.stop="openEdit(row)">编辑</el-button>
          <el-button v-if="auth.canEdit('customers')" size="small" type="danger" @click.stop="confirmDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    </div>

    <el-dialog v-model="formVisible" :title="editing ? '编辑客户' : '新建客户'" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="70px">
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
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api/index.js';

import { useAuthStore } from '../stores/auth.js';

const auth = useAuthStore();
const router = useRouter();
const customers = ref([]); const loading = ref(false); const keyword = ref('');
const formVisible = ref(false); const editing = ref(null); const saving = ref(false);
const formRef = ref(null);
const form = reactive({ name: '', address: '', notes: '', contact_methods: [{type:'电话',value:''}] });
const rules = { name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }] };
const contactTypes = ['电话', '微信', 'QQ', '邮箱', '传真'];

onMounted(fetchData);
async function fetchData() { loading.value = true; try { const r = await api.get('/customers', { params: { keyword: keyword.value } }); customers.value = r.data; } catch {} finally { loading.value = false; } }
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
      if (editing.value) { await api.put(`/customers/${editing.value.id}`, body); } else { await api.post('/customers', body); }
      formVisible.value = false; await fetchData(); ElMessage.success('保存成功');
    } catch (e) { ElMessage.error(e.response?.data?.error || e.response?.data?.detail || '保存失败'); }
    finally { saving.value = false; }
  });
}
async function confirmDelete(row) { try { await ElMessageBox.confirm(`确定删除客户 ${row.name}？`, '确认', { type: 'warning' }); await api.delete(`/customers/${row.id}`); await fetchData(); ElMessage.success('已删除'); } catch {} }
function formatDateTime(val) {
  if (!val) return '—';
  return val.slice(0, 16).replace('T', ' ');
}
</script>
