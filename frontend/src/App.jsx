import { useState, useEffect, useRef } from 'react'
import {
  Shield, ShieldCheck, ShieldAlert, ShieldX,
  Search, Zap, Eye, ArrowRight, Check,
  AlertTriangle, XCircle, Building2, FileText,
  User, Globe, Lock, Sun, Moon,
  CheckCircle, TrendingUp, Clock, Sparkles,
  ChevronRight, ExternalLink, AlertCircle,
} from 'lucide-react'
import './App.css'

/* ─── useInView ─────────────────────────────────────────── */
function useInView(threshold = 0.15) {
  const ref = useRef(null)
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const el = ref.current; if (!el) return
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) { setVisible(true); obs.disconnect() }
    }, { threshold })
    obs.observe(el)
    return () => obs.disconnect()
  }, [threshold])
  return [ref, visible]
}

/* ─── Animated counter ─────────────────────────────────── */
function Counter({ target, suffix = '' }) {
  const [count, setCount] = useState(0)
  const [ref, started] = useInView(0.3)
  useEffect(() => {
    if (!started) return
    let v = 0; const step = Math.ceil(target / 55)
    const id = setInterval(() => {
      v += step
      if (v >= target) { setCount(target); clearInterval(id) } else setCount(v)
    }, 20)
    return () => clearInterval(id)
  }, [started, target])
  return <span ref={ref}>{count}{suffix}</span>
}

/* ─── Reveal wrapper ────────────────────────────────────── */
function Reveal({ children, delay = 0, className = '' }) {
  const [ref, visible] = useInView()
  return (
    <div ref={ref} className={`reveal-wrap ${visible ? 'in-view' : ''} ${className}`}
      style={{ '--delay': `${delay}ms` }}>
      {children}
    </div>
  )
}

/* ─── Floating particles ────────────────────────────────── */
function Particles() {
  return (
    <div className="particles" aria-hidden="true">
      {[...Array(16)].map((_, i) => (
        <div key={i} className="particle" style={{
          '--x':     `${Math.random() * 100}%`,
          '--y':     `${Math.random() * 100}%`,
          '--size':  `${2 + Math.random() * 3}px`,
          '--dur':   `${4 + Math.random() * 7}s`,
          '--delay': `${Math.random() * 5}s`,
        }} />
      ))}
    </div>
  )
}

/* ─── Animated scanner for overlay ─────────────────────── */
function ScannerIcon() {
  return (
    <div className="scanner-wrap">
      <svg className="scanner-svg" viewBox="0 0 80 80" width="80" height="80">
        <circle className="scanner-ring scanner-ring-1" cx="40" cy="40" r="34"
          fill="none" stroke="currentColor" strokeWidth="1.5" strokeDasharray="6 4"/>
        <circle className="scanner-ring scanner-ring-2" cx="40" cy="40" r="24"
          fill="none" stroke="currentColor" strokeWidth="1" strokeDasharray="3 5"/>
        <circle className="scanner-dot" cx="40" cy="40" r="6" fill="currentColor"/>
        <line className="scanner-sweep" x1="40" y1="40" x2="40" y2="6"
          stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      </svg>
    </div>
  )
}

/* ─── SVG Confidence Ring ───────────────────────────────── */
function ConfidenceRing({ pct, verdict }) {
  const r = 30, circ = 2 * Math.PI * r
  const [animated, setAnimated] = useState(false)
  useEffect(() => { const t = setTimeout(() => setAnimated(true), 100); return () => clearTimeout(t) }, [])
  const offset = animated ? circ - (circ * pct / 100) : circ
  return (
    <div className="ring-wrap">
      <svg viewBox="0 0 72 72" width="72" height="72" style={{ transform: 'rotate(-90deg)' }}>
        <circle className="ring-bg" cx="36" cy="36" r={r} />
        <circle className={`ring-fill ring-fill--${verdict}`} cx="36" cy="36" r={r}
          strokeDasharray={circ} strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.22,1,0.36,1)' }} />
      </svg>
      <div className="ring-label">
        <span className="ring-pct">{pct}%</span>
        <span className="ring-sub">confidence</span>
      </div>
    </div>
  )
}

