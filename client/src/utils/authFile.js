// 鉴权文件加载器：/uploads 静态直挂已移除（8/6 报告 P0-5），
// 图纸/照片改经 GET /api/documents/file 带 Token 以 blob 拉取，
// 在前端生成 objectURL 供 <img> / <a> 使用。
import { reactive } from 'vue';
import api from '../api/index.js';

// 组件级缓存：docId -> objectURL（'' 表示拉取失败，避免反复请求）
const urlCache = reactive({});
const pending = new Set();

async function _fetch(doc) {
  pending.add(doc.id);
  try {
    const res = await api.get('/documents/file', {
      params: { id: doc.id },
      responseType: 'blob',
    });
    urlCache[doc.id] = URL.createObjectURL(res.data);
  } catch (e) {
    console.error('文件加载失败', doc.id, e);
    urlCache[doc.id] = '';
  } finally {
    pending.delete(doc.id);
  }
}

/** 模板用（同步）：触发加载并返回当前缓存值，加载完成后响应式更新 */
export function getDocUrl(doc) {
  if (!doc?.id) return '';
  if (urlCache[doc.id] === undefined && !pending.has(doc.id)) {
    _fetch(doc);
  }
  return urlCache[doc.id] || '';
}

/** 事件处理用（异步）：等待真实 URL（如点击放大预览） */
export async function resolveDocUrl(doc) {
  if (!doc?.id) return '';
  if (urlCache[doc.id] === undefined || urlCache[doc.id] === '') {
    await _fetch(doc);
  }
  return urlCache[doc.id] || '';
}
