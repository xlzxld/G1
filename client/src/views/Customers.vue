<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">客户管理</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">客户与联系人管理</p>
      </div>
      <el-button v-if="auth.canEdit('customers')" type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建客户</el-button>
    </div>

    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-4 flex flex-wrap gap-3 items-center shadow-md">
      <el-input v-model="keyword" placeholder="搜索名称/联系人/电话/微信/邮箱" clearable class="w-full sm:w-80" @input="debouncedSearch" @keyup.enter="handleSearch" />
      <el-button type="primary" @click="handleSearch" class="w-full sm:w-auto">搜索</el-button>
    </div>
    
    <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl overflow-hidden shadow-md p-4">
      <!-- 桌面端表格 -->
      <el-table v-if="!isMobile" :data="customers" border stripe v-loading="loading" @row-click="row => router.push(`/customers/${row.id}`)" style="cursor:pointer" :row-class-name="tableRowClassName">
        <el-table-column prop="name" label="客户名称" min-width="160" />
        <el-table-column label="联系人列表" min-width="240">
          <template #default="{ row }">
            <div v-if="parseContacts(row.contacts).length">
              <div v-for="(c, i) in parseContacts(row.contacts)" :key="i" class="text-xs py-0.5 border-b border-slate-100 dark:border-industrial-border/60 last:border-b-0 pb-1.5 mb-1.5 last:pb-0 last:mb-0">
                <span class="font-semibold text-slate-700 dark:text-slate-200">{{ c.name }}</span>
                <span v-if="c.role" class="text-slate-400 dark:text-slate-500"> ({{ c.role }})</span>
                <div class="flex flex-wrap gap-1 mt-0.5">
                  <span v-for="(m, idx) in c.contact_methods" :key="idx" class="text-slate-500 dark:text-slate-400 mr-2 flex items-center">
                    <el-tag size="small" type="info" class="scale-90 origin-left mr-0.5">{{ m.type }}</el-tag>
                    <span>{{ m.value }}</span>
                  </span>
                </div>
              </div>
            </div>
            <span v-else v-for="(m, i) in parseMethods(row.contact_methods)" :key="i" style="margin-right:8px;">
              <el-tag size="small" type="info">{{ m.type }}</el-tag> <span class="text-slate-300 ml-1">{{ m.value }}</span>
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="address" label="地址" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button v-if="auth.canEdit('customers')" size="small" @click.stop="openEdit(row)">编辑</el-button>
            <el-button v-if="auth.canEdit('customers')" size="small" type="danger" @click.stop="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 移动端卡片列表 -->
      <div v-else v-loading="loading" class="space-y-3 mt-2">
        <div
          v-for="row in customers"
          :key="row.id"
          :class="['rounded-xl border p-4 shadow-sm active:scale-[0.99] transition-all', row.id == highlightedId ? 'highlight-flash-card-active highlight-target-item' : 'border-slate-200 dark:border-industrial-border bg-slate-50 dark:bg-industrial-900/50']"
          @click="router.push(`/customers/${row.id}`)"
        >
          <div class="flex items-start justify-between mb-2">
            <p class="text-slate-800 dark:text-slate-100 font-semibold text-base">{{ row.name }}</p>
            <el-icon class="text-slate-400 mt-1"><ArrowRight /></el-icon>
          </div>
          <div class="space-y-1.5 mb-2">
            <div v-if="parseContacts(row.contacts).length" v-for="(c, i) in parseContacts(row.contacts)" :key="i" class="text-xs border-b border-slate-200/50 dark:border-industrial-border/30 last:border-b-0 pb-1 last:pb-0">
              <div class="flex items-center gap-1.5">
                <span class="font-semibold text-slate-700 dark:text-slate-200">{{ c.name }}</span>
                <el-tag v-if="c.role" size="small" type="info" class="scale-90 origin-left">{{ c.role }}</el-tag>
              </div>
              <div class="flex flex-wrap gap-1 mt-0.5 text-slate-500 dark:text-slate-400">
                <span v-for="(m, idx) in c.contact_methods" :key="idx" class="mr-2">[{{ m.type }}] {{ m.value }}</span>
              </div>
            </div>
            <div v-else class="flex flex-wrap gap-1.5">
              <span v-for="(m, i) in parseMethods(row.contact_methods)" :key="i" class="flex items-center gap-1">
                <el-tag size="small" type="info">{{ m.type }}</el-tag>
                <span class="text-xs text-slate-500 dark:text-slate-400">{{ m.value }}</span>
              </span>
            </div>
          </div>
          <p v-if="row.address" class="text-xs text-slate-400 dark:text-slate-500 mb-3">地址：{{ row.address }}</p>
          <div v-if="auth.canEdit('customers')" class="flex gap-2 border-t border-slate-200 dark:border-industrial-border pt-3" @click.stop>
            <el-button size="small" @click="openEdit(row)" class="flex-1">编辑</el-button>
            <el-button size="small" type="danger" @click="confirmDelete(row)" class="flex-1">删除</el-button>
          </div>
        </div>
        <div v-if="customers.length === 0" class="py-16 text-center">
          <el-empty description="暂无客户数据" />
        </div>
      </div>
    </div>

    <el-dialog v-model="formVisible" :title="editing ? '编辑客户' : '新建客户'" :width="isMobile ? '95vw' : '500px'">
      <el-form ref="formRef" :model="form" :rules="rules" :label-position="isMobile ? 'top' : 'right'" label-width="70px">
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" /></el-form-item>
        <el-divider content-position="left">联系人列表 <span style="color:#f56c6c">*</span></el-divider>
        <div v-for="(c, i) in form.contacts" :key="i" class="border border-slate-200 dark:border-industrial-border rounded-xl p-4 mb-3 relative bg-slate-50/50 dark:bg-industrial-900/30">
          <div class="grid grid-cols-2 gap-x-3 gap-y-2">
            <el-form-item label="姓名" :prop="'contacts.' + i + '.name'" :rules="{ required: true, message: '姓名必填', trigger: 'blur' }">
              <el-input v-model="c.name" placeholder="联系人姓名" />
            </el-form-item>
            <el-form-item label="职务">
              <el-input v-model="c.role" placeholder="职务/部门" />
            </el-form-item>
            
            <!-- 联系人的联系方式动态列表 -->
            <div class="col-span-2 border-t border-slate-100 dark:border-industrial-border/60 pt-3 mt-1">
              <span class="text-xs font-semibold text-slate-500 dark:text-slate-400">联系方式</span>
              <div v-for="(m, idx) in c.contact_methods" :key="idx" class="flex gap-2 mt-2 items-start">
                <el-form-item :prop="'contacts.' + i + '.contact_methods.' + idx + '.type'" :rules="{ required: true, message: '类型必填', trigger: ['blur', 'change'] }" class="mb-0">
                  <el-select v-model="m.type" style="width:110px" placeholder="类型" allow-create filterable>
                    <el-option v-for="t in contactTypes" :key="t" :value="t" :label="t" />
                  </el-select>
                </el-form-item>
                <el-form-item :prop="'contacts.' + i + '.contact_methods.' + idx + '.value'" :rules="{ required: true, message: '值必填', trigger: 'blur' }" class="mb-0 flex-1">
                  <el-input v-model="m.value" placeholder="联系号码/账号" />
                </el-form-item>
                <el-button :disabled="c.contact_methods.length <= 1" @click="c.contact_methods.splice(idx,1)" type="danger" size="small" plain class="mt-1">删除</el-button>
              </div>
              <el-button size="small" type="primary" link class="mt-2" @click="c.contact_methods.push({type:'电话',value:''})">+ 添加联系方式</el-button>
            </div>
          </div>
          <div class="mt-3 pt-3 border-t border-slate-100 dark:border-industrial-border/40 text-right">
            <el-button :disabled="form.contacts.length <= 1" @click="form.contacts.splice(i,1)" type="danger" size="small" plain>删除该联系人</el-button>
          </div>
        </div>
        <el-button type="dashed" class="w-full mt-1 mb-4" @click="form.contacts.push({name:'',role:'',contact_methods:[{type:'电话',value:''}]})">+ 添加联系人</el-button>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" @click="save" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api/index.js';
