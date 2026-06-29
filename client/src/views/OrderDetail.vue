<template>
  <div class="min-h-screen bg-slate-100 dark:bg-industrial-900 text-slate-800 dark:text-slate-200 p-3 sm:p-6 font-sans">
    <div v-if="order" class="max-w-7xl mx-auto space-y-6">
      
      <!-- Top Header Area -->
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4 border-b border-slate-200 dark:border-industrial-border pb-4">
        <div>
          <h1 class="text-3xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">订单详情 <span class="text-blue-600 dark:text-industrial-accent">#{{ order.order_no }}</span></h1>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">实时生产进度与工程图纸管理</p>
        </div>
        <div class="flex flex-wrap gap-3 w-full sm:w-auto">
          <button v-if="(isAdmin || auth.canEdit('orders')) && order.status === 'in_progress'" @click="setOrderStatus('paused')" class="px-4 py-2 bg-yellow-600/20 text-yellow-500 border border-yellow-600/50 rounded hover:bg-yellow-600/30 transition shadow-sm">暂停生产</button>
          <button v-if="(isAdmin || auth.canEdit('orders')) && order.status === 'paused'" @click="setOrderStatus('in_progress')" class="px-4 py-2 bg-green-600/20 text-green-500 border border-green-600/50 rounded hover:bg-green-600/30 transition shadow-sm">恢复生产</button>
          <router-link v-if="route.query.from_customer" :to="`/customers/${route.query.from_customer}`" class="px-4 py-2 bg-blue-50 dark:bg-industrial-800 text-blue-600 dark:text-blue-300 border border-blue-200 dark:border-industrial-border rounded hover:bg-blue-100 dark:hover:bg-industrial-700 transition shadow-sm">返回客户详情</router-link>
          <router-link to="/orders" class="px-4 py-2 bg-slate-100 dark:bg-industrial-800 text-slate-800 dark:text-slate-300 border border-slate-300 dark:border-industrial-border rounded hover:bg-slate-200 dark:hover:bg-industrial-700 transition shadow-sm">返回订单列表</router-link>
        </div>
      </div>

      <!-- Bento Grid System -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
        
        <!-- Left Column: Order Meta & Status (Span 1) -->
        <div class="lg:col-span-1 flex flex-col space-y-6">
          <!-- Meta Info Card -->
          <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-5 shadow-lg backdrop-blur-sm relative overflow-hidden">
            <div class="absolute top-0 left-0 w-1 h-full bg-industrial-accent"></div>
            <h2 class="text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 mb-4 font-semibold">基本信息</h2>
            <div class="space-y-4 text-sm">
              <div class="flex justify-between items-center border-b border-slate-200 dark:border-industrial-700 pb-2">
                <span class="text-slate-500 dark:text-slate-400">产品名称</span>
                <span class="font-medium text-slate-800 dark:text-slate-200">{{ order.product_name }}</span>
              </div>
              <div class="border-b border-slate-200 dark:border-industrial-700 pb-2">
                <div class="flex justify-between items-center mb-1">
                  <span class="text-slate-500 dark:text-slate-400">客户</span>
                  <span class="font-medium text-slate-800 dark:text-slate-200">{{ order.customer_name || '—' }}</span>
                </div>
                <div v-if="order.customer && (order.customer.contact || order.customer.phone || order.customer.wechat || order.customer.address)" class="text-xs text-slate-500 mt-2 bg-slate-50 dark:bg-industrial-900/50 p-2 rounded">
                  <div v-if="order.customer.contact" class="flex justify-between mb-1"><span class="text-slate-400">联系人：</span><span class="text-right">{{ order.customer.contact }}</span></div>
                  <div v-if="order.customer.phone" class="flex justify-between mb-1"><span class="text-slate-400">电话：</span><span class="text-right">{{ order.customer.phone }}</span></div>
                  <div v-if="order.customer.wechat" class="flex justify-between mb-1"><span class="text-slate-400">微信：</span><span class="text-right">{{ order.customer.wechat }}</span></div>
                  <div v-if="order.customer.address" class="flex justify-between"><span class="text-slate-400">地址：</span><span class="text-right break-words max-w-[150px]">{{ order.customer.address }}</span></div>
                </div>
              </div>
              <div class="flex justify-between items-center border-b border-slate-200 dark:border-industrial-700 pb-2">
                <span class="text-slate-500 dark:text-slate-400">优先级</span>
                <span :class="prioClass(order.priority)" class="px-2 py-0.5 rounded text-xs font-bold">{{ ['普通','紧急','特急'][order.priority] || '普通' }}</span>
              </div>
              <div class="flex justify-between items-center border-b border-slate-200 dark:border-industrial-700 pb-2">
                <span class="text-slate-500 dark:text-slate-400">交付日期</span>
                <span class="font-medium text-slate-800 dark:text-slate-200">{{ order.shipment_date?.slice(0, 10) || '待定' }}</span>
              </div>
              <div>
                <span class="text-slate-500 dark:text-slate-400 block mb-1">工程备注</span>
                <p class="text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-industrial-900/50 p-2 rounded border border-slate-200 dark:border-industrial-700 text-xs leading-relaxed">{{ order.notes || '暂无备注信息。' }}</p>
              </div>
            </div>
          </div>

          <!-- Materials Info Card (Left Bottom) -->
          <OrderMaterials
            v-if="order"
            :order-id="order.id"
            :order-status="order.status"
            class="flex-1"
          />
        </div>

        <!-- Middle & Right Column: Process Engine (Span 2) -->
        <div class="lg:col-span-2">
          <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-5 shadow-lg h-full flex flex-col">
            <div class="flex justify-between items-center mb-6">
              <h2 class="text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 font-semibold flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                生产流转时间线
              </h2>
              <span :class="statusBadge(order.status)" class="px-3 py-1 rounded-full text-xs font-bold border">{{ statusLabel(order.status) }}</span>
            </div>
            
            <div class="flex-1 overflow-auto pr-2">
              <div v-if="order.steps?.length" class="relative border-l-2 border-slate-200 dark:border-industrial-700 ml-4 space-y-4 pb-4">
                <div v-for="(step, idx) in order.steps" :key="step.id" class="relative pl-8">
                  <!-- Timeline Node (微调 top 位置，使之在卡片收缩后完美对齐第一行文本) -->
                  <div :class="nodeColor(step)" class="absolute -left-[9px] w-4 h-4 rounded-full border-2 border-industrial-800 z-10 transition-colors" style="top: 18px;"></div>
                  
                  <div class="bg-slate-50 dark:bg-industrial-900/50 border border-slate-200 dark:border-industrial-700 rounded-xl p-3 sm:p-5 hover:border-blue-400 dark:hover:border-industrial-accent transition-colors group shadow-sm">
                    <div class="flex flex-col sm:flex-row justify-between items-start gap-3 sm:items-center">
                      <div class="w-full sm:w-auto">
                        <div class="flex flex-wrap items-center gap-2 mb-1">
                          <span class="text-sm sm:text-base font-bold text-slate-800 dark:text-slate-200 group-hover:text-blue-500 dark:group-hover:text-industrial-accent transition-colors">{{ idx + 1 }}. {{ step.name }}</span>
                          <div class="flex flex-wrap gap-1">
                            <span v-if="step.required" class="px-1.5 py-0.5 rounded text-[8px] sm:text-[10px] font-bold bg-red-900/40 text-red-400 border border-red-800 shrink-0">必做</span>
                            <span v-if="step.outsourced" class="px-1.5 py-0.5 rounded text-[8px] sm:text-[10px] font-bold bg-indigo-900/40 text-indigo-400 border border-indigo-800 shrink-0">外协</span>
                            <span v-if="step.completion_condition === 'photo'" class="px-1.5 py-0.5 rounded text-[8px] sm:text-[10px] font-bold bg-blue-900/40 text-blue-400 border border-blue-800 flex items-center gap-0.5 shrink-0"><el-icon><Picture /></el-icon>需传照</span>
                          </div>
                        </div>
                        <div class="text-[11px] sm:text-xs text-slate-500 dark:text-slate-400 flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2 font-medium">
                          <span>负责人: {{ step.assignee || '未分配' }}</span>
                          <span v-if="completionInfo(step)" class="hidden sm:inline">•</span>
                          <span v-if="completionInfo(step)" class="text-slate-400 dark:text-slate-500">{{ completionInfo(step) }}</span>
                        </div>

                        <!-- 工序照片展示 -->
                        <div v-if="getStepPhotos(step.id).length" class="mt-2.5 flex flex-wrap gap-2">
                          <div
                            v-for="photo in getStepPhotos(step.id)"
                            :key="photo.id"
                            class="relative w-12 h-12 sm:w-16 sm:h-16 rounded-lg overflow-hidden border border-slate-200 dark:border-industrial-700 bg-slate-100 dark:bg-industrial-900 cursor-pointer group/img"
                            @click="viewPhoto(photo)"
                          >
                            <img :src="getDocUrl(photo)" class="w-full h-full object-cover" />
                            <div class="absolute inset-0 bg-black/40 opacity-0 group-hover/img:opacity-100 transition-opacity flex items-center justify-center text-white">
                              <el-icon><ZoomIn /></el-icon>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <!-- Action Panel for Active Step -->
                      <div v-if="canAct(step) && auth.canEdit('orders')" class="flex gap-2 w-full sm:w-auto mt-1 sm:mt-0 justify-end">
                        <button v-if="step.status !== 'completed' && step.completion_condition !== 'photo'" @click="doAdvance(step)" class="px-3 py-1.5 sm:px-4 sm:py-2 bg-blue-50 dark:bg-industrial-accent/20 text-blue-600 dark:text-industrial-accent border border-blue-200 dark:border-industrial-accent/50 rounded-lg hover:bg-blue-600 hover:text-white dark:hover:bg-industrial-accent dark:hover:text-industrial-900 transition text-xs font-bold shadow-sm flex-1 sm:flex-none">完成工序</button>
                        <button v-if="step.status !== 'completed' && step.completion_condition === 'photo'" @click="openPhotoUpload(step)" class="px-3 py-1.5 sm:px-4 sm:py-2 bg-blue-50 dark:bg-industrial-accent/20 text-blue-600 dark:text-industrial-accent border border-blue-200 dark:border-industrial-accent/50 rounded-lg hover:bg-blue-600 hover:text-white dark:hover:bg-industrial-accent dark:hover:text-industrial-900 transition text-xs font-bold shadow-sm flex items-center justify-center gap-1 flex-1 sm:flex-none">
                          <el-icon><Picture /></el-icon>上传照片完成
                        </button>
                        <button v-if="step.status === 'completed'" @click="doRollback(step)" class="px-3 py-1.5 sm:px-4 sm:py-2 bg-red-500/10 text-red-500 border border-red-500/30 rounded-lg hover:bg-red-500/20 transition text-xs font-medium shadow-sm flex-1 sm:flex-none">撤回</button>
                        <button v-if="!step.required && step.status === 'pending'" @click="doSkip(step)" class="px-3 py-1.5 sm:px-4 sm:py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition text-xs font-medium shadow-sm flex-1 sm:flex-none">跳过</button>
                      </div>
                      <div v-else class="text-right w-full sm:w-auto mt-1 sm:mt-0">
                        <span :class="stepBadgeClass(step)" class="px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg text-xs font-bold uppercase tracking-wider inline-block shadow-sm">{{ stepStatusLabel(step.status) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="text-center text-slate-500 py-10">此订单暂无工艺流程。</div>
            </div>
          </div>
        </div>

      </div>

      <!-- Bottom Full Width: Drawing Panel Component (Moved outside of the grid to prevent layout overlapping) -->
      <div class="mt-6">
        <DrawingPanel
          v-if="order"
          :order-id="order.id"
          :order-no="order.order_no"
          :documents="order.documents || []"
          @refresh="fetchOrder"
        />
      </div>
    </div>

    <!-- 工序照片上传对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="工序完成确认 — 上传照片" width="460px" @close="resetUpload">
      <div class="space-y-4">
        <p class="text-sm text-slate-600 dark:text-slate-400">
          工序：<strong class="text-slate-800 dark:text-slate-200">{{ activeUploadStep?.name }}</strong>
        </p>
        <el-upload
          ref="uploadRef"
          action=""
          :http-request="doUpload"
          accept="image/*"
          :show-file-list="true"
          :limit="1"
          :auto-upload="false"
          drag
          class="w-full"
          @change="onFileChange"
          @remove="selectedFile = null"
        >
          <el-icon class="text-3xl text-slate-400 mb-2"><UploadFilled /></el-icon>
          <div class="text-sm text-slate-500">
            拖拽文件到此处，或<em class="text-blue-500 not-italic">点击上传</em>
          </div>
          <div class="text-xs text-slate-400 mt-1">
            仅支持上传图片格式作为工序完工凭证，最大 50MB
          </div>
        </el-upload>
      </div>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" :disabled="!selectedFile" @click="submitUpload">
          确认并完成工序
        </el-button>
      </template>
    </el-dialog>

    <!-- 照片大图预览全屏 Teleport -->
    <teleport to="body">
      <div
        v-if="fullscreenPhotoUrl"
        class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/95 p-4"
        @click="fullscreenPhotoUrl = null"
      >
        <img
          :src="fullscreenPhotoUrl"
          class="max-w-full max-h-full object-contain rounded shadow-2xl"
          @click.stop
        />
        <div class="absolute top-4 right-4 flex gap-2">
          <button
            @click="fullscreenPhotoUrl = null"
            class="p-4 sm:p-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition backdrop-blur-sm text-xl sm:text-base"
          >
            <el-icon><Close /></el-icon>
          </button>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useAuthStore } from '../stores/auth.js';
import api from '../api/index.js';
import DrawingPanel from '../components/DrawingPanel.vue';
import OrderMaterials from '../components/OrderMaterials.vue';
import { UploadFilled, Picture, ZoomIn, Close } from '@element-plus/icons-vue';

// 工序传照确认相关状态
const uploadDialogVisible = ref(false);
const activeUploadStep = ref(null);
const uploading = ref(false);
const selectedFile = ref(null);
const uploadRef = ref(null);
const fullscreenPhotoUrl = ref(null);

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const order = ref(null);
const isAdmin = auth.isAdmin;
const isMobile = ref(false);

const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768;
};

