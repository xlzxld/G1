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
      <el-table-column prop="contact" label="联系人" width="100" />
      <el-table-column prop="phone" label="电话" width="130" />
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
        <el-form-item label="联系人"><el-input v-model="form.contact" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="微信"><el-input v-model="form.wechat" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" /></el-form-item>
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
const customers = ref([]);
const loading = ref(false);
const keyword = ref('');
const formVisible = ref(false);
const editing = ref(null);
const saving = ref(false);
const form = reactive({ name: '', contact: '', phone: '', address: '', wechat: '', email: '', notes: '' });

onMounted(fetchData);
async function fetchData() { loading.value = true; try { const r = await api.get('/customers', { params: { keyword: keyword.value } }); customers.value = r.data; } catch {} finally { loading.value = false; } }
function openCreate() { editing.value = null; Object.assign(form, { name: '', contact: '', phone: '', address: '', wechat: '', email: '', notes: '' }); formVisible.value = true; }
function openEdit(row) { editing.value = row; Object.assign(form, { name: row.name, contact: row.contact, phone: row.phone, address: row.address, wechat: row.wechat, email: row.email, notes: row.notes }); formVisible.value = true; }

async function save() {
  saving.value = true;
  try {
    if (editing.value) { await api.put(`/customers/${editing.value.id}`, form); } else { await api.post('/customers', form); }
    formVisible.value = false; await fetchData(); ElMessage.success('保存成功');
  } catch (e) { ElMessage.error(e.response?.data?.error || '保存失败'); }
  finally { saving.value = false; }
}

async function confirmDelete(row) {
  try { await ElMessageBox.confirm(`确定删除客户 ${row.name}？`, '确认', { type: 'warning' }); await api.delete(`/customers/${row.id}`); await fetchData(); ElMessage.success('已删除'); } catch {}
}
</script>
