import client from "./client";

export async function listTransactions(params = {}) {
  const { data } = await client.get("/transactions/", { params });
  return data; // { count, next, previous, results }
}

export async function getTransaction(id) {
  const { data } = await client.get(`/transactions/${id}/`);
  return data;
}

export async function listBatches(params = {}) {
  const { data } = await client.get("/transactions/batches/", { params });
  return data;
}

export async function uploadCsv(file) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post("/transactions/upload/", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data; // { batch_id, filename, imported, flagged, alert_ids }
}
