<template>
  <div class="bg-white dark:bg-industrial-800 border border-slate-200 dark:border-industrial-border rounded-xl p-5 shadow-lg">
    <!-- 标题栏 -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-5 border-b border-slate-100 dark:border-industrial-border pb-3">
      <div class="flex flex-col sm:flex-row sm:items-center gap-3 w-full sm:w-auto">
        <h2 class="text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 font-semibold flex items-center gap-2 shrink-0">
          <el-icon><Picture /></el-icon>工程图纸与附件
        </h2>
        <!-- 一级 Tab 切换：预览图 / 工程文件 -->
        <div class="flex bg-slate-100 dark:bg-industrial-700 rounded-lg p-0.5 text-xs w-full sm:w-fit justify-between sm:justify-start">
          <button
            @click="activeTab = 'preview'; activeSubCategory = '2D图'"
            :class="activeTab === 'preview'
              ? 'bg-blue-500 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'"
            class="px-3 py-1.5 rounded-md font-medium transition-all flex items-center gap-1 flex-1 sm:flex-none justify-center"
          >
            <span>预览图</span>
            <span 
              :class="activeTab === 'preview'
                ? 'bg-white/20 text-white'
                : 'bg-slate-200 dark:bg-industrial-500 text-slate-600 dark:text-slate-300'"
              class="px-1.5 py-0.5 rounded-full text-[9px]"
            >
              {{ totalPreviewCount }}
            </span>
          </button>
          <button
            @click="activeTab = 'engineering'; activeSubCategory = '2D图'"
            :class="activeTab === 'engineering'
              ? 'bg-blue-500 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'"
            class="px-3 py-1.5 rounded-md font-medium transition-all flex items-center gap-1 flex-1 sm:flex-none justify-center"
          >
            <span>工程文件</span>
            <span 
              :class="activeTab === 'engineering'
                ? 'bg-white/20 text-white'
                : 'bg-slate-200 dark:bg-industrial-500 text-slate-600 dark:text-slate-300'"
              class="px-1.5 py-0.5 rounded-full text-[9px]"
            >
              {{ totalEngineeringCount }}
            </span>
          </button>
        </div>
      </div>
      <el-button v-if="canEdit" type="primary" size="small" @click="openUpload" class="w-full sm:w-auto min-h-[36px] sm:min-h-0">
        <el-icon><Upload /></el-icon>&nbsp;上传文件
      </el-button>
    </div>

    <!-- 二级分类切换 -->
    <div class="mb-5">
      <div class="flex flex-wrap gap-2">
        <button
          v-for="cat in currentSubCategories"
          :key="cat"
          @click="activeSubCategory = cat"
          :class="activeSubCategory === cat
            ? 'bg-blue-500 text-white shadow-md shadow-blue-500/20'
            : 'bg-slate-100 dark:bg-industrial-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-industrial-600'"
          class="px-3.5 py-1.5 rounded-lg font-medium text-xs transition-all flex items-center gap-1.5"
        >
          <span>{{ cat }}</span>
          <span class="bg-black/10 dark:bg-white/10 px-1.5 py-0.5 rounded-full text-[9px]">
            {{ getSubCategoryCount(cat) }}
          </span>
        </button>
      </div>
    </div>

    <!-- ===== 内容展示区 ===== -->
    <div>
      <!-- 1. 预览图 Tab 的具体内容 -->
      <div v-if="activeTab === 'preview'">
        <div v-if="currentPreviewDocs.length" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          <div
            v-for="doc in currentPreviewDocs"
            :key="doc.id"
            class="group relative rounded-xl overflow-hidden border border-slate-200 dark:border-industrial-700 bg-slate-50 dark:bg-industrial-900/50 aspect-square cursor-pointer"
          >
            <!-- 描述信息提示气泡 -->
            <el-tooltip
              v-if="doc.description"
              :content="doc.description"
              placement="top"
              effect="dark"
            >
              <div class="absolute top-2 left-2 z-10 w-5 h-5 rounded-full bg-black/60 text-white flex items-center justify-center text-xs backdrop-blur-sm shadow">
                <el-icon><InfoFilled /></el-icon>
              </div>
            </el-tooltip>
            
            <img
              :src="getDocUrl(doc)"
              :alt="doc.title || doc.original_name"
              class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
              @error="onImgError($event)"
            />
            <!-- 悬浮操作层 -->
            <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-2 p-2">
              <button @click.stop="viewFullscreen(doc)" class="w-full py-1.5 text-xs font-medium bg-white/20 hover:bg-white/30 text-white rounded-lg backdrop-blur-sm transition">查看大图</button>
              <button v-if="canEdit" @click.stop="openEdit(doc)" class="w-full py-1.5 text-xs font-medium bg-blue-500/60 hover:bg-blue-500/80 text-white rounded-lg transition">编辑信息</button>
              <button v-if="canEdit" @click.stop="confirmDelete(doc)" class="w-full py-1.5 text-xs font-medium bg-red-500/60 hover:bg-red-500/80 text-white rounded-lg transition">删除</button>
            </div>
            <!-- 文件名 & 版本 -->
            <div class="absolute bottom-0 left-0 right-0 px-2 py-1.5 bg-gradient-to-t from-black/70 to-transparent">
              <p class="text-white text-[11px] truncate font-medium flex items-center gap-1">
                <span class="bg-blue-500 text-white text-[8px] px-1 rounded font-bold">V{{ doc.version }}</span>
                {{ doc.title || doc.original_name }}
              </p>
              <p class="text-white/60 text-[10px]">{{ formatDateTime(doc.created_at) }}</p>
            </div>
          </div>
        </div>
        <div v-else class="flex flex-col items-center justify-center py-14 text-slate-400 dark:text-slate-500">
          <el-icon class="text-4xl mb-3 opacity-50"><PictureFilled /></el-icon>
          <p class="text-sm">该分类下暂无预览图</p>
          <p v-if="canEdit" class="text-xs mt-1 opacity-70">点击右上角"上传文件"添加图片</p>
        </div>
      </div>

      <!-- 2. 工程文件 Tab 的具体内容 -->
      <div v-else-if="activeTab === 'engineering'">
        <div v-if="currentEngineeringDocs.length" class="space-y-2">
          <div
            v-for="doc in currentEngineeringDocs"
            :key="doc.id"
            class="flex flex-col sm:flex-row gap-3 sm:items-center justify-between px-4 py-3 rounded-xl border transition-colors"
            :class="doc.status === 'active'
              ? 'border-blue-200 dark:border-industrial-accent/40 bg-blue-50/50 dark:bg-industrial-accent/5'
              : 'border-slate-200 dark:border-industrial-700 bg-slate-50 dark:bg-industrial-900/40 opacity-60'"
          >
            <div class="flex items-center gap-3 w-full sm:w-auto flex-1 min-w-0">
              <!-- 文件图标 -->
              <div class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 text-xs font-bold uppercase"
                :class="fileIconClass(doc.original_name)">
                {{ fileExt(doc.original_name) }}
              </div>

              <!-- 文件信息 -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-medium text-sm text-slate-800 dark:text-slate-200 truncate max-w-xs">
                    {{ doc.title || doc.original_name }}
                  </span>
                <!-- 版本号标签 -->
                <span class="px-2 py-0.5 rounded text-[10px] font-bold border"
                  :class="doc.status === 'active'
                    ? 'bg-blue-100 dark:bg-industrial-accent/20 text-blue-600 dark:text-industrial-accent border-blue-200 dark:border-industrial-accent/40'
                    : 'bg-slate-100 dark:bg-industrial-700 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-industrial-600'">
                  V{{ doc.version }}
                </span>
                <el-tag v-if="doc.status === 'active'" size="small" type="success">当前版本</el-tag>
                <el-tag v-else-if="doc.status === 'deprecated'" size="small" type="info">历史版本</el-tag>
                <el-tag v-else-if="doc.status === 'pending'" size="small" type="warning">审核中</el-tag>
              </div>
              <div class="text-xs text-slate-400 dark:text-slate-500 mt-0.5 flex flex-wrap items-center gap-x-2">
                <span>{{ formatFileSize(doc.file_size) }}</span>
                <span>·</span>
                <span>{{ formatDateTime(doc.created_at) }}</span>
                <span v-if="doc.description" class="text-slate-500 dark:text-slate-400 font-normal">
                  · 描述: {{ doc.description }}
                </span>
              </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="flex items-center justify-end sm:justify-start gap-2 flex-wrap sm:flex-nowrap w-full sm:w-auto flex-shrink-0 mt-1 sm:mt-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100 dark:border-industrial-700/50">
              <a :href="getDocUrl(doc)" :download="doc.original_name" target="_blank">
                <el-button size="small" plain class="min-h-[36px] sm:min-h-0">
                  <el-icon><Download /></el-icon>
                </el-button>
              </a>
              <el-button v-if="canEdit" size="small" plain @click="openEdit(doc)" class="min-h-[36px] sm:min-h-0">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button v-if="canEdit && doc.status !== 'active'" size="small" type="primary" plain @click="setActive(doc)" class="min-h-[36px] sm:min-h-0">
                激活
              </el-button>
              <el-button v-if="canEdit" size="small" type="danger" plain @click="confirmDelete(doc)" class="min-h-[36px] sm:min-h-0">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
        <div v-else class="flex flex-col items-center justify-center py-14 text-slate-400 dark:text-slate-500">
          <el-icon class="text-4xl mb-3 opacity-50"><Document /></el-icon>
          <p class="text-sm">该分类下暂无工程文件</p>
          <p v-if="canEdit" class="text-xs mt-1 opacity-70">点击右上角"上传文件"添加工程文件</p>
        </div>
      </div>
    </div>
  </div>

  <!-- ===== 上传对话框 ===== -->
  <el-dialog v-model="uploadVisible" title="上传文件" width="480px" @close="resetUpload">
    <div class="space-y-4">
      <!-- 1. 文件类型选择（格式约束） -->
      <div>
        <p class="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">1. 选择文件格式约束</p>
        <div class="grid grid-cols-2 gap-3">
          <button
            @click="uploadCategory = '预览图'; onCategoryChange()"
            :class="uploadCategory === '预览图'
              ? 'border-blue-400 bg-blue-50 dark:bg-industrial-accent/10 text-blue-600 dark:text-industrial-accent'
              : 'border-slate-200 dark:border-industrial-600 text-slate-600 dark:text-slate-300 hover:border-slate-300'"
            class="flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-all cursor-pointer"
          >
            <el-icon class="text-xl"><PictureFilled /></el-icon>
            <div class="text-center">
              <div class="text-xs font-semibold">图片/预览图限制</div>
              <div class="text-[10px] opacity-60 mt-0.5">PNG · JPG · WebP · GIF</div>
            </div>
          </button>
          <button
            @click="uploadCategory = '工程文件'; onCategoryChange()"
            :class="uploadCategory === '工程文件'
              ? 'border-blue-400 bg-blue-50 dark:bg-industrial-accent/10 text-blue-600 dark:text-industrial-accent'
              : 'border-slate-200 dark:border-industrial-600 text-slate-600 dark:text-slate-300 hover:border-slate-300'"
            class="flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-all cursor-pointer"
          >
            <el-icon class="text-xl"><Document /></el-icon>
            <div class="text-center">
              <div class="text-xs font-semibold">工程文件限制</div>
              <div class="text-[10px] opacity-60 mt-0.5">CAD · UG · PDF · 压缩包</div>
            </div>
          </button>
        </div>
      </div>

      <!-- 2. 图纸种类选择 -->
      <div v-if="uploadCategory">
        <p class="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">2. 选择/输入图纸种类</p>
        <el-radio-group v-model="selectedDocType" class="flex flex-wrap gap-2">
          <el-radio-button
            v-for="cat in allExistingCategories"
            :key="cat"
            :label="cat"
          >{{ cat }}</el-radio-button>
          <el-radio-button label="自定义">自定义</el-radio-button>
        </el-radio-group>

        <!-- 自定义输入框 -->
        <div v-if="selectedDocType === '自定义'" class="mt-3">
          <el-input
            v-model="customDocType"
            placeholder="请输入自定义图纸种类（如：装配图、控制箱）"
            maxlength="20"
            show-word-limit
            clearable
          />
        </div>
      </div>

      <!-- 3. 上传区域 -->
      <div v-if="uploadCategory && isDocTypeReady">
        <p class="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">3. 选择要上传的文件</p>
        <el-upload
          ref="uploadRef"
          action=""
          :http-request="doUpload"
          :accept="uploadAccept"
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
            {{ uploadCategory === '预览图' ? '仅支持图片格式 (PNG/JPG/GIF/WebP/BMP/SVG)' : '支持格式 (CAD / UG / PDF / 压缩包)，最大 50MB' }}
          </div>
        </el-upload>
      </div>
    </div>

    <template #footer>
      <el-button @click="uploadVisible = false">取消</el-button>
      <el-button type="primary" :loading="uploading" :disabled="!uploadCategory || !isDocTypeReady || !selectedFile" @click="submitUpload">
        {{ uploading ? '上传中...' : '确认上传' }}
      </el-button>
    </template>
  </el-dialog>

  <!-- ===== 编辑对话框 ===== -->
  <el-dialog v-model="editVisible" title="编辑图纸信息" width="420px">
    <el-form label-width="60px" class="mt-2">
      <el-form-item label="标题">
        <el-input v-model="editForm.title" placeholder="图纸标题" maxlength="100" show-word-limit />
      </el-form-item>
      <el-form-item label="说明">
        <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="图纸描述（可选）" maxlength="500" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="editVisible = false">取消</el-button>
      <el-button type="primary" :loading="editSaving" @click="saveEdit">保存</el-button>
    </template>
  </el-dialog>

  <!-- ===== 全屏预览 ===== -->
  <teleport to="body">
    <div
      v-if="fullscreenDoc"
      class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/95 p-4"
      @click="fullscreenDoc = null"
    >
      <img
        :src="getDocUrl(fullscreenDoc)"
        :alt="fullscreenDoc.title || fullscreenDoc.original_name"
        class="max-w-full max-h-full object-contain rounded shadow-2xl"
        @click.stop
      />
      <!-- 关闭 + 下载 -->
      <div class="absolute top-4 right-4 flex gap-2">
        <a
          :href="getDocUrl(fullscreenDoc)"
          :download="fullscreenDoc.original_name"
          class="p-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition backdrop-blur-sm"
          title="下载"
          @click.stop
        >
          <el-icon><Download /></el-icon>
        </a>
        <button
          @click="fullscreenDoc = null"
          class="p-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition backdrop-blur-sm"
          title="关闭"
        >
          <el-icon><Close /></el-icon>
        </button>
      </div>
      <!-- 文件名 & 描述 -->
      <div class="absolute bottom-4 left-1/2 -translate-x-1/2 text-center text-white/80 text-sm bg-black/40 px-5 py-2.5 rounded-2xl backdrop-blur-sm max-w-lg">
        <p class="font-medium">{{ fullscreenDoc.title || fullscreenDoc.original_name }}</p>
        <p v-if="fullscreenDoc.description" class="text-xs text-white/60 mt-1">{{ fullscreenDoc.description }}</p>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  Picture, PictureFilled, Document, Upload, UploadFilled,
  Download, Edit, Delete, Close, InfoFilled
} from '@element-plus/icons-vue';
import { useAuthStore } from '../stores/auth.js';
import api from '../api/index.js';

