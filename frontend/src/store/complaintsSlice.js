import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import * as api from "../api/api";

export const fetchComplaints = createAsyncThunk(
  "complaints/fetchAll",
  async () => api.listComplaints()
);

export const uploadAndExtract = createAsyncThunk(
  "complaints/uploadAndExtract",
  async (file) => api.extractFromFile(file)
);

export const submitComplaint = createAsyncThunk(
  "complaints/submit",
  async (payload) => api.createComplaint(payload)
);

export const runAiAnalysis = createAsyncThunk(
  "complaints/analyze",
  async (complaintId) => {
    const result = await api.analyzeComplaint(complaintId);
    return { complaintId, result };
  }
);

const initialState = {
  items: [],
  listStatus: "idle",

  draftFields: {
    customer_name: "",
    customer_email: "",
    product_name: "",
    batch_lot_number: "",
    complaint_category: "",
    complaint_description: "",
    manufacturing_site: "",
  },
  rawText: "",
  extractStatus: "idle",
  extractError: null,

  activeComplaint: null,
  submitStatus: "idle",
  submitError: null,

  aiResult: null,
  aiStatus: "idle",
  aiError: null,
};

const complaintsSlice = createSlice({
  name: "complaints",
  initialState,
  reducers: {
    setDraftField(state, action) {
      const { field, value } = action.payload;
      state.draftFields[field] = value;
    },
    resetDraft(state) {
      state.draftFields = initialState.draftFields;
      state.rawText = "";
      state.aiResult = null;
      state.activeComplaint = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchComplaints.pending, (state) => { state.listStatus = "loading"; })
      .addCase(fetchComplaints.fulfilled, (state, action) => {
        state.listStatus = "succeeded";
        state.items = action.payload;
      })
      .addCase(fetchComplaints.rejected, (state) => { state.listStatus = "failed"; })

      .addCase(uploadAndExtract.pending, (state) => {
        state.extractStatus = "loading";
        state.extractError = null;
      })
      .addCase(uploadAndExtract.fulfilled, (state, action) => {
        state.extractStatus = "succeeded";
        const { raw_text, ...fields } = action.payload;
        state.rawText = raw_text;
        Object.keys(state.draftFields).forEach((key) => {
          if (fields[key]) state.draftFields[key] = fields[key];
        });
      })
      .addCase(uploadAndExtract.rejected, (state, action) => {
        state.extractStatus = "failed";
        state.extractError = action.error.message;
      })

      .addCase(submitComplaint.pending, (state) => {
        state.submitStatus = "loading";
        state.submitError = null;
      })
      .addCase(submitComplaint.fulfilled, (state, action) => {
        state.submitStatus = "succeeded";
        state.activeComplaint = action.payload;
        state.items.unshift(action.payload);
      })
      .addCase(submitComplaint.rejected, (state, action) => {
        state.submitStatus = "failed";
        state.submitError = action.error.message;
      })

      .addCase(runAiAnalysis.pending, (state) => {
        state.aiStatus = "loading";
        state.aiError = null;
      })
      .addCase(runAiAnalysis.fulfilled, (state, action) => {
        state.aiStatus = "succeeded";
        state.aiResult = action.payload.result;
      })
      .addCase(runAiAnalysis.rejected, (state, action) => {
        state.aiStatus = "failed";
        state.aiError = action.error.message;
      });
  },
});

export const { setDraftField, resetDraft } = complaintsSlice.actions;
export default complaintsSlice.reducer;
