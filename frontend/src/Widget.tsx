import { useState, useRef, useCallback, useEffect } from 'react'

interface QueryResponse {
  answer: string
  sql: string
  attempts: number
}

interface HistoryEntry {
  id: number
  question: string
  response?: QueryResponse
  error?: string
}

const LOADING_STEPS = [
  'Fetching schema…',
  'Drafting query…',
  'Validating SQL…',
  'Running on BigQuery…',
]

const s = {
  container: {
    background: '#fff',
    border: '1px solid #e2e8f0',
    borderRadius: '12px',
    padding: '28px',
    boxShadow: '0 1px 4px rgba(0,0,0,.06)',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    color: '#1a202c',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '20px',
  } as React.CSSProperties,
  header: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '4px',
  } as React.CSSProperties,
  heading: {
    margin: 0,
    fontSize: '18px',
    fontWeight: 600,
    letterSpacing: '-0.01em',
  } as React.CSSProperties,
  sub: {
    margin: 0,
    fontSize: '13px',
    color: '#718096',
  } as React.CSSProperties,
  history: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '16px',
    maxHeight: '420px',
    overflowY: 'auto' as const,
    paddingRight: '4px',
  } as React.CSSProperties,
  entry: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '10px',
  } as React.CSSProperties,
  questionBubble: {
    alignSelf: 'flex-end' as const,
    background: '#2b6cb0',
    color: '#fff',
    padding: '9px 14px',
    borderRadius: '14px 14px 4px 14px',
    fontSize: '14px',
    lineHeight: 1.5,
    maxWidth: '85%',
  } as React.CSSProperties,
  answerBubble: {
    alignSelf: 'flex-start' as const,
    background: '#f7fafc',
    border: '1px solid #e2e8f0',
    borderRadius: '14px 14px 14px 4px',
    padding: '12px 14px',
    fontSize: '14px',
    lineHeight: 1.6,
    color: '#2d3748',
    maxWidth: '95%',
    width: '100%',
  } as React.CSSProperties,
  answerText: {
    margin: '0 0 12px',
  } as React.CSSProperties,
  details: {
    borderRadius: '8px',
    overflow: 'hidden',
    border: '1px solid #2d3748',
  } as React.CSSProperties,
  summaryRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '7px 12px',
    background: '#2d3748',
  } as React.CSSProperties,
  summaryLabel: {
    color: '#e2e8f0',
    fontSize: '11px',
    fontWeight: 700,
    letterSpacing: '0.06em',
    textTransform: 'uppercase' as const,
  } as React.CSSProperties,
  copyBtn: {
    background: 'transparent',
    border: '1px solid #4a5568',
    borderRadius: '5px',
    color: '#a0aec0',
    fontSize: '11px',
    padding: '2px 8px',
    cursor: 'pointer',
    transition: 'color .15s, border-color .15s',
  } as React.CSSProperties,
  code: {
    margin: 0,
    padding: '14px 16px',
    background: '#1a202c',
    color: '#e2e8f0',
    fontSize: '12.5px',
    fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", Menlo, monospace',
    lineHeight: 1.65,
    overflowX: 'auto' as const,
    whiteSpace: 'pre' as const,
  } as React.CSSProperties,
  meta: {
    marginTop: '8px',
    fontSize: '11.5px',
    color: '#a0aec0',
  } as React.CSSProperties,
  errorBubble: {
    alignSelf: 'flex-start' as const,
    background: '#fff5f5',
    border: '1px solid #fc8181',
    borderRadius: '14px 14px 14px 4px',
    padding: '10px 14px',
    color: '#c53030',
    fontSize: '13px',
    maxWidth: '90%',
  } as React.CSSProperties,
  loadingBubble: {
    alignSelf: 'flex-start' as const,
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    background: '#f7fafc',
    border: '1px solid #e2e8f0',
    borderRadius: '14px 14px 14px 4px',
    padding: '10px 14px',
    fontSize: '13px',
    color: '#718096',
  } as React.CSSProperties,
  spinner: {
    display: 'inline-block',
    width: '13px',
    height: '13px',
    border: '2px solid #cbd5e0',
    borderTopColor: '#2b6cb0',
    borderRadius: '50%',
    flexShrink: 0,
    animation: 'spin .7s linear infinite',
  } as React.CSSProperties,
  inputRow: {
    display: 'flex',
    gap: '8px',
  } as React.CSSProperties,
  input: {
    flex: 1,
    padding: '10px 14px',
    fontSize: '14px',
    border: '1px solid #cbd5e0',
    borderRadius: '8px',
    outline: 'none',
    color: '#1a202c',
    background: '#fff',
    transition: 'border-color .15s',
  } as React.CSSProperties,
  button: {
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: 600,
    background: '#2b6cb0',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    whiteSpace: 'nowrap' as const,
    transition: 'background .15s',
  } as React.CSSProperties,
  buttonDisabled: {
    background: '#a0aec0',
    cursor: 'not-allowed',
  } as React.CSSProperties,
}