const props = defineProps({
  orderId: { type: Number, required: true },
  orderNo: { type: String, required: true },
  documents: { type: Array, default: () => [] },
});

const emit = defineEmits(['refresh']);

const isMobile = ref(window.innerWidth < 768);
function onResize() { isMobile.value = window.innerWidth < 768; }
onMounted(() => window.addEventListener('resize', onResize));
onUnmounted(() => window.removeEventListener('resize', onResize));

const auth = useAuthStore();
const canEdit = computed(() => auth.isAdmin || auth.canEdit('drawings'));

// ────────────────────────── 一级 Tab 与二级种类状态 ──────────────────────────
const activeTab = ref('preview'); // 'preview' | 'engineering'
const activeSubCategory = ref('2D图'); // 默认选中 '2D图'

// 判断是否是图片格式
const isImageFile = (filename) => {
  if (!filename) return false;
  return /\.(jpg|jpeg|png|gif|webp|bmp|svg)$/i.test(filename);
};

// 预览图总数（所有图片）
const totalPreviewCount = computed(() => {
  return props.documents.filter(d => isImageFile(d.filename)).length;
});

// 工程文件总数（所有非图片）
const totalEngineeringCount = computed(() => {
  return props.documents.filter(d => !isImageFile(d.filename)).length;
});