onMounted(() => {
  checkMobile();
  window.addEventListener('resize', checkMobile);
  fetchOrder();
});

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile);
});

async function fetchOrder() { 
  try { 
    const r = await api.get(`/orders/${route.params.id}`); 
    order.value = r.data; 
    // Fallback if API doesn't return documents array yet
    if (!order.value.documents) order.value.documents = [];
  } catch (e) {
    console.error("Fetch failed", e);
    ElMessage.error("该订单已不存在或已被删除！");
    router.push('/orders');
  } 
}

// Visual Helpers
function nodeColor(s) { 
  if (s.status === 'completed') return 'bg-green-500 border-white dark:border-industrial-900 shadow-md dark:shadow-[0_0_12px_rgba(34,197,94,0.9)]'; 
  if (s.status === 'in_progress') return 'bg-red-500 border-white dark:border-industrial-900 shadow-lg dark:shadow-[0_0_18px_rgba(244,63,94,0.95)] animate-pulse ring-2 ring-red-500/20'; 
  if (s.status === 'skipped') return 'bg-green-300 dark:bg-green-800/80 border-white dark:border-slate-800'; 
  // 未完成/未开始的工序：亮起鲜艳的红色灯，并在暗黑模式下呈现明显的光晕
  return 'bg-red-600 dark:bg-red-500 border-white dark:border-industrial-900 shadow-md dark:shadow-[0_0_10px_rgba(239,68,68,0.85)]'; 
}

