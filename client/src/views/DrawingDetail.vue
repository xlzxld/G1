<template>
  <div v-if="doc">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>{{ doc.title || doc.original_name }}</h2>
      <router-link to="/drawings"><el-button>返回列表</el-button></router-link>
    </div>
    <el-row :gutter="16">
      <el-col :span="14">
        <el-image v-if="isImage(doc.mime_type)" :src="`/api/download/${encodeURIComponent(doc.order_no)}/${encodeURIComponent(doc.category)}/${encodeURIComponent(doc.filename)}`" style="width:100%;object-fit:contain;background:#f5f5f5;border-radius:8px" fit="contain" />
        <el-empty v-else description="非图片文件" />
      </el-col>
      <el-col :span="10">
        <el-card header="图纸信息">
          <el-form :model="form" label-width="70px">
            <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
            <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="4" /></el-form-item>
            <el-form-item label="文件名">{{ doc.original_name }}</el-form-item>
            <el-form-item label="订单">
              <router-link :to="`/orders/${doc.order_id}`" style="color:#409eff;text-decoration:none">{{ doc.order_no }}</router-link>
              <span style="margin-left:8px;color:#606266">{{ doc.product_name || '' }}</span>
            </el-form-item>
            <el-form-item label="分类">{{ doc.category }}</el-form-item>
            <el-form-item label="版本">V{{ doc.version }}</el-form-item>
            <el-form-item label="状态"><el-tag :type="doc.status==='active'?'success':doc.status==='deprecated'?'info':'warning'" size="small">{{ statusLabel(doc.status) }}</el-tag></el-form-item>
            <el-form-item label="大小">{{ formatSize(doc.file_size) }}</el-form-item>
            <el-form-item label="上传时间">{{ doc.created_at }}</el-form-item>
            <el-form-item><el-button type="primary" @click="saveData">保存信息</el-button></el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import api from '../api/index.js';

const route = useRoute();
const doc = ref(null);
const form = reactive({ title: '', description: '' });

onMounted(async () => {
  try {
    const r = await api.get('/documents');
    const d = r.data.find(d => d.id === Number(route.params.id));
    if (d) { doc.value = d; form.title = d.title || ''; form.description = d.description || ''; }
  } catch {}
});

function isImage(mime) { return mime?.startsWith('image/'); }
function statusLabel(s) { return s === 'active' ? '使用中' : s === 'deprecated' ? '作废' : '待审核'; }
function formatSize(bytes) { if (!bytes) return '0 B'; const u = ['B','KB','MB','GB']; let i = 0; while (bytes >= 1024 && i < 3) { bytes /= 1024; i++; } return bytes.toFixed(1) + ' ' + u[i]; }

async function saveData() {
  try { await api.put(`/documents/${doc.value.id}`, { title: form.title, description: form.description }); ElMessage.success('已保存'); }
  catch (e) { ElMessage.error('保存失败'); }
}
</script>