// 动态计算所有已存在过的图纸分类（供上传对话框单选列表使用，包括默认的以及当前订单中已有的自定义分类）
const allExistingCategories = computed(() => {
  const defaultCats = ['2D图', '3D图', '热咀'];
  const existing = props.documents.map(d => d.category).filter(Boolean);
  return [...new Set([...defaultCats, ...existing])];
});

// 动态计算当前大类 Tab 下可切换的二级子分类列表
const currentSubCategories = computed(() => {
  const defaultCats = ['2D图', '3D图', '热咀'];
  // 仅在当前大类有文件的分类中提取已有的自定义分类
  const filteredDocs = props.documents.filter(d => 
    activeTab.value === 'preview' ? isImageFile(d.filename) : !isImageFile(d.filename)
  );
  const existing = filteredDocs.map(d => d.category).filter(Boolean);
  return [...new Set([...defaultCats, ...existing])];
});

// 获取当前大类和二级种类下的文档数量
function getSubCategoryCount(cat) {
  return props.documents.filter(d => 
    d.category === cat && 
    (activeTab.value === 'preview' ? isImageFile(d.filename) : !isImageFile(d.filename))
  ).length;
}

// 过滤当前大类及二级种类下的图片预览文档
const currentPreviewDocs = computed(() => {
  return props.documents
    .filter(d => d.category === activeSubCategory.value && isImageFile(d.filename))
    .sort((a, b) => b.version - a.version);
});

