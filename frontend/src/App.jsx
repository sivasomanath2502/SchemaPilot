import { useState, useEffect, useRef, useCallback } from 'react'
import './App.css'

const API_BASE = 'http://localhost:8000'
const POLL_INTERVAL_MS = 5000

const EXAMPLE_REQUIREMENT =
  'Design a database for an online ticket booking system. Users should be able ' +
  'to search events, select seats and book tickets. Multiple users may try to ' +
  'book the same seat simultaneously. Double booking must never occur.'

function useElapsedSeconds(isRunning) {
  const [elapsed, setElapsed] = useState(0)
  useEffect(() => {
    if (!isRunning) return
    setElapsed(0)
    const start = Date.now()
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - start) / 1000)), 1000)
    return () => clearInterval(id)
  }, [isRunning])
  return elapsed
}

function formatElapsed(sec) {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function SeverityBadge({ severity }) {
  return <span className={`badge badge-${severity}`}>{severity}</span>
}

function Pipeline({ activeStage }) {
  const stages = ['Requirement', 'Selection', 'Schema', 'Review']
  return (
    <div className="pipeline" aria-hidden="true">
      {stages.map((stage, i) => (
        <div className="pipeline-stage" key={stage}>
          <div className={`pipeline-node ${activeStage === i ? 'active' : ''}`}>
            <span className="pipeline-node-index">{i + 1}</span>
          </div>
          <span className="pipeline-label">{stage}</span>
          {i < stages.length - 1 && <div className="pipeline-connector" />}
        </div>
      ))}
    </div>
  )
}

function RequirementTab({ requirement }) {
  if (!requirement) return null
  return (
    <div className="tab-panel">
      <dl className="kv-grid">
        <dt>Application</dt>
        <dd>{requirement.application}</dd>
        <dt>Critical invariant</dt>
        <dd className="highlight">{requirement.critical_invariant || '—'}</dd>
        <dt>Consistency</dt>
        <dd>{requirement.consistency}</dd>
        <dt>Concurrency</dt>
        <dd>{requirement.concurrency}</dd>
        <dt>Workload</dt>
        <dd>{requirement.workload}</dd>
        <dt>Read/write pattern</dt>
        <dd>{requirement.read_write_ratio}</dd>
        <dt>Search required</dt>
        <dd>{requirement.search_required ? 'Yes' : 'No'}</dd>
        <dt>Expected scale</dt>
        <dd>{requirement.expected_scale}</dd>
      </dl>
      <h4>Entities</h4>
      <div className="chip-row">
        {(requirement.entities || []).map((e) => (
          <span className="chip" key={e}>{e}</span>
        ))}
      </div>
    </div>
  )
}

function SelectionTab({ selection }) {
  if (!selection) return null
  return (
    <div className="tab-panel">
      <div className="recommendation-card">
        <span className="eyebrow">Recommended primary database</span>
        <h3>{selection.primary_database}</h3>
        <p>{selection.primary_reasoning}</p>
      </div>

      {selection.supporting_components?.length > 0 && (
        <>
          <h4>Supporting components</h4>
          <table className="data-table">
            <thead>
              <tr><th>Component</th><th>Purpose</th><th>Required</th></tr>
            </thead>
            <tbody>
              {selection.supporting_components.map((c, i) => (
                <tr key={i}>
                  <td>{c.component}</td>
                  <td>{c.purpose}</td>
                  <td>{c.required ? 'Yes' : 'Optional'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {selection.alternatives?.length > 0 && (
        <>
          <h4>Alternatives considered</h4>
          {selection.alternatives.map((a, i) => (
            <div className="reasoning-item" key={i}>
              <strong>{a.database}</strong>
              <p>{a.reasoning}</p>
            </div>
          ))}
        </>
      )}

      {selection.rejected?.length > 0 && (
        <>
          <h4>Rejected</h4>
          {selection.rejected.map((r, i) => (
            <div className="reasoning-item reasoning-rejected" key={i}>
              <strong>{r.database}</strong>
              <p>{r.reason}</p>
            </div>
          ))}
        </>
      )}
    </div>
  )
}

function SchemaTab({ schema }) {
  if (!schema) return null
  return (
    <div className="tab-panel">
      <h4>Entities &amp; relationships</h4>
      <div className="chip-row">
        {(schema.entities || []).map((e) => (
          <span className="chip" key={e.name} title={e.description}>{e.name}</span>
        ))}
      </div>
      <ul className="relationship-list">
        {(schema.relationships || []).map((r, i) => (
          <li key={i}>
            <span className="mono">{r.from}</span> → <span className="mono">{r.to}</span>
            <span className="rel-type">{r.type}</span>
          </li>
        ))}
      </ul>

      <h4>Transaction strategy</h4>
      <p>{schema.transaction_strategy}</p>

      <h4>SQL DDL {schema.validation && (
        <span className={`badge badge-${schema.validation.final_valid ? 'ok' : 'critical'}`}>
          {schema.validation.final_valid ? 'validated against MySQL' : 'validation unresolved'}
        </span>
      )}</h4>
      <pre className="code-block"><code>{schema.sql_ddl}</code></pre>

      {schema.indexes?.length > 0 && (
        <>
          <h4>Indexes</h4>
          <table className="data-table">
            <thead><tr><th>Table</th><th>Columns</th><th>Reason</th></tr></thead>
            <tbody>
              {schema.indexes.map((idx, i) => (
                <tr key={i}>
                  <td className="mono">{idx.table}</td>
                  <td className="mono">{(idx.columns || []).join(', ')}</td>
                  <td>{idx.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {schema.important_queries?.length > 0 && (
        <>
          <h4>Important queries</h4>
          {schema.important_queries.map((q, i) => (
            <div key={i} className="query-item">
              <span className="query-desc">{q.description}</span>
              <pre className="code-block small"><code>{q.sql}</code></pre>
            </div>
          ))}
        </>
      )}
    </div>
  )
}

function ReviewTab({ review, cycleCount }) {
  if (!review) return null
  const hasIssues = review.issues && review.issues.length > 0
  return (
    <div className="tab-panel">
      <p className="cycle-note">
        Ran {cycleCount} review-improve cycle{cycleCount === 1 ? '' : 's'}.
      </p>
      <div className={`assessment-card ${hasIssues ? 'assessment-warn' : 'assessment-ok'}`}>
        <p>{review.overall_assessment}</p>
      </div>

      {hasIssues ? (
        review.issues.map((issue, i) => (
          <div className="issue-card" key={i}>
            <div className="issue-header">
              <SeverityBadge severity={issue.severity} />
              <span className="issue-category">{issue.category}</span>
            </div>
            <p>{issue.description}</p>
            <p className="suggested-fix"><strong>Suggested fix:</strong> {issue.suggested_fix}</p>
          </div>
        ))
      ) : (
        <p className="no-issues">No outstanding issues found.</p>
      )}
    </div>
  )
}

export default function App() {
  const [requirements, setRequirements] = useState(EXAMPLE_REQUIREMENT)
  const [projectId, setProjectId] = useState(null)
  const [status, setStatus] = useState(null) // null | 'running' | 'done' | 'error'
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('requirement')
  const pollRef = useRef(null)

  const isRunning = status === 'running'
  const elapsed = useElapsedSeconds(isRunning)

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  useEffect(() => () => stopPolling(), [stopPolling])

  async function submit(e) {
    e.preventDefault()
    setError(null)
    setResult(null)
    setStatus('running')

    try {
      const res = await fetch(`${API_BASE}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements }),
      })
      if (!res.ok) throw new Error(`Server returned ${res.status}`)
      const data = await res.json()
      setProjectId(data.project_id)

      pollRef.current = setInterval(async () => {
        try {
          const pollRes = await fetch(`${API_BASE}/projects/${data.project_id}`)
          if (!pollRes.ok) throw new Error(`Server returned ${pollRes.status}`)
          const pollData = await pollRes.json()
          if (pollData.status === 'done') {
            setStatus('done')
            setResult(pollData.result)
            stopPolling()
          } else if (pollData.status === 'error') {
            setStatus('error')
            setError(pollData.error)
            stopPolling()
          }
        } catch (pollErr) {
          setStatus('error')
          setError(pollErr.message)
          stopPolling()
        }
      }, POLL_INTERVAL_MS)
    } catch (err) {
      setStatus('error')
      setError(
        err.message.includes('fetch')
          ? 'Could not reach the API. Is it running at localhost:8000?'
          : err.message
      )
    }
  }

  function reset() {
    stopPolling()
    setProjectId(null)
    setStatus(null)
    setResult(null)
    setError(null)
    setActiveTab('requirement')
  }

  const tabs = [
    { id: 'requirement', label: 'Requirement' },
    { id: 'selection', label: 'Database' },
    { id: 'schema', label: 'Schema' },
    { id: 'review', label: 'Review' },
  ]

  return (
    <div className="app">
      <header className="app-header">
        <span className="eyebrow">Agentic AI</span>
        <h1>Database Architecture Advisor</h1>
      </header>

      {status !== 'done' && (
        <section className="input-section">
          <form onSubmit={submit}>
            <label htmlFor="requirements">Describe your application's requirements</label>
            <textarea
              id="requirements"
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              rows={6}
              disabled={isRunning}
            />
            <button type="submit" disabled={isRunning || !requirements.trim()}>
              {isRunning ? 'Analyzing…' : 'Generate architecture'}
            </button>
          </form>
        </section>
      )}

      {status === 'running' && (
        <section className="status-section">
          <Pipeline activeStage={-1} />
          <p className="status-line">
            <span className="spinner" /> Running on local hardware — this typically takes
            around 15–20 minutes. Elapsed: <span className="mono">{formatElapsed(elapsed)}</span>
          </p>
        </section>
      )}

      {status === 'error' && (
        <section className="status-section error-section">
          <p>Something went wrong: {error}</p>
          <button onClick={reset}>Try again</button>
        </section>
      )}

      {status === 'done' && result && (
        <section className="results-section">
          <div className="results-header">
            <Pipeline activeStage={3} />
            <button className="secondary" onClick={reset}>New project</button>
          </div>

          <nav className="tab-bar">
            {tabs.map((t) => (
              <button
                key={t.id}
                className={activeTab === t.id ? 'tab-active' : ''}
                onClick={() => setActiveTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </nav>

          {activeTab === 'requirement' && <RequirementTab requirement={result.requirement} />}
          {activeTab === 'selection' && <SelectionTab selection={result.selection} />}
          {activeTab === 'schema' && <SchemaTab schema={result.schema} />}
          {activeTab === 'review' && (
            <ReviewTab review={result.review} cycleCount={result.cycle_count} />
          )}
        </section>
      )}
    </div>
  )
}