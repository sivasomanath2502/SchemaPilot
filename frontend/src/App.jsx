import { useState, useEffect, useRef, useCallback } from 'react'
import './App.css'

const API_BASE = 'http://localhost:8000'
const POLL_INTERVAL_MS = 5000

const EXAMPLE_REQUIREMENT =
  'Design a database for an online ticket booking system. Users should be able ' +
  'to search events, select seats and book tickets. Multiple users may try to ' +
  'book the same seat simultaneously. Double booking must never occur.'

const WORKFLOW_STAGES = [
  'Requirement',
  'Database Selection',
  'Schema',
  'Review',
  'ER Diagram',
  'Final Report',
]

const REPORT_TITLES = [
  'Requirements / Scope',
  'Scale',
  'Features & Roles',
  'Read vs Write',
  'Concurrency',
  'Entities',
  'Relationships / Cardinality',
  'Schema',
  'SQL vs NoSQL',
  'Important Queries',
  'Indexes',
  'Cache',
  'Replication',
  'Search',
  'Partitioning',
  'Sharding',
  'Pagination',
  'Transactions',
  'Failure Handling',
  'Idempotency',
  'Consistency',
  'Final Architecture',
  'Trade-offs & Review',
]

function useElapsedSeconds(isRunning) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (!isRunning) return

    setElapsed(0)
    const start = Date.now()

    const id = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000))
    }, 1000)

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
  if (!severity) return null

  return (
    <span className={`badge badge-${String(severity).toLowerCase()}`}>
      {severity}
    </span>
  )
}

