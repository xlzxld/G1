import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../api/index.js';

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || '');
  const refreshTokenVal = ref(localStorage.getItem('refresh_token') || '');
  const user = ref(null);
  const permissions = ref([]);

  const isAdmin = computed(() => user.value?.is_admin ?? false);
  const loggedIn = computed(() => !!user.value);

  function canView(pageKey) {
    if (isAdmin.value) return true;
    const p = permissions.value.find(x => x.page_key === pageKey);
    return p ? !!p.can_view : false;
  }

  function canEdit(pageKey) {
    if (isAdmin.value) return true;
    const p = permissions.value.find(x => x.page_key === pageKey);
    return p ? !!p.can_edit : false;
  }

  const notifications = ref([]);
  const unreadNotifications = computed(() => notifications.value.filter(n => !n.is_read));
  const unreadCount = computed(() => unreadNotifications.value.length);
  const eventSource = ref(null);

  function setupSSE() {
    if (eventSource.value) {
      eventSource.value.close();
      eventSource.value = null;
    }
    if (!token.value) return;

    const streamUrl = `/api/notifications/stream?token=${encodeURIComponent(token.value)}`;
    const es = new EventSource(streamUrl);
    
    es.onmessage = (event) => {
      if (event.data === 'refresh') {
        fetchNotifications();
      }
    };
    
    es.onerror = () => {
      // 浏览器 EventSource 在连接中断时会自动尝试重连，在此处只做警告提示
      console.warn("SSE connection error or closed, EventSource will automatically retry in the background.");
    };
    
    eventSource.value = es;
  }

  function closeSSE() {
    if (eventSource.value) {
      eventSource.value.close();
      eventSource.value = null;
    }
  }

  async function fetchNotifications() {
    if (!token.value) return;
    try {
      const res = await api.get('/notifications');
      notifications.value = res.data;
    } catch (e) {
      console.error(e);
    }
  }

  async function login(username, password) {
    const res = await api.post('/auth/login', { username, password });
    token.value = res.data.access_token;
    refreshTokenVal.value = res.data.refresh_token;
    user.value = res.data.user;
    localStorage.setItem('access_token', token.value);
    localStorage.setItem('refresh_token', refreshTokenVal.value);
    await fetchMe();
    setupSSE();
  }

  async function fetchMe() {
    const res = await api.get('/auth/me');
    user.value = {
      id: res.data.id,
      username: res.data.username,
      display_name: res.data.display_name,
      role_label: res.data.role_label,
      is_admin: res.data.is_admin,
    };
    permissions.value = res.data.permissions || [];
    // 刷新页面再次获取个人信息时，如果已登录，自动打开实时通知流
    setupSSE();
  }

  async function refreshAccess() {
    const res = await api.post('/auth/refresh', { refresh_token: refreshTokenVal.value });
    token.value = res.data.access_token;
    localStorage.setItem('access_token', token.value);
    setupSSE();
  }

  async function markNotificationRead(id) {
    try {
      await api.put(`/notifications/${id}/read`);
      await fetchNotifications();
    } catch (e) {
      console.error(e);
    }
  }

  async function markAllNotificationsRead() {
    try {
      await api.put('/notifications/read-all');
      await fetchNotifications();
    } catch (e) {
      console.error(e);
    }
  }

  function logout() {
    api.post('/auth/logout', { refresh_token: refreshTokenVal.value }).catch(() => {});
    closeSSE();
    token.value = '';
    refreshTokenVal.value = '';
    user.value = null;
    permissions.value = [];
    notifications.value = [];
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  return { 
    token, 
    refreshToken: refreshTokenVal, 
    user, 
    permissions, 
    isAdmin, 
    loggedIn, 
    login, 
    fetchMe, 
    refreshAccess, 
    logout, 
    canView, 
    canEdit,
    notifications,
    unreadNotifications,
    unreadCount,
    fetchNotifications,
    markNotificationRead,
    markAllNotificationsRead,
    setupSSE,
    closeSSE
  };
});
