import { HARDCODED_RESPONSE } from './hardcoded-data'

function App() {
  return (
    <div style={{ padding: '40px', fontFamily: 'sans-serif' }}>
      <h2>Veritas Demo</h2>

      <h3>Question: Why is Claude calling the wrong tool or using incorrect parameters?</h3>

      {HARDCODED_RESPONSE.sections.map((section) => (
        <div key={section.title} style={{ marginBottom: '30px' }}>
          <h4>{section.title}</h4>
          <p style={{ whiteSpace: 'pre-line' }}>{section.content}</p>
        </div>
      ))}
    </div>
  )
}

export default App
