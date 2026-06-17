import { createRoot } from 'react-dom/client'
import { Widget } from './Widget'

const el = document.getElementById('bq-agent-widget')
if (el) {
  const apiUrl = el.dataset.apiUrl ?? 'http://localhost:8000'
  createRoot(el).render(<Widget apiUrl={apiUrl} />)
}
