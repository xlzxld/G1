<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>客户管理</h2>
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建客户</el-button>
    </div>
    <div class="search-bar" style="margin-bottom:12px">
      <el-input v-model="keyword" placeholder="搜索客户" clearable style="width:240px" @keyup.enter="fetchData" />
      <el-button type="primary" style="margin-left:8px" @click="fetchData">搜索</el-button>
    </div>
    <el-table :data="customers" border stripe v-loading="loading" @row-click="row => router.push(`/customers/${row.id}`)" style="cursor:pointer">
      <el-table-column prop="name" label="客户名称" min-width="160" />
      <el-table-column label="联系方式" min-width="200">
        <template #default="{ row }">
          <span v-for="(m, i) in parseMethods(row.contact_methods)" :key="i" style="margin-right:8px;">
            <el-tag size="small" type="info">{{ m.type }}</el-tag> {{ m.value }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="address" label="地址" width="120" />
      <el-table-column prop="created_at" label="创建时间" width="120" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" @click.stop="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click.stop="confirmDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="formVisible" :title="editing ? '编辑客户' : '新建客户'" width="500px">
      <el-form :model="form" label-width="70px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" /></el-form-item>
        <el-divider content-position="left">联系方式 <span style="color:#f56c6c">*</span></el-divider>
        <div v-for="(m, i) in form.contact_methods" :key="i" style="display:flex;gap:8px;margin-bottom:8px;align-items:center">
          <el-select v-model="m.type" style="width:120px" placeholder="类型">
            <el-option v-for="t in contactTypes" :key="t" :value="t" :label="t" />
            <el-option value="__custom__" label="自定义...">
              <template #default>
                <el-input v-model="customType" placeholder="输入类型" size="small" @click.stop />
              </template>
            </el-option>
          </el-select>
          <el-input v-model="m.value" placeholder="值" style="flex:1" />
          <el-button :disabled="form.contact_methods.length <= 1" @click="form.contact_methods.splice(i,1)" type="danger" size="small" circle>×</el-button>
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

const router = useRouter();
const customers = ref([]); const loading = ref(false); const keyword = ref('');
const formVisible = ref(false); const editing = ref(null); const saving = ref(false);
const form = reactive({ name: '', address: '', notes: '', contact_methods: [{type:'电话',value:''}] });
const contactTypes = ['电话', '微信', 'QQ', '邮箱', '联系人', '传真', '地址'];

onMounted(fetchData);
async function fetchData() { loading.value = true; try { const r = await api.get('/customers', { params: { keyword: keyword.value } }); customers.value = r.data; } catch {} finally { loading.value = false; } }
function parseMethods(raw) { try { return typeof raw === 'string' ? JSON.parse(raw) : (raw || []); } catch { return []; } }
function openCreate() { editing.value = null; Object.assign(form, { name: '', address: '', notes: '', contact_methods: [{type:'电话',value:''}] }); formVisible.value = true; }
function openEdit(row) { editing.value = row; Object.assign(form, { name: row.name, address: row.address, notes: row.notes, contact_methods: parseMethods(row.contact_methods) }); if (form.contact_methods.length === 0) form.contact_methods.push({type:'电话',value:''}); formVisible.value = true; }
async function save() {
  saving.value = true;
  try {
    const body = { name: form.name, address: form.address, notes: form.notes, contact_methods: form.contact_methods.filter(m => m.value.trim()) };
    if (editing.value) { await api.put(`/customers/${editing.value.id}`, body); } else { await api.post('/customers', body); }
    formVisible.value = false; await fetchData(); ElMessage.success('保存成功');
  } catch (e) { ElMessage.error(e.response?.data?.error || '保存失败'); }
  finally { saving.value = false; }
}
async function confirmDelete(row) { try { await ElMessageBox.confirm(`确定删除客户 ${row.name}？`, '确认', { type: 'warning' }); await api.delete(`/customers/${row.id}`); await fetchData(); ElMessage.success('已删除'); } catch {} }
</script>
