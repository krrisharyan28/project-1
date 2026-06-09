import { useMemo, useState } from "react";
import { listTransactions } from "../api/transactions";
import usePaginatedQuery from "../hooks/usePaginatedQuery";
import Card from "../components/ui/Card";
import RiskBadge from "../components/ui/RiskBadge";
import Spinner from "../components/ui/Spinner";
import Pagination from "../components/ui/Pagination";
import { formatCurrency, formatDateTime, RISK_LEVELS } from "../lib/format";

const PAGE_SIZE = 20;

export default function TransactionsPage() {
  const [riskLevel, setRiskLevel] = useState("");
  const [search, setSearch] = useState("");

  const filters = useMemo(() => {
    const f = {};
    if (riskLevel) f.risk_level = riskLevel;
    if (search) f.search = search;
    return f;
  }, [riskLevel, search]);

  const { results, count, page, setPage, loading } = usePaginatedQuery(
    listTransactions,
    filters
  );

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-800">Transactions</h2>

      <Card>
        <div className="mb-4 flex flex-wrap gap-3">
          <input
            type="text"
            placeholder="Search merchant, ID, customer…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-64 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
          <select
            value={riskLevel}
            onChange={(e) => setRiskLevel(e.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm capitalize focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="">All risk levels</option>
            {RISK_LEVELS.map((l) => (
              <option key={l} value={l} className="capitalize">
                {l}
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
                  <th className="px-3 py-2">ID</th>
                  <th className="px-3 py-2">Date</th>
                  <th className="px-3 py-2">Merchant</th>
                  <th className="px-3 py-2">Amount</th>
                  <th className="px-3 py-2">Country</th>
                  <th className="px-3 py-2">Score</th>
                  <th className="px-3 py-2">Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {results.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-mono text-xs text-slate-500">
                      {t.external_id}
                    </td>
                    <td className="px-3 py-2 text-slate-600">
                      {formatDateTime(t.timestamp)}
                    </td>
                    <td className="px-3 py-2 text-slate-700">{t.merchant || "—"}</td>
                    <td className="px-3 py-2 font-medium text-slate-800">
                      {formatCurrency(t.amount, t.currency)}
                    </td>
                    <td className="px-3 py-2 text-slate-600">{t.country || "—"}</td>
                    <td className="px-3 py-2 text-slate-600">{t.risk_score}</td>
                    <td className="px-3 py-2">
                      <RiskBadge level={t.risk_level} />
                    </td>
                  </tr>
                ))}
                {!results.length && (
                  <tr>
                    <td colSpan={7} className="px-3 py-12 text-center text-slate-400">
                      No transactions found.
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
