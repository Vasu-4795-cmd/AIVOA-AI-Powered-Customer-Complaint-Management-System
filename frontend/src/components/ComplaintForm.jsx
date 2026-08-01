import { useDispatch, useSelector } from 'react-redux'
import { updateField, commitComplaint, resetForm } from '../store/complaintSlice'
import StatusBadge from './StatusBadge'

function Field({ label, name, value, onChange, placeholder, aiFilled, textarea, select, options }) {
  const commonProps = {
    id: name,
    value: value || '',
    onChange: (e) => onChange(name, e.target.value),
    placeholder: placeholder || 'Awaiting AI extraction...',
    className: aiFilled ? 'ai-filled' : '',
  }
  return (
    <div className="field">
      <label htmlFor={name}>{label}</label>
      {select ? (
        <select {...commonProps}>
          <option value="">Awaiting AI classification...</option>
          {options.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      ) : textarea ? (
        <textarea {...commonProps} rows={4} />
      ) : (
        <input type="text" {...commonProps} />
      )}
    </div>
  )
}

const SITE_OPTIONS = ['Manufacturing', 'Packaging', 'Warehouse', 'QC Lab', 'Dispatch']

export default function ComplaintForm() {
  const dispatch = useDispatch()
  const { fields, risk, bonus, status, committing, committedRef } = useSelector((s) => s.complaint)

  const onChange = (name, value) => dispatch(updateField({ key: name, value }))
  const canCommit = status === 'ready_to_commit' && !committing

  return (
    <div className="form-pane">
      <div className="form-header">
        <div>
          <h1 className="form-title">Log Customer Complaint</h1>
          <p className="form-subtitle">API &amp; FDF Quality Assurance Module</p>
        </div>
        <StatusBadge status={status} />
      </div>

      <section className="form-section">
        <p className="section-label">1. Origin &amp; Customer Details</p>
        <div className="field-grid">
          <Field label="Complaint Source" name="complaint_source" value={fields.complaint_source} onChange={onChange} />
          <Field label="Customer Name" name="customer_name" value={fields.customer_name} onChange={onChange} />
        </div>
      </section>

      <section className="form-section">
        <p className="section-label">2. Product &amp; Batch Identification</p>
        <div className="field-grid">
          <Field label="Product Name" name="product_name" value={fields.product_name} onChange={onChange} />
          <Field label="Product Strength / Grade" name="product_strength" value={fields.product_strength} onChange={onChange} />
          <Field label="Batch / Lot Number" name="batch_number" value={fields.batch_number} onChange={onChange} />
          <Field label="Affected Quantity" name="affected_quantity" value={fields.affected_quantity} onChange={onChange} />
          <Field label="Manufacturing Date" name="manufacturing_date" value={fields.manufacturing_date} onChange={onChange} />
          <Field label="Expiry Date" name="expiry_date" value={fields.expiry_date} onChange={onChange} />
        </div>
      </section>

      <section className="form-section">
        <p className="section-label">3. Facility &amp; Material Impact</p>
        <div className="field-grid">
          <Field
            label="Originating Site Block" name="originating_site_block"
            value={fields.originating_site_block} onChange={onChange}
            select options={SITE_OPTIONS}
          />
          <Field
            label="Impacted Non-Product Materials (NPM)" name="impacted_npm"
            value={fields.impacted_npm} onChange={onChange} placeholder="e.g., Primary packaging..."
          />
        </div>
      </section>

      <section className="form-section">
        <p className="section-label">4. Defect Analysis</p>
        <div className="field-grid single">
          <Field label="Complaint Category" name="complaint_category" value={fields.complaint_category} onChange={onChange} />
          <Field
            label="Complaint Description" name="complaint_description"
            value={fields.complaint_description} onChange={onChange} textarea
            placeholder="AI will synthesize the complaint into a formal QMS description..."
          />
        </div>

        <div className="risk-box">
          <p className="risk-box-title">🛡️ AI Copilot Risk Assessment</p>
          <div className="field-grid" style={{ marginBottom: 20 }}>
            <Field label="Severity (Suggested)" name="ai_severity" value={risk.ai_severity} onChange={() => {}} aiFilled />
            <Field label="Suggested Next Action" name="ai_suggested_next_action" value={risk.ai_suggested_next_action} onChange={() => {}} aiFilled />
          </div>
          <Field
            label="Initial Risk Assessment" name="ai_initial_risk_assessment"
            value={risk.ai_initial_risk_assessment} onChange={() => {}} textarea aiFilled
          />
          {bonus.ai_capa_recommendation && (
            <div style={{ marginTop: 16 }}>
              <Field
                label="CAPA Recommendation (Bonus AI)" name="ai_capa_recommendation"
                value={bonus.ai_capa_recommendation} onChange={() => {}} textarea aiFilled
              />
            </div>
          )}
          {bonus.ai_completeness_score != null && (
            <p style={{ fontSize: 12, color: '#6b7280', marginTop: 10 }}>
              Complaint completeness score: <strong>{bonus.ai_completeness_score}%</strong>
              {bonus.ai_duplicate_of && ' · ⚠️ Possible duplicate of an existing open complaint'}
            </p>
          )}
        </div>
      </section>

      <div className="commit-bar">
        {status === 'committed' ? (
          <div className="committed-banner">
            ✅ Committed to QMS Ledger — Reference {committedRef}
            <div style={{ marginTop: 10 }}>
              <button className="commit-btn" style={{ background: '#6b7280' }} onClick={() => dispatch(resetForm())}>
                Log Another Complaint
              </button>
            </div>
          </div>
        ) : (
          <button className="commit-btn" disabled={!canCommit} onClick={() => dispatch(commitComplaint())}>
            {committing ? 'Committing…' : 'Commit to QMS Ledger'}
          </button>
        )}
      </div>
    </div>
  )
}
