import { createContext, useContext, useState } from 'react'

const ModelContext = createContext(null)

export function ModelProvider({ children }) {
  const [model, setModel] = useState('elo') // 'elo' | 'form'

  return (
    <ModelContext.Provider value={{ model, setModel }}>
      {children}
    </ModelContext.Provider>
  )
}

export function useModel() {
  const ctx = useContext(ModelContext)
  if (!ctx) throw new Error('useModel must be used inside ModelProvider')
  return ctx
}