// 过滤当前大类及二级种类下的工程文件文档
const currentEngineeringDocs = computed(() => {
  return props.documents
    .filter(d => d.category === activeSubCategory.value && !isImageFile(d.filename))
    .sort((a, b) => b.version - a.version);
});

// ────────────────────────── URL 构建 ──────────────────────────
function getDocUrl(doc) {
  if (!doc?.file_path) return '';
  const fp = doc.file_path.replace(/\\/g, '/'); // 防御性处理反斜杠
  return fp.startsWith('/') ? fp : '/' + fp;
}

function onImgError(e) {
  e.target.style.display = 'none';
  e.target.parentElement.classList.add('img-error');
}

// ────────────────────────── 文件工具函数 ──────────────────────────
function fileExt(name) {
  if (!name) return '?';
  return name.split('.').pop()?.substring(0, 4)?.toUpperCase() || 'FILE';
}

function fileIconClass(name) {
  const ext = (name || '').split('.').pop()?.toLowerCase();
  if (['pdf'].includes(ext)) return 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400';
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400';
  if (['dwg', 'dxf', 'dwf'].includes(ext)) return 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400';
  if (['step', 'stp', 'iges', 'igs'].includes(ext)) return 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400';
  if (['prt', 'x_t', 'x_b'].includes(ext)) return 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400';
  return 'bg-slate-100 dark:bg-industrial-700 text-slate-500 dark:text-slate-400';
}

