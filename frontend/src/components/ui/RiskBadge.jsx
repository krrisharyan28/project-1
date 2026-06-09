import { riskBadgeClasses } from "../../lib/format";

export default function RiskBadge({ level }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize ring-1 ring-inset ${riskBadgeClasses(
        level
      )}`}
    >
      {level}
    </span>
  );
}
