<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>图纸管理</h2>
      <el-button type="primary" @click="uploadVisible = true"><el-icon><Upload /></el-icon> 上传图纸</el-button>
    </div>

    <div class="search-bar" style="margin-bottom:12px">
      <el-select v-model="filterOrder" placeholder="订单筛选" clearable filterable style="width:220px" @change="fetchDocs">
        <el-option v-for="o in orders" :key="o.id" :label="`${o.order_no} ${o.product_name}`" :value="o.id" />
      </el-select>
      <el-select v-model="filterCat" placeholder="图纸分类" clearable style="width:160px;margin-left:8px" @change="fetchDocs">
        <el-option v-for="c in cats" :key="c" :label="c" :value="c" />
      </el-select>
    </div>

    <el-table :data="docs" border stripe v-loading="loading">
      <el-table-column prop="order_no" label="订单号" width="120" />
      <el-table-column prop="original_name" label="文件名" min-width="180">
        <template #default="{ row }"><a :href="`/api/download/${encodeURIComponent(row.order_no)}/${encodeURIComponent(row.category)}/${encodeURIComponent(row.filename)}`" target="_blank" style="color:#409eff">{{ row.original_name }}</a></template>
      </el-table-column>
      <el-table-column prop="category" label="分类" width="100" />
      <el-table-column label="版本" width="60" align="center">
        <template #default="{ row }">V{{ row.version }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="file_size" label="大小" width="100">
        <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="上传时间" width="120" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="changeStatus(row)">改状态</el-button>
          <el-button size="small" type="danger" @click="confirmDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="uploadVisible" title="上传图纸" width="500px">
      <el-form label-width="80px">
        <el-form-item label="订单">
          <el-select v-model="uploadOrderNo" placeholder="选择订单" filterable style="width:100%">
            <el-option v-for="o in orders" :key="o.order_no" :label="`${o.order_no} ${o.product_name}`" :value="o.order_no" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="uploadCat" placeholder="选择分类" style="width:100%">
            <el-option v-for="c in cats" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="文件"><el-upload :auto-upload="false" :on-change="onFileChange" :limit="1"><el-button>选择文件</el-button></el-upload></el-form-item>
        <p v-if="uploadFile" style="color:#909399">{{ uploadFile.name }} ({{ formatSize(uploadFile.size) }})</p>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" @click="doUpload" :loading="uploading" :disabled="!uploadFile">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api/index.js';

const docs = ref([]);
const orders = ref([]);
const loading = ref(false);
const filterOrder = ref(null);
const filterCat = ref('');
const uploadVisible = ref(false);
const uploadOrderNo = ref('');
const uploadCat = ref('图纸');
const uploadFile = ref(null);
const uploading = ref(false);

const cats = ['分流板图', '零件图', '精雕图', '线切割图', '图纸'];

onMounted(async () => {
  try { orders.value = (await api.get('/orders')).data.data; } catch {}
  fetchDocs();
});

async function fetchDocs() {
  loading.value = true;
  const params = {};
  if (filterOrder.value) params.order_id = filterOrder.value;
  if (filterCat.value) params.category = filterCat.value;
  try { docs.value = (await api.get('/documents', { params })).data; } catch {} finally { loading.value = false; }
}

function onFileChange(f) { uploadFile.value = f.raw; }

async function doUpload() {
  uploading.value = true;
  try {
    const fd = new FormData();
    fd.append('file', uploadFile.value);
    fd.append('category', uploadCat.value);
    await api.post(`/documents/upload/${uploadOrderNo.value}`, fd);
    uploadVisible.value = false; uploadFile.value = null;
    await fetchDocs(); ElMessage.success('上传成功');
  } catch (e) { ElMessage.error(e.response?.data?.error || '上传失败'); }
  finally { uploading.value = false; }
}

async function changeStatus(row) {
  const next = row.status === 'active' ? 'deprecated' : row.status === 'deprecated' ? 'pending' : 'active';
  try { await api.put(`/documents/${row.id}/status`, { status: next }); await fetchDocs(); ElMessage.success(`状态已改为${statusLabel(next)}`); }
  catch (e) { ElMessage.error(e.response?.data?.error || '操作失败'); }
}

async function confirmDelete(row) {
  try { await ElMessageBox.confirm(`确定删除 ${row.original_name}？`, '确认', { type: 'warning' }); await api.delete(`/documents/${row.id}`); await fetchDocs(); ElMessage.success('已删除'); } catch {}
}

function statusType(s) { return s === 'active' ? 'success' : s === 'deprecated' ? 'info' : 'warning'; }
function statusLabel(s) { return s === 'active' ? '使用中' : s === 'deprecated' ? '作废' : '待审核'; }
function formatSize(bytes) { if (!bytes) return '0 B'; const u = ['B','KB','MB','GB']; let i = 0; while (bytes >= 1024 && i < 3) { bytes /= 1024; i++; } return bytes.toFixed(1) + ' ' + u[i]; }
</script>