import { useAuthStore } from '../stores/auth.js';
import { debounce } from '../utils/debounce.js';

defineOptions({ name: 'Customers' });

const isMobile = ref(window.innerWidth < 768);
function onResize() { isMobile.value = window.innerWidth < 768; }
window.addEventListener('resize', onResize);
onUnmounted(() => window.removeEventListener('resize', onResize));

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const debouncedSearch = debounce(handleSearch, 300);

const customers = ref([]); const loading = ref(false); const keyword = ref('');
const formVisible = ref(false); const editing = ref(null); const saving = ref(false);
const formRef = ref(null);
const highlightedId = ref(null);
const form = reactive({ name: '', address: '', notes: '', contacts: [{name:'',role:'',contact_methods:[{type:'电话',value:''}]}] });
const rules = { name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }] };
const contactTypes = ['电话', '微信', 'QQ', '邮箱', '传真'];

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

    const exists = customers.value.some(o => o.id === targetId);
    if (exists) {
      triggerHighlightScroll();
      fetchData(true);
      return;
    }
  } else {
    highlightedId.value = null;
  }
  await fetchData(true);
  triggerHighlightScroll();
}, { immediate: true });

function tableRowClassName({ row }) {
  return row.id == highlightedId.value ? 'highlight-flash-row highlight-target-item' : '';
}

