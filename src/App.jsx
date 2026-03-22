import { useState, useEffect } from 'react'
import { ModelProvider } from './context/ModelContext'
import Header from './components/Header'
import PlayoffOddsTable from './components/PlayoffOddsTable'
import BumpsChart from './components/BumpsChart'
import RankProbabilityChart from './components/RankProbabilityChart'
import ScenarioExplorer from './components/ScenarioExplorer'
import Footer from './components/Footer'
import './index.css'

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
      <div className="min-h-screen bg-[#0f1117] flex items-center justify-center text-red-400">
        {error}
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-[#0f1117] flex items-center justify-center">
        <div className="flex items-center gap-3 text-gray-400">
          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Loading forecast data…
        </div>
      </div>
    )
  }

  const divider = <div className="h-px bg-[#2a2d3a] max-w-7xl mx-auto" />

  return (
    <ModelProvider>
      <div className="min-h-screen bg-[#0f1117]">
        <Header
          lastUpdated={data.last_updated}
          seasonStart={data.season_start}
          defendingChampion={data.defending_champion}
        />

        <main>
          <PlayoffOddsTable teams={data.teams} />
          {divider}
          <BumpsChart teams={data.teams} />
          {divider}
          <RankProbabilityChart teams={data.teams} />
          {divider}
          <ScenarioExplorer teams={data.teams} />
        </main>

        <Footer />
      </div>
    </ModelProvider>
  )
}

export default App
