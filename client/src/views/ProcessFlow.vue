<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">工艺模板</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">生产标准工艺流程配置</p>
      </div>
      <el-button v-if="auth.canEdit('process_flow')" type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建模板</el-button>
    </div>

    <!-- 1. 模板列表 -->
    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl overflow-hidden shadow-md p-4">
      <!-- 桌面端表格 -->
      <el-table v-if="!isMobile" :data="flows" border stripe v-loading="loading" @row-click="selectFlow" highlight-current-row class="cursor-pointer" :row-class-name="tableRowClassName">
        <el-table-column prop="name" label="模板名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button v-if="auth.canEdit('process_flow')" size="small" @click.stop="editFlow(row)">编辑</el-button>
            <el-button v-if="auth.canEdit('process_flow')" size="small" type="danger" @click.stop="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 移动端卡片列表 -->
      <div v-else v-loading="loading" class="space-y-3">
        <div
          v-for="row in flows"
          :key="row.id"
          :class="['rounded-xl border p-4 shadow-sm transition-all cursor-pointer', selectedFlow?.id === row.id ? 'border-blue-400 bg-blue-50/30 dark:bg-blue-900/10' : 'border-slate-200 dark:border-industrial-border bg-slate-50 dark:bg-industrial-900/50', row.id == highlightedId ? 'highlight-flash-card-active highlight-target-item' : '']"
          @click="selectFlow(row)"
        >
          <div class="flex justify-between items-start mb-2">
            <h4 class="font-bold text-slate-800 dark:text-slate-100 text-base">{{ row.name }}</h4>
            <span class="text-[10px] text-slate-400 dark:text-slate-500">{{ formatDateTime(row.updated_at) }}</span>
          </div>
          <p v-if="row.description" class="text-xs text-slate-500 dark:text-slate-400 mb-3 line-clamp-2 leading-relaxed">{{ row.description }}</p>
          <div v-if="auth.canEdit('process_flow')" class="flex gap-2 border-t border-slate-200 dark:border-industrial-border pt-3" @click.stop>
            <el-button size="small" @click="editFlow(row)" class="flex-1">编辑</el-button>
            <el-button size="small" type="danger" @click="confirmDelete(row)" class="flex-1">删除</el-button>
          </div>
        </div>
        <div v-if="flows.length === 0" class="py-16 text-center">
          <el-empty description="暂无工艺模板" />
        </div>
      </div>
    </div>

    <!-- 2. 步骤编辑区 -->
    <el-divider v-if="selectedFlow" />
    <div v-if="selectedFlow" class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-base sm:text-lg font-semibold text-slate-800 dark:text-slate-200">步骤编辑 — {{ selectedFlow.name }}</h3>
        <el-button v-if="auth.canEdit('process_flow') && isMobile" size="small" type="primary" @click="addStep"><el-icon><Plus /></el-icon>添加步骤</el-button>
      </div>

      <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-4 shadow-md">
        <!-- 桌面端步骤表格 -->
        <el-table v-if="!isMobile" :data="steps" border stripe row-key="idx">
          <el-table-column label="序号" width="60" align="center">
            <template #default="{ $index }">{{ $index + 1 }}</template>
          </el-table-column>
          <el-table-column prop="name" label="工序名称">
            <template #default="{ row }">
              <el-input v-model="row.name" size="small" placeholder="工序名称" />
            </template>
          </el-table-column>
          <el-table-column label="必做" width="70" align="center">
            <template #default="{ row }"><el-switch v-model="row.required" size="small" /></template>
          </el-table-column>
          <el-table-column label="完成条件" width="130">
            <template #default="{ row }">
              <el-select v-model="row.completion_condition" size="small">
                <el-option label="手动确认" value="manual" />
                <el-option label="上传照片" value="photo" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="负责人" width="160">
            <template #default="{ row }">
              <el-select v-model="row.assignee" size="small" placeholder="选择负责人" clearable filterable>
                <el-option v-for="u in users" :key="u.id" :label="u.display_name || u.username" :value="u.username" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ $index }">
              <el-button v-if="auth.canEdit('process_flow')" size="small" type="danger" @click="steps.splice($index, 1)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 移动端步骤卡片编辑器 -->
        <div v-else class="space-y-4">
          <div
            v-for="(row, $index) in steps"
            :key="$index"
            class="rounded-xl border border-slate-200 dark:border-industrial-border bg-slate-50 dark:bg-industrial-900/50 p-4 shadow-sm relative space-y-3"
          >
            <div class="flex justify-between items-center border-b border-slate-200 dark:border-industrial-border pb-2">
              <span class="font-bold text-sm text-blue-500">步骤 {{ $index + 1 }}</span>
              <el-button
                v-if="auth.canEdit('process_flow')"
                size="small"
                type="danger"
                circle
                plain
                @click="steps.splice($index, 1)"
              >
                ×
              </el-button>
            </div>

            <div class="grid grid-cols-1 gap-3 text-xs">
              <div class="flex items-center gap-2">
                <span class="w-16 text-slate-500 shrink-0">工序名称:</span>
                <el-input v-model="row.name" placeholder="请输入工序名称" class="flex-1" />
              </div>
              
              <div class="flex items-center gap-2">
                <span class="w-16 text-slate-500 shrink-0">是否必做:</span>
                <el-switch v-model="row.required" />
              </div>

              <div class="flex items-center gap-2">
                <span class="w-16 text-slate-500 shrink-0">完成条件:</span>
                <el-select v-model="row.completion_condition" class="flex-1">
                  <el-option label="手动确认" value="manual" />
                  <el-option label="上传照片" value="photo" />
                </el-select>
              </div>

              <div class="flex items-center gap-2">
                <span class="w-16 text-slate-500 shrink-0">负责人:</span>
                <el-select v-model="row.assignee" placeholder="选择负责人" clearable filterable class="flex-1">
                  <el-option v-for="u in users" :key="u.id" :label="u.display_name || u.username" :value="u.username" />
                </el-select>
              </div>
            </div>
          </div>
          <div v-if="steps.length === 0" class="py-8 text-center text-slate-400">
            暂无步骤配置，请点击“添加步骤”
          </div>
        </div>

        <div class="mt-4 flex gap-2" v-if="auth.canEdit('process_flow')">
          <el-button v-if="!isMobile" @click="addStep">添加步骤</el-button>
          <el-button type="primary" @click="saveSteps" :loading="savingSteps" class="flex-1 sm:flex-none">保存全部步骤</el-button>
        </div>
      </div>
    </div>

    <!-- 3. 新增/编辑弹窗 -->
    <el-dialog v-model="formVisible" :title="editing ? '编辑模板' : '新建模板'" :width="isMobile ? '95vw' : '440px'">
      <el-form ref="formRef" :model="form" :rules="rules" :label-position="isMobile ? 'top' : 'right'" label-width="70px">
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" @click="saveFlow" :loading="saving">保存</el-button>
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