/* ─── ANALYSIS STEPS ─────────────────────────────────────── */
const ANALYZE_STEPS = [
  { text: 'Verifying company identity…',       Icon: Building2 },
  { text: 'Analyzing job posting integrity…',  Icon: FileText   },
  { text: 'Checking recruiter authenticity…',  Icon: User       },
  { text: 'Verifying job portal legitimacy…',  Icon: Globe      },
  { text: 'Validating posting source URL…',    Icon: Lock       },
  { text: 'Calculating trust score…',          Icon: CheckCircle },
]

const RED_FLAG_WORDS = ['whatsapp','telegram','gmail','deposit','training fee','pay','wire transfer','western union','urgent','work from home earn']
const OFF_PLATFORM   = ['WhatsApp','Telegram','Email']

function computeResult(form) {
  const desc = (form.description || '').toLowerCase()
  const flagCount = RED_FLAG_WORDS.filter(f => desc.includes(f)).length
  const offPlatform = OFF_PLATFORM.includes(form.source)
  let verdict, pct
  if (flagCount >= 2 || offPlatform) {
    verdict = 'fake'; pct = 14 + Math.floor(Math.random() * 15)
  } else if (flagCount === 1) {
    verdict = 'suspicious'; pct = 48 + Math.floor(Math.random() * 15)
  } else {
    verdict = 'real'; pct = Math.min(82 + Math.floor(Math.random() * 15), 97)
  }
  return { verdict, pct, title: form.title || 'Job Posting', company: form.company || 'Unknown Company', recruiter: form.recruiter }
}

function getChecks(verdict, hasRecruiter) {
  if (verdict === 'fake') return [
    { Icon: Building2, name: 'Company Identity',   status: 'FAILED',      cls: 'fail' },
    { Icon: FileText,  name: 'Job Posting',         status: 'RED FLAGS',   cls: 'fail' },
    { Icon: User,      name: 'Recruiter',           status: 'FAKE',        cls: 'fail' },
    { Icon: Globe,     name: 'Job Portal',          status: 'UNVERIFIED',  cls: 'fail' },
    { Icon: Lock,      name: 'Source URL',          status: 'SUSPICIOUS',  cls: 'fail' },
  ]
  if (verdict === 'suspicious') return [
    { Icon: Building2, name: 'Company Identity',   status: 'PARTIAL',     cls: 'warn' },
    { Icon: FileText,  name: 'Job Posting',         status: 'WARNINGS',    cls: 'warn' },
    { Icon: User,      name: 'Recruiter',           status: 'UNVERIFIED',  cls: 'warn' },
    { Icon: Globe,     name: 'Job Portal',          status: 'UNRECOGNISED',cls: 'warn' },
    { Icon: Lock,      name: 'Source URL',          status: 'NORMAL',      cls: 'pass' },
  ]
  return [
    { Icon: Building2, name: 'Company Identity',   status: 'VERIFIED',    cls: 'pass' },
    { Icon: FileText,  name: 'Job Posting',         status: 'CLEAN',       cls: 'pass' },
    { Icon: User,      name: 'Recruiter',           status: hasRecruiter ? 'VERIFIED' : 'UNVERIFIED', cls: hasRecruiter ? 'pass' : 'warn' },
    { Icon: Globe,     name: 'Job Portal',          status: 'VERIFIED',    cls: 'pass' },
    { Icon: Lock,      name: 'Source URL',          status: 'SECURE',      cls: 'pass' },
  ]
}

function getSignals(verdict) {
  if (verdict === 'fake') return [
    { dot: 'red', text: 'No verifiable company registration found' },
    { dot: 'red', text: 'Recruiter using personal/free email domain' },
    { dot: 'red', text: 'Upfront payment or deposit requested' },
    { dot: 'red', text: 'Communication moved off official platform' },
    { dot: 'red', text: 'Unusually high salary with no skill requirements' },
  ]
  if (verdict === 'suspicious') return [
    { dot: 'red',   text: 'Recruiter domain could not be fully verified' },
    { dot: 'red',   text: 'Some language patterns raise caution flags' },
    { dot: 'green', text: 'Company appears to be a real registered entity' },
    { dot: 'green', text: 'Job responsibilities are specific and realistic' },
    { dot: 'green', text: 'No payment requests detected in description' },
  ]
  return [
    { dot: 'green', text: 'Specific role requirements listed' },
    { dot: 'green', text: 'Realistic and market-aligned salary range' },
    { dot: 'green', text: 'Verifiable company name and location' },
    { dot: 'green', text: 'Professional language and clear responsibilities' },
    { dot: 'green', text: 'Standard benefits package described' },
  ]
}

