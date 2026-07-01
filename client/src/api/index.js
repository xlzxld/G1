import axios from 'axios';
import { useAuthStore } from '../stores/auth.js';

const api = axios.create({ baseURL: '/api' });

api.interceptors.request.use((config) => {
  const auth = useAuthStore();
  if (auth.token) config.headers.Authorization = `Bearer ${auth.token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const auth = useAuthStore();
    
    if (error.response?.data) {
      if (error.response.data.detail && !error.response.data.error) {
        error.response.data.error = error.response.data.detail;
      }
    }
    
    if (error.response?.status === 401 && auth.refreshToken && !error.config._retry) {
      error.config._retry = true;
      try {
        await auth.refreshAccess();
        error.config.headers.Authorization = `Bearer ${auth.token}`;
        return api(error.config);
      } catch {
        auth.logout();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
