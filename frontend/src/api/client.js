/**
 * Central Axios instance.
 *
 * - Attaches the JWT access token to every request.
 * - On a 401, transparently tries to refresh the token once and replays the
 *   original request. If refresh fails, it clears tokens and the auth layer
 *   redirects to login.
 *
 * Token persistence helpers live in `tokenStore` so the auth context and the
 * interceptor share a single source of truth.
 */
import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

const ACCESS_KEY = "fad_access";
const REFRESH_KEY = "fad_refresh";

export const tokenStore = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set: (access, refresh) => {
    if (access) localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

const client = axios.create({ baseURL: BASE_URL });

client.interceptors.request.use((config) => {
  const token = tokenStore.getAccess();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let isRefreshing = false;

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const refresh = tokenStore.getRefresh();

    if (error.response?.status === 401 && refresh && !original._retried) {
      original._retried = true;
      try {
        if (!isRefreshing) {
          isRefreshing = true;
          const { data } = await axios.post(`${BASE_URL}/auth/refresh/`, {
            refresh,
          });
          tokenStore.set(data.access, null);
          isRefreshing = false;
        }
        original.headers.Authorization = `Bearer ${tokenStore.getAccess()}`;
        return client(original);
      } catch (refreshError) {
        isRefreshing = false;
        tokenStore.clear();
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export default client;
