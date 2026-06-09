import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listAlerts } from "../api/fraud";
import usePaginatedQuery from "../hooks/usePaginatedQuery";
import Card from "../components/ui/Card";
import RiskBadge from "../components/ui/RiskBadge";
import Spinner from "../components/ui/Spinner";
import Pagination from "../components/ui/Pagination";
import { formatCurrency, ALERT_STATUS_LABELS } from "../lib/format";

const PAGE_SIZE = 20;
const STATUSES = ["open", "confirmed_fraud", "dismissed"];

const statusClasses = {
  open: "bg-amber-100 text-amber-700",
  confirmed_fraud: "bg-red-100 text-red-700",
  dismissed: "bg-slate-100 text-slate-600",
};

export default function AlertsPage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState("");

  const filters = useMemo(() => (status ? { status } : {}), [status]);
  const { results, count, page, setPage, loading } = usePaginatedQuery(
    listAlerts,
    filters
  );

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-800">Alert queue</h2>

      <Card>
        <div className="mb-4">
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="">All statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {ALERT_STATUS_LABELS[s]}
              </option>
            ))}
          </select>
        </div>

        {loading ? (
          <div className="flex h-48 items-center justify-center">
            <Spinner />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead>
                <tr className="text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                  <th className="px-3 py-2">Alert</th>
                  <th className="px-3 py-2">Merchant</th>
                  <th className="px-3 py-2">Amount</th>
                  <th className="px-3 py-2">Score</th>
                  <th className="px-3 py-2">Risk</th>
                  <th className="px-3 py-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {results.map((a) => (
                  <tr
                    key={a.id}
                    onClick={() => navigate(`/alerts/${a.id}`)}
                    className="cursor-pointer hover:bg-slate-50"
                  >
                    <td className="px-3 py-2 font-medium text-brand-700">
                      #{a.id}
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {a.transaction.merchant || "—"}
                    </td>
                    <td className="px-3 py-2 font-medium text-slate-800">
                      {formatCurrency(
                        a.transaction.amount,
                        a.transaction.currency
                      )}
                    </td>
                    <td className="px-3 py-2 text-slate-600">{a.risk_score}</td>
                    <td className="px-3 py-2">
                      <RiskBadge level={a.transaction.risk_level} />
                    </td>
                    <td className="px-3 py-2">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${statusClasses[a.status]}`}
                      >
                        {ALERT_STATUS_LABELS[a.status]}
                      </span>
                    </td>
                  </tr>
                ))}
                {!results.length && (
                  <tr>
                    <td colSpan={6} className="px-3 py-12 text-center text-slate-400">
                      No alerts found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        <Pagination
          page={page}
          pageSize={PAGE_SIZE}
          count={count}
          onChange={setPage}
        />
      </Card>
    </div>
  );
}