function stepBadgeClass(s) {
  if (s.status === 'completed') return 'bg-blue-50 text-blue-600 border border-blue-200 dark:bg-industrial-accent/10 dark:text-industrial-accent dark:border-industrial-accent/50';
  if (s.status === 'skipped') return 'bg-slate-50 text-slate-500 border border-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700';
  if (s.status === 'in_progress') return 'bg-orange-50 text-orange-600 border border-orange-200 dark:bg-orange-500/10 dark:text-orange-400 dark:border-orange-500/50';
  return 'bg-slate-100 text-slate-500 border border-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:border-slate-600';
}

function statusBadge(s) {
  if (s === 'completed') return 'bg-blue-50 text-blue-600 border-blue-200 dark:bg-industrial-accent/10 dark:text-industrial-accent dark:border-industrial-accent/50 dark:shadow-[0_0_8px_rgba(56,189,248,0.3)]';
  if (s === 'paused') return 'bg-red-50 text-red-600 border-red-200 dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/50';
  if (s === 'in_progress') return 'bg-orange-50 text-orange-600 border-orange-200 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/50';
  return 'bg-slate-100 text-slate-500 border-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:border-slate-600';
}

function prioClass(p) { 
  return p === 2 ? 'bg-red-900/40 text-red-400 border border-red-800' : 
         p === 1 ? 'bg-orange-900/40 text-orange-400 border border-orange-800' : 
         'bg-slate-800 text-slate-400 border border-slate-700'; 
}

