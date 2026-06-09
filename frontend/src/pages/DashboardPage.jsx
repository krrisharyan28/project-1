import { useEffect, useState } from "react";
import { fetchStats } from "../api/fraud";
import Card from "../components/ui/Card";
import StatCard from "../components/ui/StatCard";
import Spinner from "../components/ui/Spinner";
import RiskByLevelChart from "../components/charts/RiskByLevelChart";
import FraudTrendChart from "../components/charts/FraudTrendChart";
import TopRulesChart from "../components/charts/TopRulesChart";

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchStats().then(setStats).catch(() => setError(true));
  }, []);

  if (error) {
    return <p className="text-sm text-red-600">Failed to load dashboard stats.</p>;
  }
  if (!stats) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-800">Overview</h2>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Transactions" value={stats.total_transactions} />
        <StatCard
          label="Open alerts"
          value={stats.open_alerts}
          accent="text-amber-600"
        />
        <StatCard
          label="Confirmed fraud"
          value={stats.confirmed_fraud}
          accent="text-red-600"
        />
        <StatCard
          label="Dismissed"
          value={stats.dismissed}
          accent="text-green-600"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Risk distribution">
          <RiskByLevelChart distribution={stats.risk_distribution} />
        </Card>
        <Card title="Flagged transactions over time">
          <FraudTrendChart data={stats.fraud_trend} />
        </Card>
        <Card title="Most triggered rules">
          <TopRulesChart data={stats.top_rules} />
        </Card>
        <Card title="Top countries (flagged)">
          {stats.top_countries.length ? (
            <ul className="divide-y divide-slate-100">
              {stats.top_countries.map((c) => (
                <li
                  key={c.country}
                  className="flex items-center justify-between py-2 text-sm"
                >
                  <span className="font-medium text-slate-700">{c.country}</span>
                  <span className="text-slate-500">{c.count}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-12 text-center text-sm text-slate-400">
              No flagged transactions yet.
            </p>
          )}
        </Card>
      </div>
    </div>
  );
}