function Pipeline({ activeStage = -1, completed = false }) {
  return (
    <div className="pipeline">
      {WORKFLOW_STAGES.map((stage, i) => {
        const isComplete = completed || i < activeStage
        const isActive = !completed && i === activeStage

        return (
          <div className="pipeline-stage" key={stage}>
            <div
              className={[
                'pipeline-node',
                isComplete ? 'complete' : '',
                isActive ? 'active' : '',
              ].join(' ')}
            >
              {isComplete ? '✓' : i + 1}
            </div>

            <span className="pipeline-label">{stage}</span>

            {i < WORKFLOW_STAGES.length - 1 && (
              <div
                className={`pipeline-connector ${
                  completed || i < activeStage ? 'complete' : ''
                }`}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

function StatCard({ label, value, detail }) {
  return (
    <div className="stat-card">
      <span className="stat-label">{label}</span>
      <strong className="stat-value">{value}</strong>
      {detail && <span className="stat-detail">{detail}</span>}
    </div>
  )
}

function OverviewTab({ result }) {
  const requirement = result?.requirement
  const selection = result?.selection
  const schema = result?.schema
  const review = result?.review
  const report = result?.report

  const entityCount = schema?.entities?.length || 0
  const relationshipCount = schema?.relationships?.length || 0
  const issueCount = review?.issues?.length || 0
  const criticalCount =
    review?.issues?.filter((i) => i.severity === 'critical').length || 0

  const validated = schema?.validation?.final_valid

  return (
    <div className="tab-panel">
      <div className="overview-hero">
        <div>
          <span className="eyebrow">Architecture generated</span>
          <h2>{requirement?.application || report?.application || 'Database Architecture'}</h2>
          <p>
            Six-agent workflow completed with schema validation, architectural
            review, ER diagram generation, and final report synthesis.
          </p>
        </div>

        <div className="status-pill success">
          <span className="status-dot" />
          Completed
        </div>
      </div>

      <div className="stats-grid">
        <StatCard
          label="Primary Database"
          value={selection?.primary_database || '—'}
          detail="Recommended"
        />

        <StatCard
          label="Entities"
          value={entityCount}
          detail="Schema entities"
        />

        <StatCard
          label="Relationships"
          value={relationshipCount}
          detail="Defined relationships"
        />

        <StatCard
          label="MySQL Validation"
          value={validated ? 'PASS' : 'CHECK'}
          detail={validated ? 'Schema validated' : 'Validation unresolved'}
        />

        <StatCard
          label="Review Cycles"
          value={result?.cycle_count ?? 0}
          detail="Review → improve"
        />

        <StatCard
          label="Report Sections"
          value={report?.sections ? Object.keys(report.sections).length : 23}
          detail="Architecture report"
        />
      </div>

      <div className="overview-grid">
        <section className="overview-card">
          <div className="card-heading">
            <div>
              <span className="eyebrow">Agentic workflow</span>
              <h3>Six specialized agents</h3>
            </div>
          </div>

          <div className="agent-grid">
            {WORKFLOW_STAGES.map((stage, i) => (
              <div className="agent-card" key={stage}>
                <span className="agent-number">{String(i + 1).padStart(2, '0')}</span>
                <div>
                  <strong>{stage}</strong>
                  <p>
                    {[
                      'Extracts application requirements and invariants.',
                      'Chooses the primary database and supporting components.',
                      'Designs entities, relationships, constraints and SQL.',
                      'Checks the architecture and drives revisions.',
                      'Builds the ER representation from the validated schema.',
                      'Assembles the final architecture report.',
                    ][i]}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="overview-card">
          <div className="card-heading">
            <div>
              <span className="eyebrow">Review status</span>
              <h3>{criticalCount ? 'Issues require attention' : 'Architecture reviewed'}</h3>
            </div>

            <span className={`status-pill ${criticalCount ? 'warning' : 'success'}`}>
              {criticalCount ? `${criticalCount} critical` : 'No critical issues'}
            </span>
          </div>

          <p className="overview-text">
            {review?.overall_assessment ||
              'The Review Agent did not return an overall assessment.'}
          </p>

          {issueCount > 0 && (
            <div className="mini-issue-list">
              {review.issues.slice(0, 4).map((issue, i) => (
                <div className="mini-issue" key={i}>
                  <SeverityBadge severity={issue.severity} />
                  <span>{issue.description}</span>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function RequirementTab({ requirement }) {
  if (!requirement) return null

  return (
    <div className="tab-panel">
      <div className="section-intro">
        <span className="eyebrow">Agent 01</span>
        <h2>Requirement Analysis</h2>
        <p>The application requirements extracted from the user's description.</p>
      </div>

      <dl className="kv-grid">
        <dt>Application</dt>
        <dd>{requirement.application}</dd>

        <dt>Critical invariant</dt>
        <dd className="highlight">{requirement.critical_invariant || '—'}</dd>

        <dt>Consistency</dt>
        <dd>{requirement.consistency || '—'}</dd>

        <dt>Concurrency</dt>
        <dd>{requirement.concurrency || '—'}</dd>

        <dt>Workload</dt>
        <dd>{requirement.workload || '—'}</dd>

        <dt>Read/write pattern</dt>
        <dd>{requirement.read_write_ratio || '—'}</dd>

        <dt>Search required</dt>
        <dd>{requirement.search_required ? 'Yes' : 'No'}</dd>

        <dt>Expected scale</dt>
        <dd>{requirement.expected_scale || '—'}</dd>
      </dl>

      {requirement.features?.length > 0 && (
        <>
          <h4>Features</h4>
          <div className="chip-row">
            {requirement.features.map((feature, i) => (
              <span className="chip" key={i}>
                {feature}
              </span>
            ))}
          </div>
        </>
      )}

      <h4>Entities</h4>
      <div className="chip-row">
        {(requirement.entities || []).map((entity) => (
          <span className="chip" key={entity}>
            {entity}
          </span>
        ))}
      </div>

      {requirement.actors?.length > 0 && (
        <>
          <h4>Roles & actors</h4>
          <div className="actor-list">
            {requirement.actors.map((actor, i) => (
              <div className="actor-item" key={i}>
                <strong>{actor.role}</strong>
                <span>{actor.description}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function SelectionTab({ selection }) {
  if (!selection) return null

  return (
    <div className="tab-panel">
      <div className="section-intro">
        <span className="eyebrow">Agent 02</span>
        <h2>Database Selection</h2>
        <p>Database and infrastructure decisions derived from the requirements.</p>
      </div>

      <div className="recommendation-card">
        <span className="eyebrow">Recommended primary database</span>
        <h2>{selection.primary_database}</h2>
        <p>{selection.primary_reasoning}</p>
      </div>

      {selection.supporting_components?.length > 0 && (
        <>
          <h4>Supporting components</h4>
          <table className="data-table">
            <thead>
              <tr>
                <th>Component</th>
                <th>Purpose</th>
                <th>Required</th>
              </tr>
            </thead>
            <tbody>
              {selection.supporting_components.map((component, i) => (
                <tr key={i}>
                  <td>{component.component}</td>
                  <td>{component.purpose}</td>
                  <td>{component.required ? 'Yes' : 'Optional'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {selection.alternatives?.length > 0 && (
        <>
          <h4>Alternatives considered</h4>
          <div className="decision-list">
            {selection.alternatives.map((alternative, i) => (
              <div className="decision-item" key={i}>
                <strong>{alternative.database}</strong>
                <p>{alternative.reasoning}</p>
              </div>
            ))}
          </div>
        </>
      )}

      {selection.rejected?.length > 0 && (
        <>
          <h4>Rejected options</h4>
          <div className="decision-list">
            {selection.rejected.map((rejected, i) => (
              <div className="decision-item rejected" key={i}>
                <strong>{rejected.database}</strong>
                <p>{rejected.reason}</p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function SchemaTab({ schema }) {
  if (!schema) return null

  return (
    <div className="tab-panel">
      <div className="section-intro">
        <span className="eyebrow">Agent 03</span>
        <h2>Schema & SQL</h2>
        <p>Validated relational design, constraints, indexes and important queries.</p>
      </div>

      <h4>Entities</h4>
      <div className="chip-row">
        {(schema.entities || []).map((entity) => (
          <span
            className="chip"
            key={entity.name}
            title={entity.description}
          >
            {entity.name}
          </span>
        ))}
      </div>

      <h4>Relationships</h4>
      <ul className="relationship-list">
        {(schema.relationships || []).map((relationship, i) => (
          <li key={i}>
            <span className="mono">{relationship.from}</span>
            <span className="arrow">→</span>
            <span className="mono">{relationship.to}</span>
            <span className="rel-type">{relationship.type}</span>
          </li>
        ))}
      </ul>

      {schema.constraints?.length > 0 && (
        <>
          <h4>Constraints</h4>
          <table className="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Table</th>
                <th>Columns</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {schema.constraints.map((constraint, i) => (
                <tr key={i}>
                  <td>{constraint.type}</td>
                  <td className="mono">{constraint.table}</td>
                  <td className="mono">
                    {(constraint.columns || []).join(', ')}
                  </td>
                  <td>{constraint.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      <h4>
        Transaction strategy
      </h4>
      <div className="text-card">
        {schema.transaction_strategy || '—'}
      </div>

      <h4>
        SQL DDL
        {schema.validation && (
          <span
            className={`badge ${
              schema.validation.final_valid ? 'badge-ok' : 'badge-critical'
            }`}
          >
            {schema.validation.final_valid
              ? 'validated against MySQL'
              : 'validation unresolved'}
          </span>
        )}
      </h4>

      <pre className="code-block">
        <code>{schema.sql_ddl || 'No SQL DDL returned.'}</code>
      </pre>

      {schema.indexes?.length > 0 && (
        <>
          <h4>Indexes</h4>
          <table className="data-table">
            <thead>
              <tr>
                <th>Table</th>
                <th>Columns</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {schema.indexes.map((index, i) => (
                <tr key={i}>
                  <td className="mono">{index.table}</td>
                  <td className="mono">
                    {(index.columns || []).join(', ')}
                  </td>
                  <td>{index.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {schema.important_queries?.length > 0 && (
        <>
          <h4>Important queries</h4>
          {schema.important_queries.map((query, i) => (
            <div className="query-item" key={i}>
              <span className="query-desc">{query.description}</span>
              <pre className="code-block small">
                <code>{query.sql}</code>
              </pre>
            </div>
          ))}
        </>
      )}
    </div>
  )
}

function ERDiagramTab({ diagram }) {
  if (!diagram) {
    return (
      <div className="tab-panel empty-panel">
        <h2>ER Diagram</h2>
        <p>No ER diagram was returned by the pipeline.</p>
      </div>
    )
  }

  return (
    <div className="tab-panel">
      <div className="section-intro">
        <span className="eyebrow">Agent 05</span>
        <h2>Entity Relationship Diagram</h2>
        <p>
          Generated from the validated schema. The diagram is shown as Mermaid
          source so the exact generated artifact is preserved.
        </p>
      </div>

      <div className="diagram-toolbar">
        <span className="status-pill success">
          <span className="status-dot" />
          Generated from validated DDL
        </span>

        <button
          className="secondary compact"
          onClick={() => navigator.clipboard?.writeText(diagram)}
        >
          Copy Mermaid
        </button>
      </div>

      <div className="diagram-container">
        <pre className="mermaid-block">
          <code>{diagram}</code>
        </pre>
      </div>

      <div className="diagram-note">
        <strong>Consistency rule:</strong> the ER diagram is generated from the
        final validated schema, so the entities and relationships should match
        the SQL shown in the Schema tab.
      </div>
    </div>
  )
}

function ReportTab({ report }) {
  const [selectedSection, setSelectedSection] = useState(0)

  if (!report) {
    return (
      <div className="tab-panel empty-panel">
        <h2>Architecture Report</h2>
        <p>No report was returned by the pipeline.</p>
      </div>
    )
  }

  const sections = report.sections || {}
  const sectionEntries = Object.entries(sections)

  const current =
    sectionEntries[selectedSection] || sectionEntries[0] || null

  return (
    <div className="report-layout">
      <aside className="report-sidebar">
        <div className="report-sidebar-header">
          <span className="eyebrow">Agent 06</span>
          <strong>Architecture Report</strong>
          <span>{sectionEntries.length || 23} sections</span>
        </div>

        <div className="report-section-list">
          {sectionEntries.map(([key], index) => (
            <button
              className={selectedSection === index ? 'report-section-active' : ''}
              key={key}
              onClick={() => setSelectedSection(index)}
            >
              <span>{String(index + 1).padStart(2, '0')}</span>
              <strong>
                {REPORT_TITLES[index] ||
                  key
                    .split('_')
                    .slice(1)
                    .join(' ')
                    .replace(/\b\w/g, (c) => c.toUpperCase())}
              </strong>
            </button>
          ))}
        </div>
      </aside>

      <main className="report-content">
        {current && (
          <>
            <div className="report-header">
              <div>
                <span className="eyebrow">
                  Section {String(selectedSection + 1).padStart(2, '0')}
                </span>
                <h2>
                  {REPORT_TITLES[selectedSection] ||
                    current[0]
                      .split('_')
                      .slice(1)
                      .join(' ')
                      .replace(/\b\w/g, (c) => c.toUpperCase())}
                </h2>
              </div>

              <span className="report-progress">
                {selectedSection + 1} / {sectionEntries.length}
              </span>
            </div>

            <div
              className="report-markdown"
              dangerouslySetInnerHTML={{
                __html: markdownToHtml(current[1]),
              }}
            />

            <div className="report-navigation">
              <button
                className="secondary compact"
                disabled={selectedSection === 0}
                onClick={() => setSelectedSection((value) => value - 1)}
              >
                ← Previous
              </button>

              <button
                className="secondary compact"
                disabled={selectedSection === sectionEntries.length - 1}
                onClick={() => setSelectedSection((value) => value + 1)}
              >
                Next →
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  )
}

function ReviewTab({ review, cycleCount }) {
  if (!review) return null

  const hasIssues = review.issues && review.issues.length > 0

  return (
    <div className="tab-panel">
      <div className="section-intro">
        <span className="eyebrow">Agent 04</span>
        <h2>Architecture Review</h2>
        <p>
          Review findings and the iterative improvement cycle performed by the
          workflow.
        </p>
      </div>

      <div className="review-summary">
        <div>
          <span className="eyebrow">Review cycles</span>
          <strong>{cycleCount || 0}</strong>
        </div>

        <div>
          <span className="eyebrow">Issues</span>
          <strong>{review.issues?.length || 0}</strong>
        </div>

        <div>
          <span className="eyebrow">Critical</span>
          <strong>
            {review.issues?.filter((i) => i.severity === 'critical').length || 0}
          </strong>
        </div>
      </div>

      <div
        className={`assessment-card ${
          hasIssues ? 'assessment-warn' : 'assessment-ok'
        }`}
      >
        <span className="eyebrow">Overall assessment</span>
        <p>{review.overall_assessment}</p>
      </div>

      {hasIssues ? (
        <div className="issue-list">
          {review.issues.map((issue, i) => (
            <div className="issue-card" key={i}>
              <div className="issue-header">
                <SeverityBadge severity={issue.severity} />
                <span className="issue-category">{issue.category}</span>
              </div>

              <p>{issue.description}</p>

              <p className="suggested-fix">
                <strong>Suggested fix:</strong> {issue.suggested_fix}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <div className="no-issues">
          <strong>No outstanding issues found.</strong>
          <p>
            The Review Agent did not identify any critical architectural issues
            requiring another improvement cycle.
          </p>
        </div>
      )}
    </div>
  )
}

/*
 * The backend already returns Markdown for the final report.
 * This lightweight renderer handles the Markdown produced by report_agent.py
 * without adding another frontend dependency.
 */
function markdownToHtml(markdown = '') {
  const escapeHtml = (value) =>
    value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')

  let html = escapeHtml(markdown)

  html = html.replace(
    /```sql\n([\s\S]*?)```/g,
    '<pre class="report-code"><code>$1</code></pre>'
  )

  html = html.replace(
    /```mermaid\n([\s\S]*?)```/g,
    '<pre class="report-code"><code>$1</code></pre>'
  )

  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
  html = html.replace(/^### (.*)$/gm, '<h4>$1</h4>')
  html = html.replace(/^## (.*)$/gm, '<h3>$1</h3>')
  html = html.replace(/^- (.*)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
  html = html.replace(/\n\n/g, '<br />')

  return html
}

export default function App() {
  const [requirements, setRequirements] = useState(EXAMPLE_REQUIREMENT)
  const [projectId, setProjectId] = useState(null)
  const [status, setStatus] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')

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
    setActiveTab('overview')

    try {
      const res = await fetch(`${API_BASE}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements }),
      })

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`)
      }

      const data = await res.json()
      setProjectId(data.project_id)

      pollRef.current = setInterval(async () => {
        try {
          const pollRes = await fetch(
            `${API_BASE}/projects/${data.project_id}`
          )

          if (!pollRes.ok) {
            throw new Error(`Server returned ${pollRes.status}`)
          }

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
        } catch (pollError) {
          setStatus('error')
          setError(pollError.message)
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
    setActiveTab('overview')
  }

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'requirement', label: 'Requirements' },
    { id: 'selection', label: 'Database' },
    { id: 'schema', label: 'Schema & SQL' },
    { id: 'er', label: 'ER Diagram' },
    { id: 'report', label: 'Architecture Report' },
    { id: 'review', label: 'Review' },
  ]

  return (
    <div className="app">
      <header className="app-header">
      <div>
        <h1>SchemaPilot</h1>
        <p className="app-caption">
          Agentic AI Database Architecture Advisor
        </p>
        <p className="header-subtitle">
          From natural-language requirements to a validated, reviewed database architecture.
        </p>
      </div>

      <div className="header-badge">
        <span className="status-dot" />
        Six-agent workflow
      </div>
      </header>

      {status !== 'done' && (
        <section className="input-section">
          <form onSubmit={submit}>
            <div className="input-header">
              <div>
                <span className="eyebrow">Start a new architecture</span>
                <label htmlFor="requirements">
                  Describe your application's requirements
                </label>
              </div>

              <span className="input-hint">
                Include workload, scale and critical constraints if known.
              </span>
            </div>

            <textarea
              id="requirements"
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              rows={7}
              disabled={isRunning}
              placeholder="Describe your application..."
            />

            <div className="form-footer">
              <span className="form-note">
                Requirement → Selection → Schema → Review → ER → Report
              </span>

              <button
                type="submit"
                disabled={isRunning || !requirements.trim()}
              >
                {isRunning ? 'Generating…' : 'Generate architecture'}
              </button>
            </div>
          </form>
        </section>
      )}

      {status === 'running' && (
        <section className="status-section">
          <div className="status-header">
            <div>
              <span className="eyebrow">Agentic workflow running</span>
              <h2>Building your database architecture</h2>
            </div>

            <span className="elapsed mono">
              {formatElapsed(elapsed)}
            </span>
          </div>

          <Pipeline activeStage={-1} />

          <div className="running-card">
            <div className="spinner" />
            <div>
              <strong>Agents are working on the architecture</strong>
              <p>
                Requirement analysis, database selection, schema validation,
                review, ER generation and report synthesis are being processed.
              </p>
            </div>
          </div>

          <p className="status-note">
            This workflow can take several minutes when running locally with Ollama.
          </p>
        </section>
      )}

      {status === 'error' && (
        <section className="status-section error-section">
          <div className="error-icon">!</div>
          <div>
            <span className="eyebrow">Generation failed</span>
            <h2>Something went wrong</h2>
            <p>{error}</p>
          </div>
          <button onClick={reset}>Try again</button>
        </section>
      )}

      {status === 'done' && result && (
        <section className="results-section">
          <div className="results-header">
            <div>
              <Pipeline completed />
              <div className="result-meta">
                <span className="status-pill success">
                  <span className="status-dot" />
                  Architecture complete
                </span>

                {projectId && (
                  <span className="project-id mono">
                    Project {projectId}
                  </span>
                )}
              </div>
            </div>

            <button className="secondary" onClick={reset}>
              New project
            </button>
          </div>

          <nav className="tab-bar">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                className={activeTab === tab.id ? 'tab-active' : ''}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </nav>

          {activeTab === 'overview' && <OverviewTab result={result} />}

          {activeTab === 'requirement' && (
            <RequirementTab requirement={result.requirement} />
          )}

          {activeTab === 'selection' && (
            <SelectionTab selection={result.selection} />
          )}

          {activeTab === 'schema' && (
            <SchemaTab schema={result.schema} />
          )}

          {activeTab === 'er' && (
            <ERDiagramTab diagram={result.er_diagram} />
          )}

          {activeTab === 'report' && (
            <ReportTab report={result.report} />
          )}

          {activeTab === 'review' && (
            <ReviewTab
              review={result.review}
              cycleCount={result.cycle_count}
            />
          )}
        </section>
      )}
    </div>
  )
}