function formatFileSize(bytes) {
  if (!bytes) return '—';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatDateTime(val) {
  if (!val) return '—';
  return val.slice(0, 16).replace('T', ' ');
}

// ────────────────────────── 全屏预览 ──────────────────────────
const fullscreenDoc = ref(null);
function viewFullscreen(doc) { fullscreenDoc.value = doc; }

// ────────────────────────── 上传 ──────────────────────────
const uploadVisible = ref(false);
const uploadCategory = ref(''); // 对应格式约束（'预览图' | '工程文件'）
const selectedDocType = ref('2D图'); // 对应选中的分类，默认'2D图'
const customDocType = ref(''); // 用户填写的自定义图纸种类
const uploading = ref(false);
const uploadRef = ref(null);
const selectedFile = ref(null);

const isDocTypeReady = computed(() => {
  if (selectedDocType.value === '自定义') {
    return !!customDocType.value.trim();
  }
  return !!selectedDocType.value;
});

const uploadAccept = computed(() => {
  if (uploadCategory.value === '预览图') return 'image/*';
  return '.pdf,.zip,.rar,.7z,.tar,.gz,.dwg,.dxf,.dwf,.step,.stp,.iges,.igs,.prt,.x_t,.x_b';
});

function openUpload() {
  uploadCategory.value = '';
  selectedDocType.value = '2D图';
  customDocType.value = '';
  selectedFile.value = null;
  uploadVisible.value = true;
}

function resetUpload() {
  uploadCategory.value = '';
  selectedDocType.value = '2D图';
  customDocType.value = '';
  uploading.value = false;
  selectedFile.value = null;
}

// 监听分类切换时清空已选文件
function onCategoryChange() {
  selectedFile.value = null;
  if (uploadRef.value) uploadRef.value.clearFiles();
}

function onFileChange(file) {
  selectedFile.value = file?.raw || null;
}

async function submitUpload() {
  if (!uploadCategory.value) {
    ElMessage.warning('请先选择文件格式约束');
    return;
  }
  if (!isDocTypeReady.value) {
    ElMessage.warning('请输入自定义图纸种类名称');
    return;
  }
  if (!selectedFile.value) {
    ElMessage.warning('请先选择要上传的文件');
    return;
  }

  // 确定的最终分类字段（后端用来建文件夹和存储在 category 字段）
  const finalCategory = selectedDocType.value === '自定义'
    ? customDocType.value.trim()
    : selectedDocType.value;

  uploading.value = true;
  try {
    const formData = new FormData();
    formData.append('file', selectedFile.value);
    formData.append('order_id', props.orderId);
    formData.append('category', finalCategory);
    formData.append('title', selectedFile.value.name.replace(/\.[^.]+$/, ''));

    await api.post('/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    ElMessage.success(`上传成功！文件已存入「${finalCategory}」分类。`);
    // 上传成功后将当前列表默认切换到刚刚上传的大类和二级分类，方便用户直接查看
    activeTab.value = uploadCategory.value === '预览图' ? 'preview' : 'engineering';
    activeSubCategory.value = finalCategory;
    uploadVisible.value = false;
    emit('refresh');
  } catch (e) {
    const detail = e.response?.data?.detail || e.response?.data?.error;
    if (typeof detail === 'string') {
      ElMessage.error(detail);
    } else if (e.response?.status === 403) {
      ElMessage.error('权限不足：您没有上传图纸的权限');
    } else if (e.response?.status === 404) {
      ElMessage.error('上传失败：找不到对应订单');
    } else if (e.response?.status === 413 || (typeof detail === 'string' && detail.includes('50'))) {
      ElMessage.error('上传失败：文件大小超过 50MB 限制');
    } else if (typeof detail === 'string' && detail.includes('类型')) {
      ElMessage.error(detail);
    } else {
      ElMessage.error('上传失败，请检查文件格式或网络连接后重试');
    }
  } finally {
    uploading.value = false;
  }
}

// 处理 el-upload 的 http-request（设为空，由 submitUpload 手动触发）
function doUpload() {}

// ────────────────────────── 编辑 ──────────────────────────
const editVisible = ref(false);
const editSaving = ref(false);
const editingDoc = ref(null);
const editForm = ref({ title: '', description: '' });

function openEdit(doc) {
  editingDoc.value = doc;
  editForm.value = { title: doc.title || '', description: doc.description || '' };
  editVisible.value = true;
}

async function saveEdit() {
  editSaving.value = true;
  try {
    await api.put(`/documents/${editingDoc.value.id}`, editForm.value);
    ElMessage.success('保存成功');
    editVisible.value = false;
    emit('refresh');
  } catch (e) {
    const detail = e.response?.data?.detail || '保存失败';
    ElMessage.error(typeof detail === 'string' ? detail : '保存失败');
  } finally {
    editSaving.value = false;
  }
}

// ────────────────────────── 激活历史版本 ──────────────────────────
async function setActive(doc) {
  try {
    await api.put(`/documents/${doc.id}/status`, { status: 'active' });
    ElMessage.success(`V${doc.version} 已设为当前版本`);
    emit('refresh');
  } catch (e) {
    ElMessage.error('操作失败');
  }
}

// ────────────────────────── 删除 ──────────────────────────
async function confirmDelete(doc) {
  try {
    await ElMessageBox.confirm(
      `确定删除「${doc.title || doc.original_name}」？此操作不可恢复。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消', confirmButtonClass: 'el-button--danger' }
    );
    await api.delete(`/documents/${doc.id}`);
    ElMessage.success('已删除');
    emit('refresh');
  } catch (e) {
    if (e === 'cancel' || e === 'close') return;
    const detail = e.response?.data?.detail || '删除失败';
    ElMessage.error(typeof detail === 'string' ? detail : '删除失败');
  }
}
</script>

<style scoped>
.img-error::after {
  content: '图片加载失败';
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 12px;
  color: #9ca3af;
  background: #f9fafb;
}
</style>
