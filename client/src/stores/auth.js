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

  async function login(username, password) {
    const res = await api.post('/auth/login', { username, password });
    token.value = res.data.access_token;
    refreshTokenVal.value = res.data.refresh_token;
    user.value = res.data.user;
    localStorage.setItem('access_token', token.value);
    localStorage.setItem('refresh_token', refreshTokenVal.value);
    await fetchMe();
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
  }

  async function refreshAccess() {
    const res = await api.post('/auth/refresh', { refresh_token: refreshTokenVal.value });
    token.value = res.data.access_token;
    localStorage.setItem('access_token', token.value);
  }

  function logout() {
    api.post('/auth/logout', { refresh_token: refreshTokenVal.value }).catch(() => {});
    token.value = '';
    refreshTokenVal.value = '';
    user.value = null;
    permissions.value = [];
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  return { token, refreshToken: refreshTokenVal, user, permissions, isAdmin, loggedIn, login, fetchMe, refreshAccess, logout, canView, canEdit };
});
