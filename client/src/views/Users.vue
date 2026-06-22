<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>用户管理</h2>
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建用户</el-button>
    </div>
    <el-table :data="users" border stripe v-loading="loading">
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="display_name" label="显示名" />
      <el-table-column prop="role_label" label="角色" />
      <el-table-column label="管理员" width="80">
        <template #default="{ row }">{{ row.is_admin ? '是' : '否' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">{{ row.is_active ? '启用' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="warning" @click="openPermissions(row)">权限</el-button>
          <el-button size="small" type="danger" @click="confirmDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="formVisible" :title="editing ? '编辑用户' : '新建用户'" width="440px">
      <el-form :model="form" label-width="70px">
        <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
        <el-form-item label="显示名"><el-input v-model="form.display_name" /></el-form-item>
        <el-form-item label="角色标签"><el-input v-model="form.role_label" placeholder="如：车间工人" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" :placeholder="editing ? '留空不修改' : '请输入密码'" /></el-form-item>
        <el-form-item label="管理员"><el-switch v-model="form.is_admin" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.is_active" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" @click="saveUser" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="permVisible" title="页面权限配置" width="700px">
      <el-table :data="permRows" border stripe>
        <el-table-column prop="label" label="页面" width="120" />
        <el-table-column label="可见" width="100" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.can_view" @change="onPermChange(row)" />
          </template>
        </el-table-column>
        <el-table-column label="可编辑" width="100" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.can_edit" :disabled="!row.can_view" @change="onPermChange(row)" />
          </template>
        </el-table-column>
        <el-table-column label="说明">
          <template #default="{ row }">
            <span v-if="!row.can_view" style="color:#909399">不可见</span>
            <span v-else-if="row.can_edit" style="color:#67c23a">可编辑</span>
            <span v-else style="color:#409eff">只读</span>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="permVisible = false">取消</el-button>
        <el-button type="primary" @click="savePermissions" :loading="permSaving">保存权限</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useAuthStore } from '../stores/auth.js';
import api from '../api/index.js';

const pages = [
  { key: 'dashboard', label: '仪表台' },
  { key: 'customers', label: '客户管理' },
  { key: 'orders', label: '订单管理' },
  { key: 'process_flow', label: '工艺流程' },
  { key: 'drawings', label: '图纸管理' },
  { key: 'inventory', label: '库存管理' },
  { key: 'users', label: '用户管理' },
  { key: 'notifications', label: '通知中心' },
  { key: 'settings', label: '系统设置' },
  { key: 'outsourcing', label: '外协管理' },
];

const users = ref([]);
const auth = useAuthStore();
const loading = ref(false);
const formVisible = ref(false);
const permVisible = ref(false);
const editing = ref(null);
const saving = ref(false);
const permSaving = ref(false);
const form = reactive({ username: '', display_name: '', role_label: '', password: '', is_admin: false, is_active: true });
const permRows = ref([]);
let permUserId = null;

onMounted(fetchUsers);

async function fetchUsers() { loading.value = true; try { const r = await api.get('/users'); users.value = r.data; } catch {} finally { loading.value = false; } }

function resetForm() { Object.assign(form, { username: '', display_name: '', role_label: '', password: '', is_admin: false, is_active: true }); }

function openCreate() { resetForm(); editing.value = null; formVisible.value = true; }

function openEdit(row) { editing.value = row; Object.assign(form, { username: row.username, display_name: row.display_name, role_label: row.role_label, password: '', is_admin: !!row.is_admin, is_active: !!row.is_active }); formVisible.value = true; }

async function saveUser() {
  saving.value = true;
  try {
    if (editing.value) {
      const body = { display_name: form.display_name, role_label: form.role_label, is_admin: form.is_admin, is_active: form.is_active, username: form.username };
      if (form.password) body.password = form.password;
      await api.put(`/users/${editing.value.id}`, body);
    } else {
      await api.post('/users', form);
    }
    formVisible.value = false;
    await fetchUsers();
    ElMessage.success('保存成功');
  } catch (e) { ElMessage.error(e.response?.data?.error || '保存失败'); }
  finally { saving.value = false; }
}

async function confirmDelete(row) {
  try { await ElMessageBox.confirm(`确定删除用户 ${row.username}？`, '确认', { type: 'warning' }); await api.delete(`/users/${row.id}`); await fetchUsers(); ElMessage.success('已删除'); }
  catch {}
}

async function openPermissions(row) {
  permUserId = row.id;
  const r = await api.get(`/users/${row.id}/permissions`);
  const current = r.data;
  permRows.value = pages.map((p) => {
    const saved = current.find((c) => c.page_key === p.key);
    return { page_key: p.key, label: p.label, can_view: saved?.can_view || false, can_edit: saved?.can_edit || false };
  });
  permVisible.value = true;
}

function onPermChange(row) {
  if (!row.can_view) row.can_edit = false;
}

async function savePermissions() {
  permSaving.value = true;
  try {
    await api.put(`/users/${permUserId}/permissions`, { permissions: permRows.value.map((r) => ({ page_key: r.page_key, can_view: r.can_view, can_edit: r.can_edit })) });
    permVisible.value = false;
    ElMessage.success('权限已更新');
  } catch (e) { ElMessage.error(e.response?.data?.error || '保存失败'); }
  finally { permSaving.value = false; }
}
</script>
