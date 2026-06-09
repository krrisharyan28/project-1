import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { RISK_COLORS } from "../../lib/format";

/** Donut chart of the low/medium/high transaction distribution. */
export default function RiskByLevelChart({ distribution }) {
  const data = [
    { name: "Low", value: distribution.low, level: "low" },
    { name: "Medium", value: distribution.medium, level: "medium" },
    { name: "High", value: distribution.high, level: "high" },
  ];

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius={60}
          outerRadius={90}
          paddingAngle={2}
        >
          {data.map((entry) => (
            <Cell key={entry.level} fill={RISK_COLORS[entry.level]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