function statusLabel(s) {
  const m = { in_progress: '进行中', completed: '已完成', paused: '暂停' };
  return m[s] || (s ? s.toUpperCase() : '');
}

function completionInfo(s) { 
  if (s.completed_at) return `完成于：${formatDateTime(s.completed_at)}`; 
  if (s.started_at) return `开始于：${formatDateTime(s.started_at)}`; 
  return ''; 
}

function canAct(s) { return s.status === 'pending' || s.status === 'in_progress' || s.status === 'completed'; }

// Actions
async function doAdvance(step) {
  try { await api.post(`/orders/${order.value.id}/steps/${step.id}/advance`); await fetchOrder(); ElMessage.success('工序已完成'); }
  catch (e) { ElMessage.error(e.response?.data?.error || '操作失败'); }
}
async function doRollback(step) {
  try { await api.post(`/orders/${order.value.id}/steps/${step.id}/rollback`); await fetchOrder(); ElMessage.success('已撤回'); }
  catch (e) { ElMessage.error(e.response?.data?.error || '操作失败'); }
}
async function doSkip(step) {
  try { await api.post(`/orders/${order.value.id}/steps/${step.id}/skip`); await fetchOrder(); ElMessage.success('工序已跳过'); }
  catch (e) { ElMessage.error(e.response?.data?.error || '操作失败'); }
}
async function setOrderStatus(status) {
  try {
    const statusText = status === 'paused' ? '暂停' : '进行中';
    await ElMessageBox.confirm(`确定要将订单状态更改为 ${statusText} 吗？`, '确认', { type: 'warning' });
    await api.put(`/orders/${order.value.id}/status`, { status });
    await fetchOrder();
    ElMessage.success('状态已更新');
  } catch {}
}

