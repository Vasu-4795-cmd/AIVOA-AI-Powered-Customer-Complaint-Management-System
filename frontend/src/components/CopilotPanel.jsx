import { useEffect, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { parseComplaint, sendCorrection } from '../store/complaintSlice'
import { addUserMessage, addUserFileMessage } from '../store/chatSlice'

export default function CopilotPanel() {
  const dispatch = useDispatch()
  const { messages } = useSelector((s) => s.chat)
  const { parsing, status } = useSelector((s) => s.complaint)
  const [input, setInput] = useState('')
  const [dragging, setDragging] = useState(false)
  const fileInputRef = useRef(null)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, parsing])

  const isFirstParse = status === 'pending_triage'

  const submitText = () => {
    const text = input.trim()
    if (!text) return
    dispatch(addUserMessage(text))
    setInput('')
    if (isFirstParse) {
      dispatch(parseComplaint({ text }))
    } else {
      dispatch(sendCorrection(text))
    }
  }

  const submitFile = (file) => {
    if (!file) return
    dispatch(addUserFileMessage({ name: file.name, type: 'PDF Document' }))
    dispatch(parseComplaint({ file }))
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter') submitText()
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) submitFile(file)
  }

  return (
    <div className="copilot-pane">
      <div className="copilot-header">
        <div>
          <p className="copilot-title">🧪 AIVOA Copilot</p>
          <p className="copilot-subtitle">Drop complaint files or paste text below.</p>
        </div>
        <span className="live-dot" />
      </div>

      <div className="chat-scroll" ref={scrollRef}>
        {messages.map((m) => (
          <div key={m.id} className={`msg-row ${m.role}`}>
            <div className={`avatar ${m.role}`}>{m.role === 'assistant' ? '⚡' : '🙂'}</div>
            {m.file ? (
              <div className="bubble file-chip">
                <div className="file-chip-icon">📄</div>
                <div>
                  <div className="file-chip-name">{m.file.name}</div>
                  <div className="file-chip-sub">{m.file.type}</div>
                </div>
              </div>
            ) : (
              <div className={`bubble ${m.role}${m.isError ? ' error' : ''}`}>{m.text}</div>
            )}
          </div>
        ))}
        {parsing && (
          <div className="msg-row assistant">
            <div className="avatar assistant">⚡</div>
            <div className="bubble assistant">
              <div className="typing-dots"><span /><span /><span /></div>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input-bar">
        <div
          className={`chat-input-row ${dragging ? 'dragging' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <button className="icon-btn" title="Attach PDF / email" onClick={() => fileInputRef.current?.click()}>
            📎
          </button>
          <input
            type="file"
            accept=".pdf,.txt,.eml"
            className="hidden-file-input"
            ref={fileInputRef}
            onChange={(e) => submitFile(e.target.files?.[0])}
          />
          <input
            type="text"
            placeholder="Type a message or paste a complaint..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
          />
          <button className="send-btn" disabled={!input.trim() || parsing} onClick={submitText}>
            ✓
          </button>
        </div>
      </div>
      <p className="footer-note">POWERED BY LANGGRAPH</p>
    </div>
  )
}
