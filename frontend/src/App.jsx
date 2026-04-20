import { useState, useEffect, useRef } from 'react'
import './App.css'

// Production Backend URL (Render)
const API_URL = 'https://daily-horoscope-agent-backend.onrender.com'

function App() {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: '👋 Welcome to Daily Horoscope Agent!\n\nI can provide you with:\n• **Full daily horoscope** (love, career, health, money)\n• **Lucky guide** (color, number, direction, time)\n• **Trend analysis** (compare today vs yesterday)\n• **Calendar rating** (good/bad day for planning)\n\n**How to start:**\n1. Send your zodiac sign (e.g., "Leo", "Scorpio")\n2. Or send your birth date (e.g., "2004-12-12")\n\nThen ask me about love, career, money, health, lucky, trends, or calendar!' }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [userSign, setUserSign] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (text) => {
    if (!text.trim()) return
    
    setMessages(prev => [...prev, { sender: 'user', text }])
    setInput('')
    setIsLoading(true)
    setSidebarOpen(false)

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      })
      const data = await res.json()
      setMessages(prev => [...prev, { sender: 'bot', text: data.reply }])
      if (data.sign) setUserSign(data.sign)
    } catch (err) {
      setMessages(prev => [...prev, { sender: 'bot', text: '⚠️ Error connecting to backend. Please try again later.' }])
    }
    setIsLoading(false)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage(input)
  }

  const quickPrompts = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces', 'love', 'career', 'money', 'health', 'lucky', 'trends', 'calendar']

  return (
    <div className="app-container">
      <button className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
        {sidebarOpen ? '✕' : '☰'}
      </button>

      <div className={`sidebar-overlay ${sidebarOpen ? 'open' : ''}`} onClick={() => setSidebarOpen(false)} />

      <div className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div>
          <h1>🌟 Daily Horoscope Agent</h1>
          <p>Your personal AI astrologer. Get daily predictions for love, career, health & money.</p>
        </div>

        <div className="current-sign">
          <h3 style={{ fontSize: '11px', color: '#9d4edd', margin: '0 0 8px 0', textTransform: 'uppercase', letterSpacing: '1px' }}>Current Mode</h3>
          <ul style={{ fontSize: '12px', color: '#c0c0c0', paddingLeft: '18px', lineHeight: '1.8', margin: 0 }}>
            <li>✨ Full horoscope readings</li>
            <li>🎯 Lucky color, number, direction</li>
            <li>📊 Trend analysis (vs yesterday)</li>
            <li>📅 Calendar day ratings</li>
          </ul>
        </div>

        {userSign && (
          <div style={{ background: '#9d4edd', padding: '12px', borderRadius: '12px' }}>
            <p style={{ fontSize: '12px', margin: 0 }}>
              🔮 Current Sign: <strong>{userSign.charAt(0).toUpperCase() + userSign.slice(1)}</strong>
            </p>
          </div>
        )}

        <div className="quick-prompts">
          <h3>Quick Prompts</h3>
          <div className="prompt-buttons">
            {quickPrompts.map(prompt => (
              <button key={prompt} onClick={() => sendMessage(prompt)} className="prompt-btn">
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="chat-area">
        <div className="messages-container">
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.sender}`}>
              <div className={`message-bubble ${msg.sender}`}>
                <div className={`message-sender ${msg.sender}`}>
                  {msg.sender === 'user' ? 'You' : '🌟 Daily Horoscope Agent'}
                </div>
                {msg.text}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="loading-message">
              <div className="loading-bubble">
                <div className="message-sender bot">🌟 Daily Horoscope Agent</div>
                Reading the stars... 🔮
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="input-form">
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Enter your sign or birth date..." className="input-field" />
          <button type="submit" disabled={isLoading} className="send-btn">
            {isLoading ? '...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default App
