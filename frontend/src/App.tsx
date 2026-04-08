import { HARDCODED_RESPONSE } from './hardcoded-data'
import { AnswerDisplay } from './components/AnswerDisplay'
import BackgroundLayer from './components/BackgroundLayer'

function App() {
  return (
    <main className="min-h-screen bg-[#0b1020] text-white relative">
      <BackgroundLayer site="claude" />
      <div className="w-full max-w-5xl mx-auto px-6 pt-8 pb-4">
        <p className="text-sm uppercase tracking-[0.18em] text-zinc-500 mb-2">
          Veritas Demo
        </p>
        <h1 className="text-3xl md:text-4xl font-semibold text-zinc-100 leading-tight">
          Why is Claude calling the wrong tool or using incorrect parameters?
        </h1>
      </div>

      <AnswerDisplay sections={HARDCODED_RESPONSE.sections} />
    </main>
  )
}

export default App
