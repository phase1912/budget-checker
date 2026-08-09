import { observer } from 'mobx-react-lite'
import { useEffect } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Landing } from './pages/Landing'
import { NotFound } from './pages/NotFound'
import { healthStore } from './stores/HealthStore'

const App = observer(function App() {
  useEffect(() => {
    void healthStore.check()
  }, [])

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Landing backendStatus={healthStore.status} />} />
        <Route path="not-found" element={<NotFound />} />
        <Route path="*" element={<Navigate to="/not-found" replace />} />
      </Route>
    </Routes>
  )
})

export default App
