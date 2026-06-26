<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">系统设置</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">系统参数与全局配置</p>
      </div>
    </div>
    <el-tabs>

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
        <el-table :data="logs" border stripe max-height="500">
          <el-table-column prop="created_at" label="时间" width="160" />
          <el-table-column prop="display_name" label="操作人" width="100" />
          <el-table-column prop="action" label="操作" width="80">
            <template #default="{row}">{{ formatAction(row.action) }}</template>
          </el-table-column>
          <el-table-column prop="entity_type" label="类型" width="100">
            <template #default="{row}">{{ formatEntity(row.entity_type) }}</template>
          </el-table-column>
          <el-table-column prop="detail" label="详情" />
        </el-table>
      </el-tab-pane>
    </el-tabs>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { useAuthStore } from '../stores/auth.js';
import api from '../api/index.js';

const auth = useAuthStore();
const rules = ref([]); const logs = ref([]);
const pwd = reactive({ current:'', newPwd:'', confirm:'' }); const pwdLoading = ref(false);

onMounted(async () => {
  if (auth.isAdmin) { try { rules.value = (await api.get('/notifications/rules')).data; } catch {} try { logs.value = (await api.get('/settings/audit-logs')).data; } catch {} }
});

async function changePwd() {
  if (pwd.newPwd !== pwd.confirm) return ElMessage.error('两次密码不一致');
  pwdLoading.value = true;
  try { await api.put('/settings/change-password', { current_password: pwd.current, new_password: pwd.newPwd }); Object.assign(pwd, { current:'', newPwd:'', confirm:'' }); ElMessage.success('密码已修改'); }
  catch (e) { ElMessage.error(e.response?.data?.error||'修改失败'); } finally { pwdLoading.value = false; }
}

function formatAction(action) {
  const map = { 'create': '新增', 'update': '修改', 'delete': '删除' };
  return map[action] || action;
}

function formatEntity(entity) {
  const map = { 'customers': '客户管理', 'orders': '订单管理', 'inventory': '库存管理', 'process': '工艺流程', 'process-flows': '工艺模板', 'users': '账号管理', 'vendors': '外协管理', 'notifications': '通知中心', 'settings': '系统设置', 'auth': '登录认证' };
  return map[entity] || entity;
}

async function toggleRule(row) { try { await api.put(`/notifications/rules/${row.id}`, { is_active: !row.is_active }); rules.value = (await api.get('/notifications/rules')).data; } catch {} }
</script>
