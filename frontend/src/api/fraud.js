import client from "./client";

export async function listAlerts(params = {}) {
  const { data } = await client.get("/fraud/alerts/", { params });
  return data;
}

export async function getAlert(id) {
  const { data } = await client.get(`/fraud/alerts/${id}/`);
  return data;
}

export async function explainAlert(id) {
  const { data } = await client.post(`/fraud/alerts/${id}/explain/`);
  return data; // { id, ai_explanation }
}

export async function reviewAlert(id, status, note = "") {
  const { data } = await client.patch(`/fraud/alerts/${id}/review/`, {
    status,
    note,
  });
  return data;
}

export async function fetchStats() {
  const { data } = await client.get("/fraud/stats/");
  return data;
}
