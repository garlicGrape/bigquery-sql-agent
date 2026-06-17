import { useState, useRef, useCallback } from 'react'

interface QueryResponse {
  answer: string
  sql: string
  attempts: number
}

const s = {
  container: {
    background: '#fff',
    border: '1px solid #e2e8f0',
    borderRadius: '12px',
    padding: '28px',
    boxShadow: '0 1px 4px rgba(0,0,0,.06)',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    color: '#1a202c',
  } as React.CSSProperties,
  heading: {
    margin: '0 0 6px',
    fontSize: '18px',
    fontWeight: 600,
    letterSpacing: '-0.01em',
  } as React.CSSProperties,
  sub: {
    margin: '0 0 20px',
    fontSize: '13px',
    color: '#718096',
  } as React.CSSProperties,
  row: {
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
  error: {
    marginTop: '14px',
    padding: '10px 14px',
    background: '#fff5f5',
    border: '1px solid #fc8181',
    borderRadius: '8px',
    color: '#c53030',
    fontSize: '13px',
  } as React.CSSProperties,
  result: {
    marginTop: '20px',
  } as React.CSSProperties,
  answer: {
    margin: '0 0 16px',
    fontSize: '15px',
    lineHeight: 1.6,
    color: '#2d3748',
  } as React.CSSProperties,
  details: {
    borderRadius: '8px',
    overflow: 'hidden',
    border: '1px solid #2d3748',
  } as React.CSSProperties,
  summary: {
    padding: '8px 14px',
    background: '#2d3748',
    color: '#e2e8f0',
    fontSize: '12px',
    fontWeight: 600,
    letterSpacing: '0.05em',
    textTransform: 'uppercase' as const,
    cursor: 'pointer',
    userSelect: 'none' as const,
  } as React.CSSProperties,
  code: {
    margin: 0,
    padding: '16px',
    background: '#1a202c',
    color: '#e2e8f0',
    fontSize: '13px',
    fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", Menlo, monospace',
    lineHeight: 1.6,
    overflowX: 'auto' as const,
    whiteSpace: 'pre' as const,
  } as React.CSSProperties,
  meta: {
    marginTop: '10px',
    fontSize: '12px',
    color: '#a0aec0',
  } as React.CSSProperties,
  spinner: {
    display: 'inline-block',
    width: '14px',
    height: '14px',
    border: '2px solid #ffffff44',
    borderTopColor: '#fff',
    borderRadius: '50%',
    animation: 'spin .7s linear infinite',
  } as React.CSSProperties,
}

export function Widget({ apiUrl }: { apiUrl: string }) {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<QueryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const submit = useCallback(async () => {
    const q = question.trim()
    if (!q || loading) return
    setLoading(true)
    setError(null)
    setResponse(null)
    try {
      const res = await fetch(`${apiUrl}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`)
      setResponse(data as QueryResponse)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed')
    } finally {
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
      {/* Keyframe injected once via a style tag */}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <div style={s.container}>
        <h2 style={s.heading}>Ask the Citibike Data</h2>
        <p style={s.sub}>Powered by BigQuery · Gemini · LangGraph</p>
        <div style={s.row}>
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
            {loading ? <span style={s.spinner} /> : 'Ask'}
          </button>
        </div>

        {error && <div style={s.error}>{error}</div>}

        {response && (
          <div style={s.result}>
            <p style={s.answer}>{response.answer}</p>
            <details style={s.details}>
              <summary style={s.summary}>SQL</summary>
              <pre style={s.code}>{response.sql}</pre>
            </details>
            {response.attempts > 1 && (
              <p style={s.meta}>Needed {response.attempts} attempt{response.attempts > 1 ? 's' : ''} to generate a valid query.</p>
            )}
          </div>
        )}
      </div>
    </>
  )
}
