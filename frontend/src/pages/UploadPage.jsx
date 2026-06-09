import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadCsv } from "../api/transactions";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";

export default function UploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError("");
    setResult(null);
    try {
      const data = await uploadCsv(file);
      setResult(data);
    } catch (err) {
      setError(
        err.response?.data?.error?.message ||
          err.response?.data?.detail ||
          "Upload failed. Check the CSV format and try again."
      );
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-800">Upload transactions</h2>

      <Card className="max-w-2xl">
        <form onSubmit={handleUpload} className="space-y-4">
          <p className="text-sm text-slate-500">
            Upload a CSV with columns:{" "}
            <code className="rounded bg-slate-100 px-1 text-xs">
              external_id, timestamp, amount, currency, merchant, category,
              country, channel, card_last4, customer_id
            </code>
            . Transactions are scored on import.
          </p>

          <input
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files[0] ?? null)}
            className="block w-full text-sm text-slate-600 file:mr-4 file:rounded-md file:border-0 file:bg-brand-50 file:px-4 file:py-2 file:text-sm file:font-medium file:text-brand-700 hover:file:bg-brand-100"
          />

          {error && <p className="text-sm text-red-600">{error}</p>}

          <Button type="submit" disabled={!file || uploading}>
            {uploading ? "Uploading & scoring…" : "Upload & score"}
          </Button>
        </form>
      </Card>

      {result && (
        <Card title="Import result" className="max-w-2xl">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-semibold text-slate-800">
                {result.imported}
              </p>
              <p className="text-xs text-slate-500">Imported</p>
            </div>
            <div>
              <p className="text-2xl font-semibold text-red-600">
                {result.flagged}
              </p>
              <p className="text-xs text-slate-500">Flagged</p>
            </div>
            <div>
              <p className="text-2xl font-semibold text-slate-800">
                {result.filename}
              </p>
              <p className="text-xs text-slate-500">File</p>
            </div>
          </div>
          <div className="mt-4 flex gap-3">
            <Button onClick={() => navigate("/alerts")}>View alerts</Button>
            <Button variant="secondary" onClick={() => navigate("/transactions")}>
              View transactions
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
