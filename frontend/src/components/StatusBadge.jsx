const CONFIG = {
  pending_triage: { label: 'Pending Triage', cls: 'pending', dot: false },
  ready_to_commit: { label: 'Ready to Commit', cls: 'ready', dot: true },
  committed: { label: 'Committed', cls: 'committed', dot: true },
}

export default function StatusBadge({ status }) {
  const cfg = CONFIG[status] || CONFIG.pending_triage
  return (
    <span className={`status-badge ${cfg.cls}`}>
      {cfg.dot && <span className="status-dot" />}
      {cfg.label}
    </span>
  )
}
