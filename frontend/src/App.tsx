import { observer } from 'mobx-react-lite'
import { useEffect } from 'react'
import { Landing } from './pages/Landing'
import { healthStore } from './stores/HealthStore'

const App = observer(function App() {
  useEffect(() => {
    void healthStore.check()
  }, [])

  return <Landing backendStatus={healthStore.status} />
})

export default App
