import { useEffect, useMemo, useState } from 'react'
import {
  Bell,
  Bookmark,
  ChevronDown,
  Filter,
  Search,
  Sparkles,
} from 'lucide-react'
import './App.css'

type MarketOption = {
  label: string
  probability: number // 0-1 fraction 
  type: 'yes' | 'no' | 'outcome'
}

type Market = {
  id: string
  title: string
  description?: string
  category: string
  tags: string[]
  image?: string
  probability: number
  volume_usd: number
  settlement?: string
  cadence?: string
  options: MarketOption[]
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const formatPercent = (value: number) =>
  `${Math.round(Math.min(Math.max(value, 0), 1) * 100)}%`

const formatVolume = (value: number) =>
  value >= 1_000_000
    ? `$${(value / 1_000_000).toFixed(1)}m Vol.`
    : `$${Math.round(value / 1000)}k Vol.`

const navTopics = [
  'Trending',
  'Breaking',
  'New',
  'Politics',
  'Sports',
  'Crypto',
  'Finance',
  'Geopolitics',
  'Earnings',
  'Tech',
  'Culture',
  'World',
]

function MarketCard({ market }: { market: Market }) {
  return (
    <article className="market-card">
      <div className="market-card__header">
        <div className="market-card__thumb">
          {market.image ? (
            <img src={market.image} alt={market.title} />
          ) : (
            <div className="market-card__placeholder">{market.title[0]}</div>
          )}
        </div>
        <div className="market-card__title">
          <p className="market-card__eyebrow">{market.category}</p>
          <h3 title={market.title}>{market.title}</h3>
        </div>
        <div className="market-card__chance">
          <span className="chance-value">{formatPercent(market.probability)}</span>
          <span className="chance-label">chance</span>
        </div>
      </div>

      <div className="market-card__options">
        {market.options.map((option) => (
          <button
            key={option.label}
            className={`option-chip option-chip--${option.type}`}
          >
            <span>{option.label}</span>
            <span className="option-chip__value">{formatPercent(option.probability)}</span>
          </button>
        ))}
      </div>

      <div className="market-card__meta">
        <div className="meta-row">
          <span>{formatVolume(market.volume_usd)}</span>
          {market.cadence && <span className="pill">{market.cadence}</span>}
          {market.settlement && <span className="pill pill--muted">{market.settlement}</span>}
        </div>
        <div className="meta-row meta-actions">
          <button className="icon-btn" aria-label="Alerts">
            <Bell size={16} />
          </button>
          <button className="icon-btn" aria-label="Bookmark">
            <Bookmark size={16} />
          </button>
        </div>
      </div>
    </article>
  )
}

function EmptyCard({ index }: { index: number }) {
  return (
    <article className="market-card empty-card" aria-label={`Empty slot ${index + 1}`}>
      <div className="empty-thumb" />
      <div className="empty-lines">
        <span />
        <span />
        <span />
      </div>
    </article>
  )
}

function App() {
  const [markets, setMarkets] = useState<Market[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTag, setActiveTag] = useState('All')
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    const fetchMarkets = async () => {
      try {
        const response = await fetch(`${API_BASE}/markets`)
        if (!response.ok) throw new Error('Failed to load markets')
        const data = (await response.json()) as Market[]
        setMarkets(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unexpected error')
      } finally {
        setLoading(false)
      }
    }
    fetchMarkets()
  }, [])

  const tags = useMemo(() => {
    const set = new Set<string>(['All'])
    markets.forEach((market) => market.tags.forEach((tag) => set.add(tag)))
    return Array.from(set)
  }, [markets])

  const filteredMarkets = useMemo(() => {
    return markets.filter((market) => {
      const matchesTag =
        activeTag === 'All' ||
        market.tags.includes(activeTag) ||
        market.category === activeTag
      const matchesQuery =
        !searchQuery ||
        market.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (market.description ?? '').toLowerCase().includes(searchQuery.toLowerCase())
      return matchesTag && matchesQuery
    })
  }, [activeTag, markets, searchQuery])

  return (
    <div className="page">
      <header className="topbar">
        <div className="logo">Market</div>
        <div className="search-box">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search markets"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </header>

      <div className="nav-tabs">
        {navTopics.map((topic, idx) => (
          <button
            key={topic}
            className={`nav-tab ${activeTag === topic ? 'nav-tab--active' : ''}`}
            onClick={() => setActiveTag(topic)}
          >
            {idx === 0 && <Sparkles size={16} />}
            {topic}
          </button>
        ))}
      </div>

      <div className="filters">
        <div className="filters__left">
          <button className="icon-btn">
            <Filter size={16} />
          </button>
          <button className="icon-btn">
            <Bell size={16} />
          </button>
          <button className="icon-btn">
            <Bookmark size={16} />
          </button>
        </div>
        <div className="filters__tags">
          {tags.map((tag) => (
            <button
              key={tag}
              className={`tag-chip ${tag === activeTag ? 'tag-chip--active' : ''}`}
              onClick={() => setActiveTag(tag)}
            >
              {tag}
            </button>
          ))}
        </div>
        <button className="ghost-btn">
          <span>Filters</span>
          <ChevronDown size={16} />
        </button>
      </div>

      {loading && <div className="status">Loading markets…</div>}
      {error && <div className="status status--error">{error}</div>}

      {!loading && !error && (
        <div className="market-grid">
          {filteredMarkets.length === 0
            ? Array.from({ length: 6 }).map((_, idx) => <EmptyCard key={idx} index={idx} />)
            : filteredMarkets.map((market) => <MarketCard key={market.id} market={market} />)}
        </div>
      )}
    </div>
  )
}

export default App
