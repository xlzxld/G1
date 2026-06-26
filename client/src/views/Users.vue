<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">用户管理</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">系统用户与权限分配</p>
      </div>
      <el-button v-if="auth.isAdmin" type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建用户</el-button>
    </div>
    <el-table :data="users" border stripe v-loading="loading">
      <el-table-column prop="username" label="用户名" />
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
          <el-button v-if="auth.isAdmin" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="auth.isAdmin" size="small" type="warning" @click="openPermissions(row)">权限</el-button>
          <el-button v-if="auth.isAdmin" size="small" type="danger" @click="confirmDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="formVisible" :title="editing ? '编辑用户' : '新建用户'" width="440px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="70px">
        <el-form-item label="用户名" prop="username"><el-input v-model="form.username" /></el-form-item>
        <el-form-item label="密码" prop="password"><el-input v-model="form.password" type="password" :placeholder="editing ? '留空不修改' : '请输入密码'" /></el-form-item>
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
            <el-switch v-model="row.can_view" :disabled="isSwitchDisabled(row)" @change="onPermChange(row)" />
          </template>
        </el-table-column>
        <el-table-column label="可编辑" width="100" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.can_edit" :disabled="!row.can_view || isSwitchDisabled(row)" @change="onPermChange(row)" />
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
  { key: 'inventory', label: '库存管理' },
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
const formRef = ref(null);
const form = reactive({ username: '', password: '', is_admin: false, is_active: true });
const rules = reactive({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入初始密码', trigger: 'blur' }]
});
const permRows = ref([]);
const permUserId = ref(null);
const permUser = ref(null);

onMounted(fetchUsers);

async function fetchUsers() { loading.value = true; try { const r = await api.get('/users'); users.value = r.data; } catch {} finally { loading.value = false; } }

function resetForm() { Object.assign(form, { username: '', password: '', is_admin: false, is_active: true }); rules.password[0].required = true; }

function openCreate() { resetForm(); editing.value = null; formVisible.value = true; }

function openEdit(row) { editing.value = row; Object.assign(form, { username: row.username, password: '', is_admin: !!row.is_admin, is_active: !!row.is_active }); rules.password[0].required = false; formVisible.value = true; }

async function saveUser() {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    saving.value = true;
    try {
      if (editing.value) {
        const body = { is_admin: form.is_admin, is_active: form.is_active, username: form.username, display_name: '', role_label: '' };
        if (form.password) body.password = form.password;
        await api.put(`/users/${editing.value.id}`, body);
      } else {
        const body = { ...form, display_name: '', role_label: '' };
        await api.post('/users', body);
      }
      formVisible.value = false;
      await fetchUsers();
      ElMessage.success('保存成功');
    } catch (e) { ElMessage.error(e.response?.data?.error || e.response?.data?.detail || '保存失败'); }
    finally { saving.value = false; }
  });
}

async function confirmDelete(row) {
  try { await ElMessageBox.confirm(`确定删除用户 ${row.username}？`, '确认', { type: 'warning' }); await api.delete(`/users/${row.id}`); await fetchUsers(); ElMessage.success('已删除'); }
  catch {}
}

async function openPermissions(row) {
  permUserId.value = row.id;
  permUser.value = row;
  const r = await api.get(`/users/${row.id}/permissions`);
  const current = r.data;
  permRows.value = pages.map((p) => {
    const saved = current.find((c) => c.page_key === p.key);
    const defaultVal = row.is_admin === 1;
    let canViewVal = saved !== undefined ? saved.can_view : defaultVal;
    let canEditVal = saved !== undefined ? saved.can_edit : defaultVal;
    if (row.is_admin === 1) {
      canViewVal = true;
      canEditVal = true;
    }
    return { page_key: p.key, label: p.label, can_view: canViewVal, can_edit: canEditVal };
  });
  permVisible.value = true;
}

function onPermChange(row) {
  if (!row.can_view) row.can_edit = false;
}
function isSwitchDisabled(row) {
  return permUser.value?.is_admin === 1;
}

async function savePermissions() {
  permSaving.value = true;
  try {
    await api.put(`/users/${permUserId.value}/permissions`, { permissions: permRows.value.map((r) => ({ page_key: r.page_key, can_view: r.can_view, can_edit: r.can_edit })) });
    permVisible.value = false;
    ElMessage.success('权限已更新');
  } catch (e) { ElMessage.error(e.response?.data?.error || '保存失败'); }
  finally { permSaving.value = false; }
}
</script>
