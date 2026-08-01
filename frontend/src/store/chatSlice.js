import { createSlice } from '@reduxjs/toolkit'
import { parseComplaint, sendCorrection } from './complaintSlice'

const welcomeMessage = {
  id: 'welcome',
  role: 'assistant',
  text:
    'Ready to process new complaints. You can paste the raw email from the customer, or upload a PDF of the complaint report. I will extract the data and run the initial risk assessment.',
}

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [welcomeMessage],
  },
  reducers: {
    addUserMessage(state, action) {
      state.messages.push({ id: crypto.randomUUID(), role: 'user', text: action.payload })
    },
    addUserFileMessage(state, action) {
      state.messages.push({
        id: crypto.randomUUID(),
        role: 'user',
        file: action.payload,
      })
    },
    clearChat(state) {
      state.messages = [welcomeMessage]
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(parseComplaint.fulfilled, (state, action) => {
        state.messages.push({ id: crypto.randomUUID(), role: 'assistant', text: action.payload.reply })
      })
      .addCase(parseComplaint.rejected, (state, action) => {
        state.messages.push({
          id: crypto.randomUUID(),
          role: 'assistant',
          text: `Sorry, I couldn't parse that: ${action.error.message}`,
          isError: true,
        })
      })
      .addCase(sendCorrection.fulfilled, (state, action) => {
        state.messages.push({ id: crypto.randomUUID(), role: 'assistant', text: action.payload.reply })
      })
  },
})

export const { addUserMessage, addUserFileMessage, clearChat } = chatSlice.actions
export default chatSlice.reducer