defineOptions({ name: 'ProcessFlow' });

const auth = useAuthStore();
const route = useRoute();
const flows = ref([]);
const users = ref([]);
const loading = ref(false);
const selectedFlow = ref(null);
const steps = ref([]);
const formVisible = ref(false);
const editing = ref(null);
const saving = ref(false);
const savingSteps = ref(false);
const formRef = ref(null);
const highlightedId = ref(null);
const form = reactive({ name: '', description: '' });
const rules = { name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }] };

const isMobile = ref(window.innerWidth < 768);
function onResize() { isMobile.value = window.innerWidth < 768; }
onMounted(() => window.addEventListener('resize', onResize));
onUnmounted(() => window.removeEventListener('resize', onResize));

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

    const exists = flows.value.some(o => o.id === targetId);
    if (exists) {
      triggerHighlightScroll();
      fetchFlows(true);
      return;
    }
  } else {
    highlightedId.value = null;
  }
  await fetchFlows(true);
  triggerHighlightScroll();
}, { immediate: true });

onMounted(async () => {
  try {
    const r = await api.get('/users');
    users.value = r.data;
  } catch {}
});

function tableRowClassName({ row }) {
  return row.id == highlightedId.value ? 'highlight-flash-row highlight-target-item' : '';
}

async function fetchFlows(silent = false) { 
  if (!silent || flows.value.length === 0) {
    loading.value = true; 
  }
  try { 
    const r = await api.get('/process-flows'); 
    flows.value = r.data; 
  } 
  catch {} 
  finally { loading.value = false; } 
}

function openCreate() { editing.value = null; Object.assign(form, { name: '', description: '' }); formVisible.value = true; }
function editFlow(row) { editing.value = row; Object.assign(form, { name: row.name, description: row.description }); formVisible.value = true; }

async function saveFlow() {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    saving.value = true;
    try {
      if (editing.value) { await api.put(`/process-flows/${editing.value.id}`, form); }
      else { await api.post('/process-flows', form); }
      formVisible.value = false;
      await fetchFlows();
      ElMessage.success('保存成功');
    } catch (e) { ElMessage.error(e.response?.data?.error || e.response?.data?.detail || '保存失败'); }
    finally { saving.value = false; }
  });
}

async function confirmDelete(row) {
  try { await ElMessageBox.confirm(`确定删除模板 ${row.name}？`, '确认', { type: 'warning' }); await api.delete(`/process-flows/${row.id}`); await fetchFlows(); ElMessage.success('已删除'); }
  catch {}
}

async function selectFlow(row) {
  selectedFlow.value = row;
  const r = await api.get(`/process-flows/${row.id}`);
  steps.value = (r.data.steps || []).map((s, i) => ({
    id: s.id, name: s.name, seq: i, required: !!s.required, can_parallel: !!s.can_parallel,
    completion_condition: s.completion_condition || 'manual', assignee: s.assignee || '',
    depends_on_step_id: s.depends_on_step_id || null, depends_on_idx: null,
  }));
}

function addStep() { steps.value.push({ name: '', seq: steps.value.length, required: true, can_parallel: false, completion_condition: 'manual', assignee: '', depends_on_step_id: null, depends_on_idx: null }); }

async function saveSteps() {
  if (steps.value.some(s => !s.name || !s.name.trim())) {
    return ElMessage.error('存在空缺的工序名称，请填写后再保存');
  }
  if (steps.value.some(s => !s.assignee || !s.assignee.trim())) {
    return ElMessage.error('每道工序都必须指定负责人，请选择后再保存');
  }
  savingSteps.value = true;
  try {
    const payload = steps.value.map((s, i) => ({
      name: s.name, seq: i, required: !!s.required, can_parallel: !!s.can_parallel,
      completion_condition: s.completion_condition || 'manual', assignee: s.assignee || '',
    }));
    await api.put(`/process-flows/${selectedFlow.value.id}/steps`, { steps: payload });
    ElMessage.success('步骤已保存');
  } catch (e) { ElMessage.error(e.response?.data?.error || e.response?.data?.detail || '保存失败'); }
  finally { savingSteps.value = false; }
}
function formatDateTime(val) {
  if (!val) return '—';
  return val.slice(0, 16).replace('T', ' ');
}
</script>
