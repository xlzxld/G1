<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>工艺模板</h2>
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建模板</el-button>
    </div>
    <el-table :data="flows" border stripe v-loading="loading" @row-click="selectFlow" highlight-current-row>
      <el-table-column prop="name" label="模板名称" />
      <el-table-column prop="description" label="描述" />
      <el-table-column prop="updated_at" label="更新时间" width="180" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click.stop="editFlow(row)">编辑</el-button>
          <el-button size="small" type="danger" @click.stop="confirmDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-divider v-if="selectedFlow" />
    <div v-if="selectedFlow" style="margin-top:16px">
      <h3 style="margin-bottom:12px">步骤编辑 — {{ selectedFlow.name }}</h3>
      <el-table :data="steps" border stripe row-key="idx">
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
        <el-table-column label="可并行" width="80" align="center">
          <template #default="{ row }"><el-switch v-model="row.can_parallel" size="small" /></template>
        </el-table-column>
        <el-table-column label="完成条件" width="130">
          <template #default="{ row }">
            <el-select v-model="row.completion_condition" size="small">
              <el-option label="手动确认" value="manual" />
              <el-option label="上传照片" value="photo" />
              <el-option label="勾选清单" value="checklist" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="负责人" width="120">
          <template #default="{ row }"><el-input v-model="row.assignee" size="small" placeholder="用户名" /></template>
        </el-table-column>
        <el-table-column label="依赖" width="130">
          <template #default="{ row, $index }">
            <el-select v-model="row.depends_on_idx" size="small" clearable placeholder="无依赖" @change="v => updateDep(row, v)">
              <el-option v-for="(s, i) in steps" v-if="i !== $index" :key="i" :label="(i+1) + '. ' + s.name" :value="i" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ $index }">
            <el-button size="small" type="danger" @click="steps.splice($index, 1)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top:12px">
        <el-button @click="addStep">添加步骤</el-button>
        <el-button type="primary" @click="saveSteps" :loading="savingSteps">保存步骤</el-button>
      </div>
    </div>

    <el-dialog v-model="formVisible" :title="editing ? '编辑模板' : '新建模板'" width="440px">
      <el-form :model="form" label-width="70px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
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
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api/index.js';

const flows = ref([]);
const loading = ref(false);
const selectedFlow = ref(null);
const steps = ref([]);
const formVisible = ref(false);
const editing = ref(null);
const saving = ref(false);
const savingSteps = ref(false);
const form = reactive({ name: '', description: '' });

onMounted(fetchFlows);
async function fetchFlows() { loading.value = true; try { const r = await api.get('/process-flows'); flows.value = r.data; } catch {} finally { loading.value = false; } }

function openCreate() { editing.value = null; Object.assign(form, { name: '', description: '' }); formVisible.value = true; }
function editFlow(row) { editing.value = row; Object.assign(form, { name: row.name, description: row.description }); formVisible.value = true; }

async function saveFlow() {
  saving.value = true;
  try {
    if (editing.value) { await api.put(`/process-flows/${editing.value.id}`, form); }
    else { await api.post('/process-flows', form); }
    formVisible.value = false;
    await fetchFlows();
    ElMessage.success('保存成功');
  } catch (e) { ElMessage.error(e.response?.data?.error || '保存失败'); }
  finally { saving.value = false; }
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

function updateDep(row, targetIdx) {
  if (targetIdx === null || targetIdx === undefined) { row.depends_on_step_id = null; return; }
}

async function saveSteps() {
  savingSteps.value = true;
  try {
    const payload = steps.value.map((s, i) => ({
      name: s.name, seq: i, required: !!s.required, can_parallel: !!s.can_parallel,
      completion_condition: s.completion_condition || 'manual', assignee: s.assignee || '',
    }));
    await api.put(`/process-flows/${selectedFlow.value.id}/steps`, { steps: payload });
    ElMessage.success('步骤已保存');
  } catch (e) { ElMessage.error(e.response?.data?.error || '保存失败'); }
  finally { savingSteps.value = false; }
}
</script>
