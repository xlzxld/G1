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
        <div class="flex justify-between items-center mb-4 mt-2">
          <p class="text-xs text-slate-500 dark:text-slate-400">配置并在发生业务事件时自动通过预置规则触发站内信分发通知</p>
          <el-button type="primary" size="small" @click="openCreateRule"><el-icon><Plus /></el-icon>&nbsp;新增通知规则</el-button>
        </div>
        <el-table :data="rules" border stripe style="width: 100%">
          <el-table-column prop="name" label="规则名称" min-width="120" />
          <el-table-column prop="event" label="触发事件" width="120">
            <template #default="{row}">
              <el-tag size="small">{{ formatEvent(row.event) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="触发条件" min-width="180">
            <template #default="{row}">
              <span v-if="row.condition_field">
                当 <b>{{ row.condition_field }}</b> {{ formatOp(row.condition_op) }} <b>{{ row.condition_value }}</b> 时
              </span>
              <span v-else class="text-slate-400">无条件触发</span>
            </template>
          </el-table-column>
          <el-table-column label="接收人" min-width="150" show-overflow-tooltip>
            <template #default="{row}">
              {{ formatNotifyRole(row.notify_role) }}
            </template>
          </el-table-column>
          <el-table-column prop="title_template" label="标题模板" min-width="160" show-overflow-tooltip />
          <el-table-column label="状态" width="80" align="center">
            <template #default="{row}">
              <el-switch
                v-model="row.is_active"
                :active-value="1"
                :inactive-value="0"
                size="small"
                @change="toggleRuleActive(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" align="center">
            <template #default="{row}">
              <el-button size="small" type="primary" plain @click="openEditRule(row)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="confirmDeleteRule(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="操作日志" v-if="auth.isAdmin">
        <el-table :data="logs" border stripe max-height="500" style="width: 100%">
          <el-table-column prop="created_at" label="时间" width="180">
            <template #default="{row}">{{ formatDateTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column prop="display_name" label="操作人" width="100" />
          <el-table-column prop="action" label="操作" width="80">
            <template #default="{row}">{{ formatAction(row.action) }}</template>
          </el-table-column>
          <el-table-column prop="entity_type" label="类型" width="100">
            <template #default="{row}">{{ formatEntity(row.entity_type) }}</template>
          </el-table-column>
          <el-table-column prop="detail" label="详情" min-width="350" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 新增/编辑通知规则对话框 -->
    <el-dialog v-model="ruleDialogVisible" :title="editingRule?'编辑通知规则':'新增通知规则'" width="560px" append-to-body>
      <el-form ref="ruleFormRef" :model="ruleForm" :rules="ruleFormRules" label-width="100px" class="mt-2">
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="ruleForm.name" placeholder="例如：库存不足全局预警" />
        </el-form-item>

        <el-form-item label="触发事件" prop="event">
          <el-select v-model="ruleForm.event" class="w-full" placeholder="选择触发节点">
            <el-option label="新订单创建" value="order_created" />
            <el-option label="订单完工完成" value="order_completed" />
            <el-option label="订单设计完成" value="design_completed" />
            <el-option label="物料/零配件库存不足" value="inventory_alert" />
          </el-select>
        </el-form-item>

        <el-form-item label="触发条件">
          <!-- 订单及设计事件的条件配置 -->
          <div v-if="ruleForm.event === 'order_created' || ruleForm.event === 'order_completed' || ruleForm.event === 'design_completed'" class="flex gap-2 w-full">
            <el-select v-model="ruleForm.condition_field" placeholder="选择过滤条件" style="width: 160px" @change="handleFieldChange">
              <el-option label="无条件发送 (全部)" value="" />
              <el-option label="当订单优先级等于" value="priority" />
              <el-option label="当产品名称包含" value="product_name" />
              <el-option v-if="ruleForm.event === 'design_completed'" label="当图纸标题包含" value="drawing_title" />
            </el-select>
            
            <!-- 优先级的值下拉 -->
            <el-select v-if="ruleForm.condition_field === 'priority'" v-model="ruleForm.condition_value" placeholder="选择优先级" class="flex-1">
              <el-option label="普通" value="0" />
              <el-option label="紧急" value="1" />
              <el-option label="特急" value="2" />
            </el-select>
            <!-- 产品名称的值输入 -->
            <el-input v-else-if="ruleForm.condition_field === 'product_name'" v-model="ruleForm.condition_value" placeholder="如：热咀" class="flex-1" />
            <!-- 图纸标题的值输入 -->
            <el-input v-else-if="ruleForm.condition_field === 'drawing_title'" v-model="ruleForm.condition_value" placeholder="如：总装图" class="flex-1" />
          </div>

          <!-- 库存不足事件 the condition options -->
          <div v-else-if="ruleForm.event === 'inventory_alert'" class="flex gap-2 w-full">
            <el-select v-model="ruleForm.condition_field" placeholder="选择过滤条件" style="width: 160px" @change="handleFieldChange">
              <el-option label="无条件发送 (全部)" value="" />
              <el-option label="当可用库存量小于" value="available" />
              <el-option label="当总库存量小于" value="total" />
            </el-select>
            
            <el-input-number v-if="ruleForm.condition_field" v-model="ruleForm.condition_value" :min="0" class="flex-1" />
          </div>
        </el-form-item>

        <el-form-item label="接收人">
          <el-radio-group v-model="notifyTargetType" @change="handleNotifyTargetTypeChange">
            <el-radio label="all">所有人</el-radio>
            <el-radio label="users">指定用户</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="指定接收人" v-if="notifyTargetType === 'users'" prop="selectedUserIds">
          <el-select
            v-model="ruleForm.selectedUserIds"
            multiple
            filterable
            placeholder="请选择接收通知的具体用户"
            class="w-full"
          >
            <el-option v-for="u in allUsers" :key="u.id" :label="`${u.display_name} (${u.username})`" :value="u.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="标题模板" prop="title_template">
          <el-input v-model="ruleForm.title_template" placeholder="输入通知的标题。支持占位符模板。" />
        </el-form-item>

        <el-form-item label="内容模板">
          <el-input
            v-model="ruleForm.body_template"
            type="textarea"
            :rows="3"
            placeholder="输入通知的正文详情。"
          />
        </el-form-item>

        <div class="ml-[100px] bg-blue-50/50 dark:bg-blue-900/10 border border-blue-200/50 dark:border-blue-900/30 p-3 rounded-lg text-[11px] leading-relaxed text-blue-600 dark:text-blue-400">
          <span class="font-bold">支持的消息模板占位符 (在运行时会自动替换)：</span>
          <ul class="list-disc pl-4 mt-1 space-y-0.5">
            <li><b>订单/设计相关：</b> <code class="bg-blue-100/50 dark:bg-blue-900/40 px-1 rounded">{order_no}</code> 订单号, <code class="bg-blue-100/50 dark:bg-blue-900/40 px-1 rounded">{product_name}</code> 产品名, <code class="bg-blue-100/50 dark:bg-blue-900/40 px-1 rounded">{drawing_title}</code> 图纸名, <code class="bg-blue-100/50 dark:bg-blue-900/40 px-1 rounded">{version}</code> 版本号</li>
            <li><b>库存预警：</b> <code class="bg-blue-100/50 dark:bg-blue-900/40 px-1 rounded">{name}</code> 配件名, <code class="bg-blue-100/50 dark:bg-blue-900/40 px-1 rounded">{available}</code> 当前可用量, <code class="bg-blue-100/50 dark:bg-blue-900/40 px-1 rounded">{alert_threshold}</code> 预警阈值</li>
          </ul>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="ruleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="ruleSaving" @click="saveRule">保存规则</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Search } from '@element-plus/icons-vue';
import { useAuthStore } from '../stores/auth.js';
import api from '../api/index.js';

const auth = useAuthStore();
const rules = ref([]); const logs = ref([]); const allUsers = ref([]);
const pwd = reactive({ current:'', newPwd:'', confirm:'' }); const pwdLoading = ref(false);

const ruleDialogVisible = ref(false);
const editingRule = ref(null);
const ruleSaving = ref(false);
const ruleFormRef = ref(null);
const notifyTargetType = ref('all');

const ruleForm = ref({
  name: '',
  event: 'order_created',
  condition_field: '',
  condition_op: 'lt',
  condition_value: '',
  notify_role: 'all',
  title_template: '',
  body_template: '',
  is_active: 1,
  selectedUserIds: []
});

const ruleFormRules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  event: [{ required: true, message: '请选择触发事件', trigger: 'change' }],
  title_template: [{ required: true, message: '请输入标题模板', trigger: 'blur' }]
};

onMounted(async () => {
  if (auth.isAdmin) {
    fetchRules();
    fetchLogs();
    fetchUsers();
  }
});

async function fetchRules() {
  try { rules.value = (await api.get('/notifications/rules')).data; } catch {}
}
async function fetchLogs() {
  try { logs.value = (await api.get('/settings/audit-logs')).data; } catch {}
}
async function fetchUsers() {
  try { allUsers.value = (await api.get('/users')).data; } catch {}
}

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
  const map = { 
    'customers': '客户管理', 
    'orders': '订单管理', 
    'inventory': '库存管理', 
    'process': '工艺流程', 
    'process-flows': '工艺模板', 
    'users': '账号管理', 
    'vendors': '外协管理', 
    'notifications': '通知中心', 
    'settings': '系统设置', 
    'auth': '登录认证',
    'documents': '图纸管理'
  };
  return map[entity] || entity;
}

function formatDateTime(val) {
  if (!val) return '—';
  return val.slice(0, 19).replace('T', ' ');
}

// ────────────────────────── 通知规则联动逻辑 ──────────────────────────

function formatEvent(event) {
  const map = {
    'order_created': '订单创建',
    'order_completed': '订单完成',
    'design_completed': '订单设计完成',
    'inventory_alert': '库存不足报警'
  };
  return map[event] || event;
}

function formatOp(op) {
  const map = {
    'lt': '小于 (<)',
    'gt': '大于 (>)',
    'eq': '等于 (=)',
    'contains': '包含'
  };
  return map[op] || op;
}

function formatNotifyRole(role) {
  if (!role || role === 'all') return '所有人';
  if (role.startsWith && role.startsWith('user_ids:')) {
    try {
      const ids = role.split('user_ids:')[1].split(',').map(x => parseInt(x.trim()));
      const names = ids.map(id => {
        const u = allUsers.value.find(user => user.id === id);
        return u ? u.display_name : `ID:${id}`;
      });
      return `指定用户：${names.join(', ')}`;
    } catch {
      return '指定用户';
    }
  }
  // 兼容可能遗留的角色通知显示
  if (role === 'role:admin') return '所有人 (包含管理员)';
  if (role === 'role:operator') return '所有人 (包含普通员工)';
  return role;
}

function openCreateRule() {
  editingRule.value = null;
  notifyTargetType.value = 'all';
  ruleForm.value = {
    name: '',
    event: 'order_created',
    condition_field: '',
    condition_op: 'eq',
    condition_value: '',
    notify_role: 'all',
    title_template: '',
    body_template: '',
    is_active: 1,
    selectedUserIds: []
  };
  ruleDialogVisible.value = true;
}

function openEditRule(row) {
  editingRule.value = row;
  
  const role = row.notify_role || 'all';
  let selected = [];
  let type = 'all';
  
  if (role === 'all' || role === 'role:admin' || role === 'role:operator') {
    type = 'all';
  } else if (role.startsWith('user_ids:')) {
    type = 'users';
    try {
      selected = role.split('user_ids:')[1].split(',').map(x => parseInt(x.trim())).filter(x => !isNaN(x));
    } catch {}
  } else {
    type = 'users';
    selected = role.split(',').map(x => parseInt(x.trim())).filter(x => !isNaN(x));
  }
  
  notifyTargetType.value = type;
  ruleForm.value = {
    name: row.name,
    event: row.event,
    condition_field: row.condition_field || '',
    condition_op: row.condition_op || 'eq',
    condition_value: row.condition_value || '',
    notify_role: role,
    title_template: row.title_template,
    body_template: row.body_template || '',
    is_active: row.is_active,
    selectedUserIds: selected
  };
  ruleDialogVisible.value = true;
}

function handleNotifyTargetTypeChange(val) {
  if (val === 'all') {
    ruleForm.value.notify_role = 'all';
  } else {
    ruleForm.value.notify_role = '';
  }
}

// 联动重置：切换条件字段时，清空条件值
function handleFieldChange() {
  ruleForm.value.condition_value = '';
}

// 联动重置：切换触发事件时，清空全部条件信息
watch(() => ruleForm.value.event, () => {
  ruleForm.value.condition_field = '';
  ruleForm.value.condition_op = 'eq';
  ruleForm.value.condition_value = '';
});

async function saveRule() {
  if (!ruleFormRef.value) return;
  await ruleFormRef.value.validate(async (valid) => {
    if (!valid) return;
    
    // 根据 condition_field 自动设定数据库操作符
    const field = ruleForm.value.condition_field;
    if (field === 'priority') {
      ruleForm.value.condition_op = 'eq';
    } else if (field === 'product_name' || field === 'drawing_title') {
      ruleForm.value.condition_op = 'contains';
    } else if (field === 'available' || field === 'total') {
      ruleForm.value.condition_op = 'lt';
    } else {
      ruleForm.value.condition_op = 'eq';
      ruleForm.value.condition_value = ''; // 无条件时清空值
    }

    if (notifyTargetType.value === 'users') {
      if (!ruleForm.value.selectedUserIds || !ruleForm.value.selectedUserIds.length) {
        return ElMessage.warning("请选择至少一个指定的接收人");
      }
      ruleForm.value.notify_role = `user_ids:${ruleForm.value.selectedUserIds.join(',')}`;
    } else {
      ruleForm.value.notify_role = 'all';
    }
    
    ruleSaving.value = true;
    try {
      const payload = {
        name: ruleForm.value.name,
        event: ruleForm.value.event,
        condition_field: ruleForm.value.condition_field,
        condition_op: ruleForm.value.condition_op,
        condition_value: String(ruleForm.value.condition_value),
        notify_role: ruleForm.value.notify_role,
        title_template: ruleForm.value.title_template,
        body_template: ruleForm.value.body_template,
        is_active: ruleForm.value.is_active
      };
      
      if (editingRule.value) {
        await api.put(`/notifications/rules/${editingRule.value.id}`, payload);
        ElMessage.success("修改通知规则成功");
      } else {
        await api.post('/notifications/rules', payload);
        ElMessage.success("新增通知规则成功");
      }
      
      ruleDialogVisible.value = false;
      await fetchRules();
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || "保存失败");
    } finally {
      ruleSaving.value = false;
    }
  });
}

async function confirmDeleteRule(row) {
  try {
    await ElMessageBox.confirm(`确定删除通知规则「${row.name}」？此操作不可撤销。`, "确认删除", {
      type: "warning",
      confirmButtonClass: 'el-button--danger'
    });
    await api.delete(`/notifications/rules/${row.id}`);
    ElMessage.success("已删除规则");
    await fetchRules();
  } catch (e) {
    if (e === 'cancel' || e === 'close') return;
    ElMessage.error("删除失败");
  }
}

async function toggleRuleActive(row) {
  try {
    await api.put(`/notifications/rules/${row.id}`, {
      name: row.name,
      event: row.event,
      condition_field: row.condition_field,
      condition_op: row.condition_op,
      condition_value: row.condition_value,
      notify_role: row.notify_role,
      title_template: row.title_template,
      body_template: row.body_template,
      is_active: row.is_active
    });
    ElMessage.success(`${row.is_active ? '启用' : '停用'}规则成功`);
  } catch (e) {
    row.is_active = row.is_active === 1 ? 0 : 1;
    ElMessage.error("修改状态失败");
  }
}
</script>
