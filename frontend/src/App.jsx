import { useState, useEffect, useRef } from 'react'

// Production Backend URL (Render)
const API_URL = 'https://daily-horoscope-agent-1.onrender.com'

function App() {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: '👋 Welcome to Daily Horoscope Agent!\n\nI can provide you with:\n• **Full daily horoscope** (love, career, health, money)\n• **Lucky guide** (color, number, direction, time)\n• **Trend analysis** (compare today vs yesterday)\n• **Calendar rating** (good/bad day for planning)\n\n**How to start:**\n1. Send your zodiac sign (e.g., "Leo", "Scorpio")\n2. Or send your birth date (e.g., "2004-12-12")\n\nThen ask me about love, career, money, health, lucky, trends, or calendar!' }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [userSign, setUserSign] = useState(null)
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
    <div style={{
      display: 'flex',
      height: '100vh',
      fontFamily: 'Arial, sans-serif',
      background: '#0f0f23',
      color: '#fff'
    }}>
      {/* Sidebar */}
      <div style={{
        width: '280px',
        background: '#1a1a2e',
        padding: '20px',
        overflowY: 'auto'
      }}>
        <div style={{ marginBottom: '25px' }}>
          <h1 style={{ fontSize: '24px', margin: '0 0 12px 0', color: '#9d4edd', fontWeight: 'bold' }}>
            🌟 Daily Horoscope Agent
          </h1>
          <p style={{ fontSize: '13px', color: '#a0a0a0', lineHeight: '1.5' }}>
            Your personal AI astrologer. Get daily predictions for love, career, health & money.
          </p>
        </div>

        <div style={{
          background: '#16213e',
          padding: '16px',
          borderRadius: '12px',
          marginBottom: '20px'
        }}>
          <h3 style={{ fontSize: '11px', color: '#9d4edd', margin: '0 0 12px 0', textTransform: 'uppercase', letterSpacing: '1px' }}>
            Current Mode
          </h3>
          <ul style={{ fontSize: '12px', color: '#c0c0c0', paddingLeft: '18px', lineHeight: '1.8', margin: 0 }}>
            <li>✨ Full horoscope readings</li>
            <li>🎯 Lucky color, number, direction</li>
            <li>📊 Trend analysis (vs yesterday)</li>
            <li>📅 Calendar day ratings</li>
          </ul>
        </div>

        {userSign && (
          <div style={{
            background: '#9d4edd',
            padding: '12px',
            borderRadius: '12px',
            marginBottom: '20px'
          }}>
            <p style={{ fontSize: '12px', margin: 0 }}>
              🔮 Current Sign: <strong>{userSign.charAt(0).toUpperCase() + userSign.slice(1)}</strong>
            </p>
          </div>
        )}

        <div>
          <h3 style={{ fontSize: '11px', color: '#9d4edd', margin: '0 0 12px 0', textTransform: 'uppercase', letterSpacing: '1px' }}>
            Quick Prompts
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {quickPrompts.map(prompt => (
              <button
                key={prompt}
                onClick={() => sendMessage(prompt)}
                style={{
                  padding: '6px 12px',
                  background: '#16213e',
                  border: '1px solid #0f3460',
                  borderRadius: '16px',
                  color: '#fff',
                  fontSize: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={e => e.target.style.background = '#0f3460'}
                onMouseLeave={e => e.target.style.background = '#16213e'}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        background: '#0f0f23'
      }}>
        {/* Messages */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px'
        }}>
          {messages.map((msg, i) => (
            <div key={i} style={{
              display: 'flex',
              justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              marginBottom: '16px'
            }}>
              <div style={{
                maxWidth: '75%',
                padding: '14px 18px',
                borderRadius: msg.sender === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                background: msg.sender === 'user' ? '#5a189a' : '#1a1a2e',
                color: '#fff',
                fontSize: '14px',
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap'
              }}>
                <div style={{ 
                  fontSize: '11px', 
                  color: msg.sender === 'user' ? '#c77dff' : '#9d4edd',
                  marginBottom: '4px',
                  fontWeight: 'bold'
                }}>
                  {msg.sender === 'user' ? 'You' : '🌟 Daily Horoscope Agent'}
                </div>
                {msg.text}
              </div>
            </div>
          ))}
          {isLoading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '16px' }}>
              <div style={{
                padding: '14px 18px',
                borderRadius: '18px 18px 18px 4px',
                background: '#1a1a2e',
                color: '#9d4edd',
                fontSize: '14px'
              }}>
                <div style={{ fontSize: '11px', color: '#9d4edd', marginBottom: '4px', fontWeight: 'bold' }}>
                  🌟 Daily Horoscope Agent
                </div>
                Reading the stars... 🔮
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <form onSubmit={handleSubmit} style={{
          padding: '20px',
          borderTop: '1px solid #1a1a2e',
          display: 'flex',
          gap: '12px',
          alignItems: 'center'
        }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter your sign (e.g., Leo) or birth date (2004-12-12)..."
            style={{
              flex: 1,
              padding: '14px 20px',
              borderRadius: '25px',
              border: '1px solid #1a1a2e',
              background: '#1a1a2e',
              color: '#fff',
              fontSize: '14px',
              outline: 'none'
            }}
          />
          <button
            type="submit"
            disabled={isLoading}
            style={{
              padding: '14px 28px',
              borderRadius: '25px',
              border: 'none',
              background: isLoading ? '#444' : '#9d4edd',
              color: '#fff',
              fontSize: '14px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              transition: 'all 0.2s'
            }}
          >
            {isLoading ? '...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default App