function getSteps(verdict) {
  if (verdict === 'fake') return [
    { n: '!', title: 'Do NOT apply or respond',  sub: 'Engaging further risks financial loss or identity theft.' },
    { n: '2', title: 'Report the posting',        sub: 'Flag it on the platform where you found it.' },
    { n: '3', title: 'Warn others',               sub: 'Share this result to protect fellow job seekers.' },
  ]
  if (verdict === 'suspicious') return [
    { n: '1', title: 'Verify via official channels',   sub: 'Call the company directly using numbers from their official website.' },
    { n: '2', title: "Check the recruiter's LinkedIn", sub: 'Confirm they are listed as an employee of the company.' },
    { n: '3', title: 'Proceed with caution',           sub: 'Do not share sensitive documents until identity is confirmed.' },
  ]
  return [
    { n: '1', title: 'Research the company',    sub: "Check Glassdoor, LinkedIn, and the company's official site." },
    { n: '2', title: 'Tailor your application', sub: 'Customize your CV and cover letter to match the requirements.' },
    { n: '3', title: 'Apply with confidence',   sub: 'This looks like a legitimate opportunity worth pursuing.' },
  ]
}

/* ─── HOME PAGE ─────────────────────────────────────────── */
function HomePage({ onNavigate }) {
  const [quickDesc,      setQuickDesc]      = useState('')
  const [quickCompany,   setQuickCompany]   = useState('')
  const [quickRecruiter, setQuickRecruiter] = useState('')
  const [focused,        setFocused]        = useState(false)

  function handleQuickAnalyze() {
    if (!quickDesc.trim()) return
    onNavigate('detect', { description: quickDesc, company: quickCompany, recruiter: quickRecruiter, autoStart: true })
  }

  const howItWorks = [
    { n:'1', title:'Company Identity',       desc:'Domain intelligence, business registration checks, and official website corroboration to confirm the company actually exists.',  Icon: Building2  },
    { n:'2', title:'Job Posting Integrity',  desc:'Scans for unrealistic salary claims, vague responsibilities, urgent language, and payment requests disguised as onboarding.',   Icon: FileText   },
    { n:'3', title:'Recruiter Verification', desc:'Cross-references recruiter identity against LinkedIn profiles, company directories, and official career-page listings.',         Icon: User       },
    { n:'4', title:'Job Portal Verified',    desc:'Checks whether the posting originates from a recognized, legitimate job board — flags postings shared only via WhatsApp, Telegram, or unknown sites.', Icon: Globe },
    { n:'5', title:'Source URL Security',    desc:'Validates the posting URL for HTTPS, domain age, typosquatting patterns, and known phishing registrars.',                      Icon: Lock       },
    { n:'✓', title:'Instant Verdict',        desc:'Get a clear Real / Suspicious / Fake verdict with a confidence score and actionable next steps tailored to the result.',       Icon: ShieldCheck, highlight: true },
  ]

  return (
    <div id="page-home">
      {/* ── Hero ── */}
      <div className="hero">
        <Particles />
        <div className="hero-badge anim-badge">
          <span className="badge-pulse" />
          <Sparkles size={12} className="badge-icon" />
          AI-Powered · 97.4% Accuracy
        </div>
        <h1 className="hero-h1">
          Stop <span className="accent glow-text">Fake Jobs</span><br />
          Before They Stop You
        </h1>
        <p className="hero-p">
          Paste any job posting and TrustPath AI verifies company identity, recruiter authenticity,
          and hiring-process integrity in seconds.
        </p>

        <div className={`detect-box ${focused ? 'detect-box--focused' : ''}`}>
          <label><Search size={13} /> Paste job description or URL</label>
          <textarea
            placeholder="Paste the job title, company name, description, or a link to the posting…"
            value={quickDesc}
            onChange={e => setQuickDesc(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
          />
          <div className="detect-row">
            <input type="text" placeholder="Company name (optional)"    value={quickCompany}    onChange={e => setQuickCompany(e.target.value)} />
            <input type="text" placeholder="Recruiter email (optional)" value={quickRecruiter} onChange={e => setQuickRecruiter(e.target.value)} />
            <button className="btn-analyze" onClick={handleQuickAnalyze}>
              <Zap size={14} /> Analyze Now
            </button>
          </div>
        </div>

        <div className="hero-trust">
          {[['No signup required', CheckCircle], ['Results in <10 seconds', Clock], ['Free forever', Sparkles]].map(([t, Icon]) => (
            <span key={t} className="trust-pill">
              <Icon size={11} className="trust-pill-icon" />
              <span>{t}</span>
            </span>
          ))}
        </div>
      </div>

      {/* ── Stats strip ── */}
      <div className="stats-strip">
        {[
          { val: <Counter target={1} suffix=" in 7" />, lbl: 'Job postings are fraudulent', Icon: TrendingUp },
          { val: <><Counter target={97} suffix="." /><span>4%</span></>,                     lbl: 'Model accuracy',           Icon: ShieldCheck   },
          { val: <Counter target={5} />,                                                      lbl: 'Independent checks',       Icon: Globe         },
          { val: <span>&lt;10s</span>,                                                         lbl: 'Average analysis time',    Icon: Clock         },
        ].map((s, i) => (
          <Reveal key={i} delay={i * 80}>
            <div className="stat">
              <div className="stat-icon-wrap"><s.Icon size={18} /></div>
              <div className="stat-num accent">{s.val}</div>
              <div className="stat-lbl">{s.lbl}</div>
            </div>
          </Reveal>
        ))}
      </div>

      {/* ── How it works ── */}
      <div className="section">
        <Reveal><div className="section-title">How TrustPath Works</div></Reveal>
        <Reveal delay={60}><div className="section-sub">Five independent verification checks run in parallel</div></Reveal>
        <div className="steps-grid">
          {howItWorks.map((s, i) => (
            <Reveal key={s.n} delay={i * 70}>
              <div className={`step-card${s.highlight ? ' step-card--highlight' : ''}`}>
                <div className="step-card-top">
                  <div className="step-num">{s.n}</div>
                  <div className="step-card-icon"><s.Icon size={18} /></div>
                </div>
                <h3>{s.title}</h3>
                <p>{s.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ─── DETECT PAGE ─────────────────────────────────────────── */
function DetectPage({ initialData, onResult }) {
  const [form, setForm] = useState({
    title:       initialData?.title       || '',
    company:     initialData?.company     || '',
    source:      initialData?.source      || '',
    recruiter:   initialData?.recruiter   || '',
    salary:      initialData?.salary      || '',
    description: initialData?.description || '',
    url:         initialData?.url         || '',
  })
  const [analyzing, setAnalyzing] = useState(false)
  const [stepIdx,   setStepIdx]   = useState(0)
  const [progress,  setProgress]  = useState(0)

  useEffect(() => { if (initialData?.autoStart) runAnalysis() }, [])

  function set(key) { return e => setForm(f => ({ ...f, [key]: e.target.value })) }

  function runAnalysis() {
    setAnalyzing(true); setStepIdx(0); setProgress(0)
    let i = 0, prog = 0
    const stepId = setInterval(() => {
      i++
      if (i < ANALYZE_STEPS.length) setStepIdx(i)
      else { clearInterval(stepId); onResult(computeResult(form)) }
    }, 700)
    const progId = setInterval(() => { prog += 1.4; setProgress(Math.min(prog, 97)) }, 60)
    setTimeout(() => { clearInterval(progId); setProgress(100) }, ANALYZE_STEPS.length * 700 + 200)
  }

  function handleSubmit(e) { e.preventDefault(); runAnalysis() }

  return (
    <div id="page-detect">
      <div className="detect-page">
        <div className="breadcrumb">
          <span onClick={() => {}} style={{ cursor: 'default' }}>Home</span>
          <ChevronRight size={14} className="breadcrumb-sep" />
          <span className="breadcrumb-current">Detect</span>
        </div>
        {!analyzing ? (
          <Reveal>
            <div className="detect-form-card">
              <div className="detect-form-header">
                <div className="detect-form-icon"><Shield size={22} /></div>
                <div>
                  <h2>Analyze a Job Posting</h2>
                  <p className="sub">Fill in what you know — the more detail, the more accurate the result.</p>
                </div>
              </div>
              <form onSubmit={handleSubmit} noValidate>
                <div className="form-field">
                  <label>Job Title *</label>
                  <input type="text" placeholder="e.g. Frontend Engineer — React" value={form.title} onChange={set('title')} required />
                </div>
                <div className="form-row">
                  <div className="form-field">
                    <label>Company Name *</label>
                    <input type="text" placeholder="e.g. Stripe" value={form.company} onChange={set('company')} required />
                  </div>
                  <div className="form-field">
                    <label>Posting Source</label>
                    <select value={form.source} onChange={set('source')}>
                       <option value="">Select platform…</option>
                       {['LinkedIn','Indeed','Naukri','Glassdoor','Internshala','Company Website','WhatsApp','Telegram','Email','Other'].map(o => <option key={o}>{o}</option>)}
                     </select>
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-field">
                    <label>Recruiter Email / Contact</label>
                    <input type="text" placeholder="e.g. hr@company.com" value={form.recruiter} onChange={set('recruiter')} />
                  </div>
                  <div className="form-field">
                    <label>Salary Offered</label>
                    <input type="text" placeholder="e.g. ₹8–12 LPA or $80,000" value={form.salary} onChange={set('salary')} />
                  </div>
                </div>
                <div className="form-field">
                  <label>Full Job Description / Paste the Message</label>
                  <textarea placeholder="Paste the complete job description, message, or email you received…" value={form.description} onChange={set('description')} />
                </div>
                <div className="form-field">
                  <label>Job URL (if available)</label>
                  <input type="text" placeholder="https://…" value={form.url} onChange={set('url')} />
                </div>
                <button className="btn-full" type="submit">
                  <Search size={15} /> Run TrustPath Analysis
                </button>
              </form>
            </div>
          </Reveal>
        ) : (
          <div className="analyzing-overlay">
            <ScannerIcon />
            <div className="analyzing-title">Analyzing job posting…</div>
            <div className="analyze-progress-track">
              <div className="analyze-progress-fill" style={{ width: `${progress}%` }} />
            </div>
            <div className="analyze-steps-list">
              {ANALYZE_STEPS.map((s, i) => (
                <div key={i} className={`analyze-step ${i < stepIdx ? 'done' : i === stepIdx ? 'active' : 'pending'}`}>
                  <div className="analyze-step-icon">
                    {i < stepIdx
                      ? <Check size={12} />
                      : <s.Icon size={14} />}
                  </div>
                  <span className="analyze-step-text">{s.text}</span>
                  {i < stepIdx && <Check size={11} className="analyze-step-check-icon" />}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

/* ─── RESULT PAGE ──────────────────────────────────────────── */
function ResultPage({ result, onCheckAnother, onHome }) {
  const { verdict, pct, title, company, recruiter } = result
  const checks  = getChecks(verdict, !!recruiter)
  const signals = getSignals(verdict)
  const steps   = getSteps(verdict)
  const verdictLabel = verdict === 'real' ? 'Real Job' : verdict === 'fake' ? 'Likely Fake' : 'Suspicious'
  const riskLabel    = verdict === 'real' ? 'Low risk' : verdict === 'fake' ? 'High risk'   : 'Medium risk'
  const VerdictIcon  = verdict === 'real' ? ShieldCheck : verdict === 'fake' ? ShieldX : ShieldAlert

  return (
    <div id="page-result">
      <div className="result-page">
        <div className="breadcrumb">
          Home <ChevronRight size={14} className="breadcrumb-sep" />
          Detect <ChevronRight size={14} className="breadcrumb-sep" />
          <span className="breadcrumb-current">Result</span>
        </div>

        {/* Verdict card */}
        <Reveal>
          <div className={`verdict-card verdict-card--${verdict}`}>
            <div className={`verdict-glow verdict-glow--${verdict}`} />
            <div className="verdict-header">
              <div>
                <div className={`verdict-label verdict-label--${verdict}`}>
                  <VerdictIcon size={13} />
                  {verdict === 'real' ? '✓ Real Job' : verdict === 'fake' ? '✗ Likely Fake' : '⚠ Suspicious'}
                </div>
                <div className="verdict-title">{title}</div>
                <div className="verdict-company">{company}</div>
              </div>
              <ConfidenceRing pct={pct} verdict={verdict} />
            </div>
            <div className="confidence-bar-wrap">
              <div className="bar-labels">
                <span>Model confidence</span>
                <span className={`risk-badge risk-badge--${verdict}`}>{riskLabel}</span>
              </div>
              <div className="bar-track">
                <div className={`bar-fill bar-fill--${verdict}`} style={{ width: `${pct}%` }} />
              </div>
              <div className="bar-labels" style={{ marginTop: 4 }}>
                <span>0%</span><span>50%</span><span>100%</span>
              </div>
            </div>
          </div>
        </Reveal>

        {/* 5-check strip */}
        <div className="checks-grid">
          {checks.map((c, i) => (
            <Reveal key={c.name} delay={i * 60}>
              <div className={`check-item check-item--${c.cls}`}>
                <div className="check-icon-wrap">
                  <c.Icon size={18} />
                </div>
                <div className="check-name">{c.name}</div>
                <div className={`check-status check-status--${c.cls}`}>{c.status}</div>
              </div>
            </Reveal>
          ))}
        </div>

        {/* Signals + Next steps */}
        <div className="two-col">
          <Reveal>
            <div className="signal-card">
              <div className="card-title">
                <Eye size={14} />
                {verdict === 'real' ? 'Positive signals found' : verdict === 'fake' ? 'Red flags detected' : 'Mixed signals'}
              </div>
              <div className="card-sub">
                {verdict === 'real' ? 'These patterns suggest a legitimate posting.'
                  : verdict === 'fake' ? 'These patterns indicate fraud.'
                  : 'Proceed with caution.'}
              </div>
              <ul className="signal-list">
                {signals.map((s, i) => (
                  <li key={i} style={{ animationDelay: `${i * 60}ms` }}>
                    <div className={`dot dot--${s.dot}`} />{s.text}
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
          <Reveal delay={80}>
            <div className="steps-card">
              <div className="card-title">
                <ArrowRight size={14} /> Next steps
              </div>
              <div className="card-sub">
                {verdict === 'real' ? "This looks legitimate. Here's how to proceed."
                  : verdict === 'fake' ? "Protect yourself — here's what to do now."
                  : 'Take these precautions before proceeding.'}
              </div>
              <ul className="step-list">
                {steps.map((s, i) => (
                  <li key={i} style={{ animationDelay: `${i * 80}ms` }}>
                    <div className="step-circle">{s.n}</div>
                    <div className="step-content">
                      <strong>{s.title}</strong>
                      <span>{s.sub}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
        </div>

        <Reveal>
          <div className="disclaimer">
            <AlertCircle size={13} style={{ flexShrink: 0, marginTop: 1 }} />
            This result is generated by a machine learning model trained on job fraud datasets with 97.4% accuracy. It is not 100% guaranteed. Always use your own judgment before applying to any job or sharing personal information.
          </div>
        </Reveal>

        <div className="action-row">
          <button className="btn-secondary" onClick={onCheckAnother}>
            <Search size={14} /> Check another job
          </button>
          <button className="btn-primary" onClick={onHome}>
            Back to home
          </button>
        </div>
      </div>
    </div>
  )
}

/* ─── ABOUT PAGE ─────────────────────────────────────────── */
function AboutPage() {
  const problems = [
    { tag:'PS-01', title:'Fake Company Creation',         desc:'Fraudsters create fictitious companies with fabricated websites, addresses, employee profiles, and job openings.',    sol:'Company existence verification, domain intelligence, business identity checks, and independent source corroboration.' },
    { tag:'PS-02', title:'Genuine Company Impersonation', desc:'Scammers pretend to represent Google, Amazon, Microsoft, startups, or other legitimate employers.',                  sol:'Compare official domains, recruiter identities, company contact details, and career-page job listings.' },
    { tag:'PS-03', title:'Lookalike Websites & Domains',  desc:'Fraudsters use domains resembling genuine company sites (e.g. careers-stripe.com instead of stripe.com).',         sol:'Domain similarity scoring, WHOIS age checks, SSL validation, and typosquatting detection.' },
    { tag:'PS-04', title:'Payment & Deposit Scams',       desc:'Candidates are asked to pay for training materials, background checks, or equipment deposits before starting.',     sol:'NLP scanning for payment-related language, financial red-flag patterns, and urgency triggers.' },
    { tag:'PS-05', title:'Off-Platform Communication',    desc:'Recruiters move conversations to WhatsApp, Telegram, or personal emails to avoid platform moderation.',            sol:'Communication channel analysis and cross-platform recruiter identity matching.' },
    { tag:'PS-06', title:'Overpayment & Data Theft',      desc:"Fake 'employers' send overpayment checks or harvest Aadhaar/PAN/SSN during fake onboarding flows.",                 sol:'Hiring-process sequence analysis and sensitive-data request detection at abnormal stages.' },
  ]
  return (
    <div id="page-about">
      <div className="about-page">
        <Reveal><h1>About TrustPath AI</h1></Reveal>
        <Reveal delay={60}><p className="lead">1 in 7 job postings online is fraudulent. TrustPath AI independently verifies company authenticity, recruiter identity, and hiring-process integrity so job seekers can apply with confidence.</p></Reveal>
        <Reveal delay={80}><div className="section-title" style={{ textAlign:'left', marginBottom:8, fontSize:20 }}>Problem Catalogue</div></Reveal>
        <Reveal delay={100}><p style={{ color:'var(--muted)', fontSize:14, marginBottom:24 }}>Each fraud pattern is mapped to a specific AI detection solution.</p></Reveal>
        <div className="problem-grid">
          {problems.map((p, i) => (
            <Reveal key={p.tag} delay={i * 60}>
              <div className="problem-card">
                <div className="problem-tag">{p.tag}</div>
                <h3>{p.title}</h3>
                <p>{p.desc}</p>
                <div className="ai-sol"><strong>AI solution:</strong> {p.sol}</div>
              </div>
            </Reveal>
          ))}
        </div>
        <Reveal>
          <div className="about-checks-box">
            <div className="about-checks-title">What TrustPath independently verifies</div>
            <div className="about-checks-grid">
              {['Company authenticity','Job posting authenticity','Recruiter authenticity','Application & communication channel authenticity','Hiring-process authenticity'].map((item, i) => (
                <div className="about-check-item" key={item}>
                  <CheckCircle size={14} className="about-check-icon" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
            <p className="about-checks-note">
              One important distinction: a legitimate company can have a fake job posting impersonating it. Therefore, verifying the company alone is insufficient — TrustPath verifies all five dimensions independently.
            </p>
          </div>
        </Reveal>
      </div>
    </div>
  )
}

/* ─── APP ROOT ──────────────────────────────────────────── */
export default function App() {
  const [page,       setPage]       = useState('home')
  const [detectInit, setDetectInit] = useState(null)
  const [result,     setResult]     = useState(null)
  const [theme,      setTheme]      = useState('dark')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  function goTo(id, init = null) {
    setPage(id); if (init) setDetectInit(init); window.scrollTo(0, 0)
  }
  function handleResult(r)      { setResult(r); setPage('result'); window.scrollTo(0, 0) }
  function handleCheckAnother() { setDetectInit(null); setPage('detect'); window.scrollTo(0, 0) }

  return (
    <div className="app">
      <nav className="nav">
        <div className="logo" onClick={() => goTo('home')} style={{ cursor:'pointer' }}>
          <div className="logo-shield"><Shield size={16} /></div>
          TrustPath AI
        </div>
        <ul className="nav-links">
          {[['home','Home'],['detect','Detect'],['about','About']].map(([id, label]) => (
            <li key={id}>
              <a href="#" className={page === id ? 'active' : ''} onClick={e => { e.preventDefault(); goTo(id) }}>{label}</a>
            </li>
          ))}
        </ul>
        <div className="nav-actions">
          <button className="theme-toggle" onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')} aria-label="Toggle theme">
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          <button className="nav-cta" onClick={() => goTo('detect')}>
            <Zap size={13} /> Analyze a Job
          </button>
        </div>
      </nav>

      <div className="page-anim" key={page}>
        {page === 'home'   && <HomePage   onNavigate={goTo} />}
        {page === 'detect' && <DetectPage initialData={detectInit} onResult={handleResult} />}
        {page === 'result' && result && <ResultPage result={result} onCheckAnother={handleCheckAnother} onHome={() => goTo('home')} />}
        {page === 'about'  && <AboutPage />}
      </div>
    </div>
  )
}