function formatDateTime(val) {
  if (!val) return '—';
  return val.slice(0, 16).replace('T', ' ');
}

function stepStatusLabel(status) {
  const m = {
    pending: '等待中',
    in_progress: '进行中',
    completed: '已完成',
    skipped: '已跳过'
  };
  return m[status] || status;
}

// 工序传照相关方法
function getStepPhotos(stepId) {
  return (order.value?.documents || []).filter(
    d => d.step_id === stepId && /\.(jpg|jpeg|png|gif|webp|bmp|svg)$/i.test(d.filename)
  );
}

function getDocUrl(doc) {
  if (!doc?.file_path) return '';
  const fp = doc.file_path.replace(/\\/g, '/');
  return fp.startsWith('/') ? fp : '/' + fp;
}

function openPhotoUpload(step) {
  activeUploadStep.value = step;
  selectedFile.value = null;
  uploadDialogVisible.value = true;
}

function onFileChange(file) {
  selectedFile.value = file?.raw || null;
}

function doUpload() {}

function resetUpload() {
  activeUploadStep.value = null;
  selectedFile.value = null;
  if (uploadRef.value) uploadRef.value.clearFiles();
}

async function submitUpload() {
  if (!selectedFile.value || !activeUploadStep.value) return;
  uploading.value = true;
  try {
    const formData = new FormData();
    formData.append('file', selectedFile.value);
    formData.append('order_id', order.value.id);
    formData.append('category', activeUploadStep.value.name); // 用工序名作为分类，直通图纸管理组件
    formData.append('step_id', activeUploadStep.value.id);
    formData.append('title', `${activeUploadStep.value.name}确认照片`);
    
    // 1. 上传照片
    await api.post('/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    
    // 2. 推进工序完成
    await api.post(`/orders/${order.value.id}/steps/${activeUploadStep.value.id}/advance`);
    
    ElMessage.success('照片上传成功，工序已确认完成');
    uploadDialogVisible.value = false;
    await fetchOrder();
  } catch (e) {
    ElMessage.error(e.response?.data?.error || e.response?.data?.detail || '上传照片确认失败');
  } finally {
    uploading.value = false;
  }
}

function viewPhoto(photo) {
  fullscreenPhotoUrl.value = getDocUrl(photo);
}
</script>

<style scoped>
/* Any highly custom styles that Tailwind can't easily express */
.backdrop-blur {
  backdrop-filter: blur(8px);
}
</style>
