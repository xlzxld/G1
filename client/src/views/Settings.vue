<template>
  <div>
    <h2 style="margin-bottom:16px">系统设置</h2>
    <el-tabs>
      <el-tab-pane label="基本设置">
        <el-table :data="settings" border stripe><el-table-column prop="key" label="参数" width="200" /><el-table-column prop="value" label="值" /><el-table-column prop="category" label="分类" width="120" /><el-table-column label="操作" width="100"><template #default="{row}"><el-button size="small" @click="editSetting(row)">编辑</el-button></template></el-table-column></el-table>
        <el-button style="margin-top:12px" @click="editSetting(null)">新增参数</el-button>
      </el-tab-pane>

      <el-tab-pane label="修改密码">
        <el-form :model="pwd" label-width="100px" style="max-width:400px;margin-top:16px">
          <el-form-item label="当前密码"><el-input v-model="pwd.current" type="password" show-password /></el-form-item>
          <el-form-item label="新密码"><el-input v-model="pwd.newPwd" type="password" show-password /></el-form-item>
          <el-form-item label="确认密码"><el-input v-model="pwd.confirm" type="password" show-password /></el-form-item>
          <el-form-item><el-button type="primary" @click="changePwd" :loading="pwdLoading">修改密码</el-button></el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="通知规则" v-if="auth.isAdmin">
        <el-table :data="rules" border stripe>
          <el-table-column prop="name" label="规则名称" width="160" />
          <el-table-column prop="event" label="触发事件" width="140" />
          <el-table-column prop="title_template" label="标题模板" />
          <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.is_active?'success':'info'" size="small">{{row.is_active?'启用':'停用'}}</el-tag></template></el-table-column>
          <el-table-column label="操作" width="100"><template #default="{row}"><el-button size="small" @click="toggleRule(row)">{{row.is_active?'停用':'启用'}}</el-button></template></el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="操作日志" v-if="auth.isAdmin">
        <el-table :data="logs" border stripe max-height="500"><el-table-column prop="created_at" label="时间" width="160" /><el-table-column prop="display_name" label="操作人" width="100" /><el-table-column prop="action" label="操作" width="80" /><el-table-column prop="entity_type" label="类型" width="100" /><el-table-column prop="detail" label="详情" /></el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="setVisible" title="编辑参数" width="400px">
      <el-form :model="setForm" label-width="60px">
        <el-form-item label="参数"><el-input v-model="setForm.key" :disabled="!!setForm._id" /></el-form-item>
        <el-form-item label="值"><el-input v-model="setForm.value" /></el-form-item>
        <el-form-item label="分类"><el-input v-model="setForm.category" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="setVisible=false">取消</el-button><el-button type="primary" @click="saveSetting">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { useAuthStore } from '../stores/auth.js';
import api from '../api/index.js';

const auth = useAuthStore();
const settings = ref([]); const rules = ref([]); const logs = ref([]);
const pwd = reactive({ current:'', newPwd:'', confirm:'' }); const pwdLoading = ref(false);
const setVisible = ref(false); const setForm = reactive({ _id:null, key:'', value:'', category:'general' });

onMounted(async () => {
  try { settings.value = (await api.get('/settings')).data; } catch {}
  if (auth.isAdmin) { try { rules.value = (await api.get('/notifications/rules')).data; } catch {} try { logs.value = (await api.get('/settings/audit-logs')).data; } catch {} }
});

async function changePwd() {
  if (pwd.newPwd !== pwd.confirm) return ElMessage.error('两次密码不一致');
  pwdLoading.value = true;
  try { await api.put('/settings/change-password', { current_password: pwd.current, new_password: pwd.newPwd }); Object.assign(pwd, { current:'', newPwd:'', confirm:'' }); ElMessage.success('密码已修改'); }
  catch (e) { ElMessage.error(e.response?.data?.error||'修改失败'); } finally { pwdLoading.value = false; }
}

function editSetting(row) { if (row) { setForm._id = row.id; setForm.key = row.key; setForm.category = row.category; setForm.value = row.value; } else { setForm._id = null; setForm.key = ''; setForm.value = ''; setForm.category = 'general'; } setVisible.value = true; }

async function saveSetting() {
  try { await api.put('/settings', { key: setForm.key, value: setForm.value }); setVisible.value = false; settings.value = (await api.get('/settings')).data; ElMessage.success('已保存'); }
  catch (e) { ElMessage.error(e.response?.data?.error||'保存失败'); }
}

async function toggleRule(row) { try { await api.put(`/notifications/rules/${row.id}`, { is_active: !row.is_active }); rules.value = (await api.get('/notifications/rules')).data; } catch {} }
</script>
