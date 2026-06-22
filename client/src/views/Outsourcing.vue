<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>外协管理</h2>
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新增厂商</el-button>
    </div>
    <el-table :data="vendors" border stripe v-loading="loading">
      <el-table-column prop="name" label="厂商名称" min-width="160" />
      <el-table-column prop="contact" label="联系人" width="100" />
      <el-table-column prop="phone" label="电话" width="130" />
      <el-table-column prop="address" label="地址" width="140" />
      <el-table-column prop="notes" label="备注" />
      <el-table-column label="操作" width="150">
        <template #default="{row}"><el-button size="small" @click="openEdit(row)">编辑</el-button><el-button size="small" type="danger" @click="confirmDelete(row)">删除</el-button></template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="formVisible" :title="editing?'编辑厂商':'新增厂商'" width="440px">
      <el-form :model="form" label-width="70px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="联系人"><el-input v-model="form.contact" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="formVisible=false">取消</el-button><el-button type="primary" @click="save" :loading="saving">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api/index.js';

const vendors = ref([]); const loading = ref(false); const formVisible = ref(false); const editing = ref(null); const saving = ref(false);
const form = reactive({ name:'', contact:'', phone:'', address:'', notes:'' });

onMounted(fetchData);
async function fetchData() { loading.value = true; try { vendors.value = (await api.get('/vendors')).data; } catch {} finally { loading.value = false; } }
function openCreate() { editing.value = null; Object.assign(form, { name:'', contact:'', phone:'', address:'', notes:'' }); formVisible.value = true; }
function openEdit(row) { editing.value = row; Object.assign(form, { name:row.name, contact:row.contact, phone:row.phone, address:row.address, notes:row.notes }); formVisible.value = true; }
async function save() {
  saving.value = true;
  try { if (editing.value) await api.put(`/vendors/${editing.value.id}`, form); else await api.post('/vendors', form); formVisible.value = false; await fetchData(); ElMessage.success('保存成功'); }
  catch (e) { ElMessage.error(e.response?.data?.error||'保存失败'); } finally { saving.value = false; }
}
async function confirmDelete(row) { try { await ElMessageBox.confirm(`确定删除 ${row.name}？`,'确认',{type:'warning'}); await api.delete(`/vendors/${row.id}`); await fetchData(); ElMessage.success('已删除'); } catch {} }
</script>
