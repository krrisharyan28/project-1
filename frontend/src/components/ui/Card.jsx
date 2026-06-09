export default function Card({ title, action, className = "", children }) {
  return (
    <div
      className={`rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200 ${className}`}
    >
      {(title || action) && (
        <div className="mb-4 flex items-center justify-between">
          {title && (
            <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
          )}
          {action}
        </div>
      )}
      {children}
    </div>
  );
}
