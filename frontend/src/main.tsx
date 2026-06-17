import { createRoot } from 'react-dom/client'
import { Widget } from './Widget'

const el = document.getElementById('bq-agent-widget')
if (el) {
  const params = new URLSearchParams(window.location.search)
  const apiUrl = params.get('api') ?? el.dataset.apiUrl ?? 'http://localhost:8000'
  createRoot(el).render(<Widget apiUrl={apiUrl} />)
}