function SqlBlock({ sql }: { sql: string }) {
  const [copied, setCopied] = useState(false)

  const copy = () => {
    navigator.clipboard.writeText(sql).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    })
  }

  return (
    <details style={s.details}>
      <summary style={{ listStyle: 'none' }}>
        <div style={s.summaryRow}>
          <span style={s.summaryLabel}>SQL</span>
          <button style={s.copyBtn} onClick={e => { e.preventDefault(); copy() }}>
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </summary>
      <pre style={s.code}>{sql}</pre>
    </details>
  )
}

function LoadingBubble({ step }: { step: string }) {
  return (
    <div style={s.loadingBubble}>
      <span style={s.spinner} />
      {step}
    </div>
  )
}

let idCounter = 0

export function Widget({ apiUrl }: { apiUrl: string }) {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingStep, setLoadingStep] = useState(0)
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const inputRef = useRef<HTMLInputElement>(null)
  const historyRef = useRef<HTMLDivElement>(null)
  const stepTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Auto-scroll history to bottom when new entries arrive
  useEffect(() => {
    if (historyRef.current) {
      historyRef.current.scrollTop = historyRef.current.scrollHeight
    }
  }, [history, loading])

  const startStepCycle = () => {
    setLoadingStep(0)
    let i = 0
    stepTimerRef.current = setInterval(() => {
      i = Math.min(i + 1, LOADING_STEPS.length - 1)
      setLoadingStep(i)
    }, 1800)
  }

  const stopStepCycle = () => {
    if (stepTimerRef.current) {
      clearInterval(stepTimerRef.current)
      stepTimerRef.current = null
    }
  }

  const submit = useCallback(async () => {
    const q = question.trim()
    if (!q || loading) return

    const id = ++idCounter
    setHistory(h => [...h, { id, question: q }])
    setQuestion('')
    setLoading(true)
    startStepCycle()

    try {
      const res = await fetch(`${apiUrl}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`)
      setHistory(h => h.map(e => e.id === id ? { ...e, response: data as QueryResponse } : e))
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Request failed'
      setHistory(h => h.map(e => e.id === id ? { ...e, error: msg } : e))
    } finally {
      stopStepCycle()
      setLoading(false)
      inputRef.current?.focus()
    }
  }, [question, loading, apiUrl])

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') submit()
  }

  const btnStyle = loading || !question.trim()
    ? { ...s.button, ...s.buttonDisabled }
    : s.button

  return (
    <>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        details > summary { list-style: none; }
        details > summary::-webkit-details-marker { display: none; }
      `}</style>
      <div style={s.container}>
        <div style={s.header}>
          <h2 style={s.heading}>Ask the Citibike Data</h2>
          <p style={s.sub}>Powered by Anthropic Claude · LangGraph · BigQuery</p>
        </div>

        {history.length > 0 && (
          <div style={s.history} ref={historyRef}>
            {history.map(entry => (
              <div key={entry.id} style={s.entry}>
                <div style={s.questionBubble}>{entry.question}</div>

                {entry.response && (
                  <div style={s.answerBubble}>
                    <p style={s.answerText}>{entry.response.answer}</p>
                    <SqlBlock sql={entry.response.sql} />
                    {entry.response.attempts > 1 && (
                      <p style={s.meta}>
                        Needed {entry.response.attempts} attempts to generate a valid query.
                      </p>
                    )}
                  </div>
                )}

                {entry.error && (
                  <div style={s.errorBubble}>{entry.error}</div>
                )}
              </div>
            ))}

            {loading && (
              <LoadingBubble step={LOADING_STEPS[loadingStep]} />
            )}
          </div>
        )}

        <div style={s.inputRow}>
          <input
            ref={inputRef}
            style={s.input}
            type="text"
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={onKey}
            placeholder="e.g. Which stations were busiest in July 2018?"
            disabled={loading}
            autoComplete="off"
          />
          <button style={btnStyle} onClick={submit} disabled={loading || !question.trim()}>
            Ask
          </button>
        </div>
      </div>
    </>
  )
}
