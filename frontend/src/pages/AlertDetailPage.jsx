import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getAlert, explainAlert, reviewAlert } from "../api/fraud";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import RiskBadge from "../components/ui/RiskBadge";
import Spinner from "../components/ui/Spinner";
import {
  formatCurrency,
  formatDateTime,
  ALERT_STATUS_LABELS,
} from "../lib/format";

function Field({ label, value }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="mt-0.5 text-sm font-medium text-slate-800">{value}</dd>
    </div>
  );
}

export default function AlertDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [alert, setAlert] = useState(null);
  const [error, setError] = useState("");
  const [explaining, setExplaining] = useState(false);
  const [explainError, setExplainError] = useState("");
  const [note, setNote] = useState("");
  const [reviewing, setReviewing] = useState(false);

  useEffect(() => {
    getAlert(id).then(setAlert).catch(() => setError("Failed to load alert."));
  }, [id]);

  async function handleExplain() {
    setExplaining(true);
    setExplainError("");
    try {
      const { ai_explanation } = await explainAlert(id);
      setAlert((prev) => ({ ...prev, ai_explanation }));
    } catch {
      setExplainError(
        "Could not generate explanation. Is the Ollama (llama3) service running?"
      );
    } finally {
      setExplaining(false);
    }
  }

  async function handleReview(status) {
    setReviewing(true);
    try {
      const updated = await reviewAlert(id, status, note);
      setAlert(updated);
    } finally {
      setReviewing(false);
    }
  }

  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (!alert) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner />
      </div>
    );
  }

  const t = alert.transaction;
  const reviewed = alert.status !== "open";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => navigate("/alerts")}
            className="text-sm text-brand-600 hover:underline"
          >
            ← Back to alerts
          </button>
          <h2 className="mt-1 text-xl font-semibold text-slate-800">
            Alert #{alert.id}
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <RiskBadge level={t.risk_level} />
          <span className="text-sm text-slate-500">
            Score {alert.risk_score}/100 · {ALERT_STATUS_LABELS[alert.status]}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Transaction facts */}
        <Card title="Transaction" className="lg:col-span-1">
          <dl className="grid grid-cols-2 gap-4">
            <Field label="External ID" value={t.external_id} />
            <Field label="Amount" value={formatCurrency(t.amount, t.currency)} />
            <Field label="Merchant" value={t.merchant || "—"} />
            <Field label="Category" value={t.category || "—"} />
            <Field label="Country" value={t.country || "—"} />
            <Field label="Channel" value={t.channel || "—"} />
            <Field label="Card" value={`••${t.card_last4 || "????"}`} />
            <Field label="Customer" value={t.customer_id || "—"} />
            <Field label="Time" value={formatDateTime(t.timestamp)} />
          </dl>
        </Card>

        {/* Rule hits */}
        <Card title="Why it was flagged" className="lg:col-span-2">
          <ul className="space-y-3">
            {alert.rule_hits.map((hit) => (
              <li
                key={hit.rule_code}
                className="flex items-start justify-between rounded-lg bg-slate-50 p-3"
              >
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    {hit.rule_label}
                  </p>
                  <p className="text-xs text-slate-500">{hit.detail}</p>
                </div>
                <span className="ml-3 shrink-0 rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700">
                  +{hit.weight}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      {/* AI explanation */}
      <Card
        title="AI explanation (Llama-3)"
        action={
          <Button
            variant="secondary"
            onClick={handleExplain}
            disabled={explaining}
          >
            {explaining
              ? "Generating…"
              : alert.ai_explanation
                ? "Regenerate"
                : "Explain with AI"}
          </Button>
        }
      >
        {explainError && <p className="text-sm text-red-600">{explainError}</p>}
        {alert.ai_explanation ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
            {alert.ai_explanation}
          </p>
        ) : (
          !explainError && (
            <p className="text-sm text-slate-400">
              No explanation yet. Click “Explain with AI” to generate a
              plain-English summary of this alert.
            </p>
          )
        )}
      </Card>

      {/* Review workflow */}
      <Card title="Analyst decision">
        {reviewed ? (
          <p className="text-sm text-slate-600">
            This alert was marked{" "}
            <span className="font-medium">
              {ALERT_STATUS_LABELS[alert.status]}
            </span>
            {alert.reviewed_by && ` by ${alert.reviewed_by}`}
            {alert.review_note && ` — “${alert.review_note}”`}.
          </p>
        ) : (
          <div className="space-y-3">
            <textarea
              placeholder="Optional review note…"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={2}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            <div className="flex gap-3">
              <Button
                variant="danger"
                disabled={reviewing}
                onClick={() => handleReview("confirmed_fraud")}
              >
                Confirm fraud
              </Button>
              <Button
                variant="success"
                disabled={reviewing}
                onClick={() => handleReview("dismissed")}
              >
                Dismiss
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
