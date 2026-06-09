import client, { tokenStore } from "./client";

export async function login(username, password) {
  const { data } = await client.post("/auth/login/", { username, password });
  tokenStore.set(data.access, data.refresh);
  return data;
}

export async function register(payload) {
  const { data } = await client.post("/auth/register/", payload);
  return data;
}

export async function fetchMe() {
  const { data } = await client.get("/auth/me/");
  return data;
}

export function logout() {
  tokenStore.clear();
}
