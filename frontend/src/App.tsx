import BackgroundLayer from './components/BackgroundLayer'
import './App.css'

function App() {
  return (
    <>
      <BackgroundLayer site="claude" />
      
      <div style={{ 
        position: 'relative', 
        zIndex: 1,
        minHeight: '100vh',
        padding: '2rem',
        color: 'white'
      }}>
        <h1>Veritas</h1>
        <p>Curated understanding system for developers</p>
      </div>
    </>
  )
}

export default App
