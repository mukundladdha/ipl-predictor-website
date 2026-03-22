import { createContext, useContext, useState } from 'react'

const ModelContext = createContext(null)

export function ModelProvider({ children }) {
  const [activeModel, setActiveModel] = useState('elo') // 'elo' | 'form'
  const [scenarioOverrides, setScenarioOverrides] = useState({}) // { [teamShort]: bonusPts }

  return (
    <ModelContext.Provider value={{ activeModel, setActiveModel, scenarioOverrides, setScenarioOverrides }}>
      {children}
    </ModelContext.Provider>
  )
}

export function useModel() {
  const ctx = useContext(ModelContext)
  if (!ctx) throw new Error('useModel must be used inside ModelProvider')
  return ctx
}