async function fetchData(silent = false) {
  if (!silent || customers.value.length === 0) {
    loading.value = true;
  }
  try { 
    const r = await api.get('/customers', { params: { keyword: keyword.value } }); 
    customers.value = r.data; 
  } 
  catch {} 
  finally { loading.value = false; } 
}

function handleSearch() {
  highlightedId.value = null;
  fetchData();
}

function parseMethods(raw) { try { return typeof raw === 'string' ? JSON.parse(raw) : (raw || []); } catch { return []; } }
function parseContacts(raw) {
  try {
    const list = typeof raw === 'string' ? JSON.parse(raw) : (raw || []);
    if (!Array.isArray(list)) return [];
    return list.map(c => {
      if (c && typeof c === 'object') {
        if (!c.contact_methods || !Array.isArray(c.contact_methods)) {
          const methods = [];
          if (c.phone) methods.push({ type: '电话', value: c.phone });
          if (c.wechat) methods.push({ type: '微信', value: c.wechat });
          if (c.email) methods.push({ type: '邮箱', value: c.email });
          c.contact_methods = methods;
        }
      } else {
        return { name: String(c), role: '', contact_methods: [] };
      }
      return c;
    });
  } catch {
    return [];
  }
}
function openCreate() { editing.value = null; Object.assign(form, { name: '', address: '', notes: '', contacts: [{name:'',role:'',contact_methods:[{type:'电话',value:''}]}] }); formVisible.value = true; }
function openEdit(row) { editing.value = row; Object.assign(form, { name: row.name, address: row.address, notes: row.notes, contacts: JSON.parse(JSON.stringify(parseContacts(row.contacts))) }); if (form.contacts.length === 0) form.contacts.push({name:'',role:'',contact_methods:[{type:'电话',value:''}]}); else { form.contacts.forEach(c => { if (!c.contact_methods) c.contact_methods = []; if (c.contact_methods.length === 0) c.contact_methods.push({type:'电话',value:''}); }); } formVisible.value = true; }
async function save() {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    saving.value = true;
    try {
      const body = { name: form.name, address: form.address, notes: form.notes, contacts: form.contacts.filter(c => c.name.trim()) };
      if (editing.value) { await api.put(`/customers/${editing.value.id}`, body); } else { await api.post('/customers', body); }
      formVisible.value = false; await fetchData(); ElMessage.success('保存成功');
    } catch (e) { ElMessage.error(e.response?.data?.error || e.response?.data?.detail || '保存失败'); }
    finally { saving.value = false; }
  });
}
async function confirmDelete(row) { try { await ElMessageBox.confirm(`确定删除客户 ${row.name}？`, '确认', { type: 'warning' }); await api.delete(`/customers/${row.id}`); await fetchData(); ElMessage.success('已删除'); } catch {} }
function formatDateTime(val) {
  if (!val) return '—';
  return val.slice(0, 16).replace('T', ' ');
}
</script>
