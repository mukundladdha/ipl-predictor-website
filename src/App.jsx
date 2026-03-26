import { useState, useEffect } from 'react'
import { ModelProvider } from './context/ModelContext'
import Nav from './components/Nav'
import Hero from './components/Hero'
import ConceptCards from './components/ConceptCards'
import MonteCarloStrip from './components/MonteCarloStrip'
import PlayoffRace from './components/PlayoffRace'
import BottomMetaStrip from './components/BottomMetaStrip'
import BumpsChart from './components/BumpsChart'
import RankProbChart from './components/RankProbChart'
import ScenarioExplorer from './components/ScenarioExplorer'
import Footer from './components/Footer'
import './index.css'

const Divider = () => (
  <div style={{ height: '0.5px', background: '#2a2d3a' }} />
)

const PreSeasonBanner = () => (
  <div style={{
    background: '#1a1d27',
    borderBottom: '0.5px solid #2a2d3a',
    padding: '9px 0',
    textAlign: 'center',
    fontSize: 12,
    color: '#FFD700',
    letterSpacing: '0.2px',
    lineHeight: 1.5,
  }}>
    IPL 2026 starts March 28. These are pre-season projections based on historical Elo ratings.
    Odds will update after each match.
  </div>
)

function App() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/data/projections.json')
      .then(r => r.json())
      .then(setData)
      .catch(() => setError('Failed to load forecast data'))
  }, [])

  if (error) {
    return (
      <div style={{
        minHeight: '100vh',
        background: '#0f1117',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#f87171',
        fontSize: 14,
      }}>
        {error}
      </div>
    )
  }

  if (!data) {
    return (
      <div style={{
        minHeight: '100vh',
        background: '#0f1117',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#888',
        fontSize: 14,
      }}>
        Loading…
      </div>
    )
  }

  return (
    <ModelProvider>
      <div style={{ background: '#0f1117', minHeight: '100vh' }}>
        <Nav lastUpdated={data.last_updated} />
        {data.pre_season && <PreSeasonBanner />}
        <Hero
          teams={data.teams}
          matchesPlayed={data.matches_played}
          matchesRemaining={data.matches_remaining}
          playoffSpots={data.playoff_spots}
        />
        <ConceptCards />
        <MonteCarloStrip />
        <PlayoffRace teams={data.teams} />
        <BottomMetaStrip
          matchesPlayed={data.matches_played}
          matchesRemaining={data.matches_remaining}
          playoffSpots={data.playoff_spots}
        />
        <Divider />
        <BumpsChart teams={data.teams} />
        <Divider />
        <RankProbChart teams={data.teams} />
        <Divider />
        <ScenarioExplorer teams={data.teams} />
        <Footer />
      </div>
    </ModelProvider>
  )
}

export default App
