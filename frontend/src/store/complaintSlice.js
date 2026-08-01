import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import api from '../api/client'

const emptyFields = {
  complaint_source: '',
  customer_name: '',
  product_name: '',
  product_strength: '',
  batch_number: '',
  affected_quantity: '',
  manufacturing_date: '',
  expiry_date: '',
  originating_site_block: '',
  impacted_npm: '',
  complaint_category: '',
  complaint_description: '',
}

const emptyRisk = {
  ai_severity: '',
  ai_suggested_next_action: '',
  ai_initial_risk_assessment: '',
}

const emptyBonus = {
  ai_completeness_score: null,
  ai_duplicate_of: null,
  ai_capa_recommendation: '',
  ai_summary: '',
}

export const parseComplaint = createAsyncThunk(
  'complaint/parse',
  async ({ text, file }) => {
    const form = new FormData()
    if (text) form.append('text', text)
    if (file) form.append('file', file)
    const { data } = await api.post('/api/copilot/parse', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  }
)

export const sendCorrection = createAsyncThunk(
  'complaint/correct',
  async (message, { getState }) => {
    const { fields } = getState().complaint
    const { data } = await api.post('/api/copilot/chat', {
      message,
      current_fields: fields,
    })
    return data
  }
)

export const commitComplaint = createAsyncThunk(
  'complaint/commit',
  async (_, { getState }) => {
    const { fields, risk, bonus, sourceText, sourceFilename } = getState().complaint
    const { data } = await api.post('/api/complaints', {
      ...fields,
      ...risk,
      ...bonus,
      source_raw_text: sourceText,
      source_filename: sourceFilename,
    })
    return data
  }
)

const complaintSlice = createSlice({
  name: 'complaint',
  initialState: {
    fields: emptyFields,
    risk: emptyRisk,
    bonus: emptyBonus,
    status: 'pending_triage', // pending_triage | ready_to_commit | committed
    sourceText: '',
    sourceFilename: '',
    parsing: false,
    committing: false,
    error: null,
    committedRef: null,
  },
  reducers: {
    updateField(state, action) {
      const { key, value } = action.payload
      state.fields[key] = value
    },
    resetForm(state) {
      state.fields = emptyFields
      state.risk = emptyRisk
      state.bonus = emptyBonus
      state.status = 'pending_triage'
      state.sourceText = ''
      state.sourceFilename = ''
      state.committedRef = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(parseComplaint.pending, (state) => {
        state.parsing = true
        state.error = null
      })
      .addCase(parseComplaint.fulfilled, (state, action) => {
        state.parsing = false
        state.fields = { ...state.fields, ...action.payload.fields }
        state.risk = action.payload.risk
        state.bonus = action.payload.bonus
        state.status = 'ready_to_commit'
      })
      .addCase(parseComplaint.rejected, (state, action) => {
        state.parsing = false
        state.error = action.error.message
      })
      .addCase(sendCorrection.fulfilled, (state, action) => {
        state.fields = { ...state.fields, ...action.payload.updated_fields }
      })
      .addCase(commitComplaint.pending, (state) => {
        state.committing = true
      })
      .addCase(commitComplaint.fulfilled, (state, action) => {
        state.committing = false
        state.status = 'committed'
        state.committedRef = action.payload.complaint_ref
      })
      .addCase(commitComplaint.rejected, (state, action) => {
        state.committing = false
        state.error = action.error.message
      })
  },
})

export const { updateField, resetForm } = complaintSlice.actions
export default complaintSlice.reducer
