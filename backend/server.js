import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import axios from 'axios';
import { connectDB, getHoroscopesCollection, getChatsCollection, getUsersCollection } from './db.js';

const app = express();
dotenv.config();
const PORT = process.env.PORT || 8000;

// Connect to MongoDB
await connectDB();

app.use(cors({ origin: process.env.FRONTEND_URL || 'http://localhost:5173' }));
app.use(express.json());

// Store user sessions (in-memory for quick access, also saved to DB)
const sessions = new Map();

// RAG Server Integration
const RAG_SERVER_URL = process.env.RAG_SERVER_URL || 'http://localhost:5001';

async function askRAGServer(question, sign) {
  try {
    const response = await axios.post(`${RAG_SERVER_URL}/api/rag/question`, {
      question,
      sign
    });
    return response.data.answer;
  } catch (error) {
    console.error('RAG Server error:', error.message);
    return null;
  }
}

// Helper to save chat to MongoDB
async function saveChat(sessionId, message, reply, sign) {
  try {
    const chats = getChatsCollection();
    await chats.insertOne({
      sessionId,
      message,
      reply,
      sign,
      timestamp: new Date()
    });
  } catch (error) {
    console.error('Error saving chat:', error);
  }
}

// Helper to save horoscope to MongoDB
async function saveHoroscope(sign, data, userId = 'anonymous') {
  try {
    const horoscopes = getHoroscopesCollection();
    await horoscopes.insertOne({
      userId,
      sign,
      ...data,
      createdAt: new Date()
    });
  } catch (error) {
    console.error('Error saving horoscope:', error);
  }
}

// Helper to get sign from birth date
function getSignFromDate(dateStr) {
  const date = new Date(dateStr);
  const month = date.getMonth() + 1;
  const day = date.getDate();
  
  if ((month === 3 && day >= 21) || (month === 4 && day <= 19)) return 'aries';
  if ((month === 4 && day >= 20) || (month === 5 && day <= 20)) return 'taurus';
  if ((month === 5 && day >= 21) || (month === 6 && day <= 20)) return 'gemini';
  if ((month === 6 && day >= 21) || (month === 7 && day <= 22)) return 'cancer';
  if ((month === 7 && day >= 23) || (month === 8 && day <= 22)) return 'leo';
  if ((month === 8 && day >= 23) || (month === 9 && day <= 22)) return 'virgo';
  if ((month === 9 && day >= 23) || (month === 10 && day <= 22)) return 'libra';
  if ((month === 10 && day >= 23) || (month === 11 && day <= 21)) return 'scorpio';
  if ((month === 11 && day >= 22) || (month === 12 && day <= 21)) return 'sagittarius';
  if ((month === 12 && day >= 22) || (month === 1 && day <= 19)) return 'capricorn';
  if ((month === 1 && day >= 20) || (month === 2 && day <= 18)) return 'aquarius';
  if ((month === 2 && day >= 19) || (month === 3 && day <= 20)) return 'pisces';
  return null;
}

// Full horoscope data with all categories
const horoscopeData = {
  aries: {
    overview: 'Intensity is high today. Depth helps you, obsession does not.',
    love: 'Deep feelings surface fast. Honest but calm communication is essential.',
    career: 'Shared resources, strategy, and hidden details deserve attention.',
    money: 'Review dues, taxes, loans, or joint commitments carefully.',
    health: 'Strong energy needs a clean outlet. Avoid emotional overload.',
    lucky: { color: 'Red', number: 9, direction: 'East', time: '6:00 AM - 8:00 AM', energy: '8/10', tag: 'Action' }
  },
  taurus: {
    overview: 'Patience pays off today. Steady progress over quick wins.',
    love: 'Sensual connections deepen. Quality time matters more than quantity.',
    career: 'Practical solutions shine. Your reliability is noticed.',
    money: 'Stable income streams. Good day for budget planning.',
    health: 'Focus on neck and throat. Gentle stretches help.',
    lucky: { color: 'Green', number: 6, direction: 'South', time: '2:00 PM - 4:00 PM', energy: '7/10', tag: 'Steady' }
  },
  gemini: {
    overview: 'Communication flows easily. Share ideas boldly.',
    love: 'Witty conversations spark romance. Keep it light and fun.',
    career: 'Networking opportunities abound. Connect with key people.',
    money: 'Multiple small gains possible. Avoid major investments today.',
    health: 'Mental stimulation needed. Read, learn, or socialize.',
    lucky: { color: 'Yellow', number: 5, direction: 'West', time: '10:00 AM - 12:00 PM', energy: '9/10', tag: 'Social' }
  },
  cancer: {
    overview: 'Home and family take priority. Nurture your foundations.',
    love: 'Emotional intimacy grows. Create safe spaces for vulnerability.',
    career: 'Collaborative projects succeed. Support your team.',
    money: 'Home-related expenses may arise. Plan for comfort, not luxury.',
    health: 'Stomach and digestion need care. Eat mindfully.',
    lucky: { color: 'Silver', number: 2, direction: 'North', time: '8:00 PM - 10:00 PM', energy: '6/10', tag: 'Nurture' }
  },
  leo: {
    overview: 'Your charisma is magnetic today. Lead with confidence.',
    love: 'Passionate energy surrounds you. Express your heart fully.',
    career: 'Recognition comes your way. Showcase your talents.',
    money: 'Generosity returns to you. Give freely, receive abundantly.',
    health: 'Heart and spine need attention. Stand tall and proud.',
    lucky: { color: 'Gold', number: 1, direction: 'East', time: '12:00 PM - 2:00 PM', energy: '10/10', tag: 'Shine' }
  },
  virgo: {
    overview: 'Details matter today. Your analysis saves the day.',
    love: 'Practical gestures speak louder than words. Show you care.',
    career: 'Problem-solving skills peak. Tackle complex tasks now.',
    money: 'Review contracts carefully. Small savings add up.',
    health: 'Digestive system focus. Clean eating benefits you.',
    lucky: { color: 'Brown', number: 5, direction: 'South', time: '6:00 AM - 8:00 AM', energy: '7/10', tag: 'Organize' }
  },
  libra: {
    overview: 'Balance is your superpower today. Harmonize conflicts.',
    love: 'Partnership harmony peaks. Compromise brings joy.',
    career: 'Diplomatic skills shine. Mediate and negotiate well.',
    money: 'Fair deals favor you. Seek win-win situations.',
    health: 'Kidneys and skin need care. Stay hydrated.',
    lucky: { color: 'Pink', number: 6, direction: 'West', time: '4:00 PM - 6:00 PM', energy: '8/10', tag: 'Harmony' }
  },
  scorpio: {
    overview: 'Transformation energy surrounds you. Embrace change.',
    love: 'Deep emotional bonds strengthen. Vulnerability is power.',
    career: 'Research and investigation succeed. Dig deeper.',
    money: 'Hidden opportunities emerge. Trust your intuition.',
    health: 'Reproductive and elimination systems. Detoxify gently.',
    lucky: { color: 'Black', number: 4, direction: 'North', time: '8:00 PM - 10:00 PM', energy: '9/10', tag: 'Transform' }
  },
  sagittarius: {
    overview: 'Adventure calls strongly today. Expand your horizons.',
    love: 'Freedom and fun attract romance. Be playful and spontaneous.',
    career: 'International connections help. Think globally.',
    money: 'Risk-taking may pay off. Trust your optimism.',
    health: 'Hips and thighs benefit from movement. Exercise outdoors.',
    lucky: { color: 'Purple', number: 3, direction: 'East', time: '10:00 AM - 12:00 PM', energy: '10/10', tag: 'Explore' }
  },
  capricorn: {
    overview: 'Ambition drives you today. Climb steadily toward goals.',
    love: 'Commitment and loyalty matter. Build lasting foundations.',
    career: 'Leadership opportunities arise. Take charge gracefully.',
    money: 'Long-term investments favored. Delayed gratification wins.',
    health: 'Knees and bones need support. Calcium-rich foods help.',
    lucky: { color: 'Navy', number: 8, direction: 'South', time: '4:00 PM - 6:00 PM', energy: '8/10', tag: 'Achieve' }
  },
  aquarius: {
    overview: 'Innovation flows freely. Think outside the box.',
    love: 'Unconventional approaches succeed. Be uniquely you.',
    career: 'Technology and teamwork shine. Collaborate on big ideas.',
    money: 'Unexpected gains possible. Stay open to surprises.',
    health: 'Circulation and ankles need care. Walk and move regularly.',
    lucky: { color: 'Electric Blue', number: 11, direction: 'West', time: '12:00 AM - 2:00 AM', energy: '9/10', tag: 'Innovate' }
  },
  pisces: {
    overview: 'Intuition is razor-sharp today. Trust your dreams.',
    love: 'Soul connections deepen. Spiritual bonds matter most.',
    career: 'Creative solutions emerge. Art and imagination lead.',
    money: 'Charity and giving return blessings. Share what you have.',
    health: 'Feet and lymphatic system. Gentle swimming or baths help.',
    lucky: { color: 'Sea Green', number: 7, direction: 'North', time: '6:00 PM - 8:00 PM', energy: '7/10', tag: 'Dream' }
  }
};

// Yesterday's data for trend comparison
function getYesterdayData(sign) {
  const yesterday = { ...horoscopeData[sign] };
  yesterday.energy = Math.max(1, (parseInt(yesterday.lucky.energy) - 2)) + '/10';
  return yesterday;
}

// Main chat endpoint
app.post('/api/chat', async (req, res) => {
  const { message, sessionId = 'default' } = req.body;
  const lowerMsg = message.toLowerCase();
  
  // Initialize session if needed
  if (!sessions.has(sessionId)) {
    sessions.set(sessionId, { sign: null, lastTopic: null });
  }
  const session = sessions.get(sessionId);
  
  let reply = '';
  let detectedSign = null;
  
  // Check for birth date format (YYYY-MM-DD)
  const dateMatch = message.match(/\d{4}-\d{2}-\d{2}/);
  if (dateMatch) {
    detectedSign = getSignFromDate(dateMatch[0]);
    if (detectedSign) {
      session.sign = detectedSign;
      const data = horoscopeData[detectedSign];
      reply = `**${detectedSign.charAt(0).toUpperCase() + detectedSign.slice(1)} Horoscope for Today**\n\n` +
              `**Overview:** ${data.overview}\n\n` +
              `**Love:** ${data.love}\n` +
              `**Career:** ${data.career}\n` +
              `**Money:** ${data.money}\n` +
              `**Health:** ${data.health}\n\n` +
              `**Lucky Guide:**\n` +
              `🎨 Color: ${data.lucky.color}\n` +
              `🔢 Number: ${data.lucky.number}\n` +
              `🧭 Direction: ${data.lucky.direction}\n` +
              `⏰ Best Time: ${data.lucky.time}\n` +
              `⚡ Energy: ${data.lucky.energy}/10\n` +
              `🏷️ Tag: ${data.lucky.tag}\n\n` +
              `Ask me about "trends" to compare with yesterday, or "calendar" for day ratings!`;
    }
  }
  
  // Check for zodiac sign
  if (!detectedSign) {
    for (const sign of Object.keys(horoscopeData)) {
      if (lowerMsg.includes(sign)) {
        detectedSign = sign;
        session.sign = sign;
        const data = horoscopeData[sign];
        reply = `**${sign.charAt(0).toUpperCase() + sign.slice(1)} Horoscope for Today**\n\n` +
                `**Overview:** ${data.overview}\n\n` +
                `**Love:** ${data.love}\n` +
                `**Career:** ${data.career}\n` +
                `**Money:** ${data.money}\n` +
                `**Health:** ${data.health}\n\n` +
                `**Lucky Guide:**\n` +
                `🎨 Color: ${data.lucky.color}\n` +
                `🔢 Number: ${data.lucky.number}\n` +
                `🧭 Direction: ${data.lucky.direction}\n` +
                `⏰ Best Time: ${data.lucky.time}\n` +
                `⚡ Energy: ${data.lucky.energy}/10\n` +
                `🏷️ Tag: ${data.lucky.tag}\n\n` +
                `Ask me about "trends" to compare with yesterday, or "calendar" for day ratings!`;
        break;
      }
    }
  }
  
  // Check for specific topics
  if (lowerMsg.includes('love') || lowerMsg.includes('romance')) {
    if (session.sign) {
      reply = `**Love Reading for ${session.sign.charAt(0).toUpperCase() + session.sign.slice(1)}**\n\n${horoscopeData[session.sign].love}\n\nLucky color for love today: ${horoscopeData[session.sign].lucky.color}`;
    } else {
      reply = 'Please tell me your zodiac sign or birth date first so I can give you a personalized love reading!';
    }
  } else if (lowerMsg.includes('career') || lowerMsg.includes('work')) {
    if (session.sign) {
      reply = `**Career Reading for ${session.sign.charAt(0).toUpperCase() + session.sign.slice(1)}**\n\n${horoscopeData[session.sign].career}\n\nBest direction for career moves today: ${horoscopeData[session.sign].lucky.direction}`;
    } else {
      reply = 'Please tell me your zodiac sign or birth date first so I can give you a personalized career reading!';
    }
  } else if (lowerMsg.includes('money') || lowerMsg.includes('finance')) {
    if (session.sign) {
      reply = `**Money Reading for ${session.sign.charAt(0).toUpperCase() + session.sign.slice(1)}**\n\n${horoscopeData[session.sign].money}\n\nLucky number for financial decisions today: ${horoscopeData[session.sign].lucky.number}`;
    } else {
      reply = 'Please tell me your zodiac sign or birth date first so I can give you a personalized money reading!';
    }
  } else if (lowerMsg.includes('health')) {
    if (session.sign) {
      reply = `**Health Reading for ${session.sign.charAt(0).toUpperCase() + session.sign.slice(1)}**\n\n${horoscopeData[session.sign].health}\n\nEnergy level today: ${horoscopeData[session.sign].lucky.energy}/10`;
    } else {
      reply = 'Please tell me your zodiac sign or birth date first so I can give you a personalized health reading!';
    }
  } else if (lowerMsg.includes('lucky') || lowerMsg.includes('fortune')) {
    if (session.sign) {
      const lucky = horoscopeData[session.sign].lucky;
      reply = `**Lucky Guide for ${session.sign.charAt(0).toUpperCase() + session.sign.slice(1)}**\n\n` +
              `🎨 Lucky Color: ${lucky.color}\n` +
              `🔢 Lucky Number: ${lucky.number}\n` +
              `🧭 Lucky Direction: ${lucky.direction}\n` +
              `⏰ Best Time: ${lucky.time}\n` +
              `⚡ Energy Level: ${lucky.energy}/10\n` +
              `🏷️ Day Tag: ${lucky.tag}`;
    } else {
      reply = 'Please tell me your zodiac sign or birth date first so I can give you your lucky guide!';
    }
  } else if (lowerMsg.includes('trend') || lowerMsg.includes('yesterday') || lowerMsg.includes('compare')) {
    if (session.sign) {
      const today = horoscopeData[session.sign];
      const yesterday = getYesterdayData(session.sign);
      reply = `**Trend Analysis for ${session.sign.charAt(0).toUpperCase() + session.sign.slice(1)}**\n\n` +
              `**Yesterday:** Energy was ${yesterday.lucky.energy}/10 - More subdued day\n` +
              `**Today:** Energy is ${today.lucky.energy}/10 - ${parseInt(today.lucky.energy) > parseInt(yesterday.lucky.energy) ? 'Rising energy, take action!' : 'Steady energy, maintain course'}\n\n` +
              `**Trend:** ${parseInt(today.lucky.energy) > parseInt(yesterday.lucky.energy) ? '↗️ Improving - Good day to start new projects' : '→ Stable - Focus on completing existing tasks'}\n\n` +
              `Yesterday's tag was "Maintain", today's is "${today.lucky.tag}"`;
    } else {
      reply = 'Please tell me your zodiac sign or birth date first so I can show you trend comparisons!';
    }
  } else if (lowerMsg.includes('calendar') || lowerMsg.includes('good day') || lowerMsg.includes('bad day') || lowerMsg.includes('rate my day') || lowerMsg.includes('is today good')) {
    if (session.sign) {
      const energy = parseInt(horoscopeData[session.sign].lucky.energy);
      let rating, color, suggestion;
      if (energy >= 8) {
        rating = '⭐⭐⭐⭐⭐ EXCELLENT';
        color = '🟢';
        suggestion = 'Great day for important decisions, meetings, and new beginnings!';
      } else if (energy >= 6) {
        rating = '⭐⭐⭐⭐ GOOD';
        color = '🔵';
        suggestion = 'Productive day - tackle your priority tasks.';
      } else if (energy >= 4) {
        rating = '⭐⭐⭐ MODERATE';
        color = '🟡';
        suggestion = 'Average day - focus on routine work, avoid risks.';
      } else {
        rating = '⭐⭐ CHALLENGING';
        color = '🔴';
        suggestion = 'Take it easy today - rest, reflect, and avoid major decisions.';
      }
      reply = `**Calendar Rating for Today**\n\n${color} ${rating}\n\n${suggestion}\n\n` +
              `Energy Level: ${energy}/10\n` +
              `Best for: ${energy >= 7 ? 'Leadership, Decisions, Socializing' : energy >= 5 ? 'Planning, Organizing, Learning' : 'Rest, Self-care, Reflection'}`;
    } else {
      reply = 'Please tell me your zodiac sign or birth date first so I can rate your day for the calendar!';
    }
  }

  // Natural language: full daily horoscope when session sign is known
  if (!reply && session.sign) {
    const fullHoroscopeTriggers = [
      'my horoscope', 'my daily', 'what is my horoscope', 'give me my horoscope',
      'tell me my horoscope', 'show my horoscope', 'what about today', "today's horoscope",
      'todays horoscope', 'daily horoscope', 'my reading', 'my prediction',
      'predict my day', 'what will happen today', 'how is my day', 'how is today',
      'full horoscope', 'complete horoscope', 'overall horoscope', 'horoscope today'
    ];
    if (fullHoroscopeTriggers.some(t => lowerMsg.includes(t))) {
      const data = horoscopeData[session.sign];
      reply = `**${session.sign.charAt(0).toUpperCase() + session.sign.slice(1)} Horoscope for Today**\n\n` +
              `**Overview:** ${data.overview}\n\n` +
              `**Love:** ${data.love}\n` +
              `**Career:** ${data.career}\n` +
              `**Money:** ${data.money}\n` +
              `**Health:** ${data.health}\n\n` +
              `**Lucky Guide:**\n` +
              `🎨 Color: ${data.lucky.color}\n` +
              `🔢 Number: ${data.lucky.number}\n` +
              `🧭 Direction: ${data.lucky.direction}\n` +
              `⏰ Best Time: ${data.lucky.time}\n` +
              `⚡ Energy: ${data.lucky.energy}/10\n` +
              `🏷️ Tag: ${data.lucky.tag}\n\n` +
              `Ask me about "trends" to compare with yesterday, or "calendar" for day ratings!`;
    }
  }

  // Notification / push preview when session sign is known
  if (!reply && session.sign) {
    const notificationTriggers = [
      'notification', 'push', 'morning alert', 'daily alert', 'send me daily',
      'notify me', 'morning summary', 'daily summary'
    ];
    if (notificationTriggers.some(t => lowerMsg.includes(t))) {
      const data = horoscopeData[session.sign];
      reply = `**🌅 Daily Horoscope Notification Preview for ${session.sign.charAt(0).toUpperCase() + session.sign.slice(1)}**\n\n` +
              `⚡ **Energy:** ${data.lucky.energy}/10 | 🏷️ **Tag:** ${data.lucky.tag}\n\n` +
              `**Overview:** ${data.overview}\n\n` +
              `🎨 **Lucky Color:** ${data.lucky.color}\n` +
              `🔢 **Lucky Number:** ${data.lucky.number}\n` +
              `⏰ **Best Time:** ${data.lucky.time}\n\n` +
              `*This is how your morning notification would look!*\n` +
              `*To subscribe: Use API /api/notification/subscribe with your sign and preferred time.*`;
    }
  }

  // If no specific topic detected, try RAG server for general questions
  if (!reply) {
    const ragAnswer = await askRAGServer(message, session.sign);
    if (ragAnswer) {
      reply = ragAnswer;
    } else {
      reply = `👋 Welcome to Daily Horoscope Agent!\n\nI can provide you with:\n• **Full daily horoscope** (love, career, health, money)\n• **Lucky guide** (color, number, direction, time)\n• **Trend analysis** (compare today vs yesterday)\n• **Calendar rating** (good/bad day for planning)\n\n**How to start:**\n1. Send your zodiac sign (e.g., "Leo", "Scorpio")\n2. Or send your birth date (e.g., "2004-12-12")\n\nThen ask me about love, career, money, health, lucky, trends, or calendar!`;
    }
  }
  
  // Save chat to database
  await saveChat(sessionId, message, reply, session.sign);
  
  res.json({ reply, sign: session.sign });
});

app.get('/api/horoscope/:sign', async (req, res) => {
  const sign = req.params.sign.toLowerCase();
  if (horoscopeData[sign]) {
    // Save horoscope view to database
    await saveHoroscope(sign, horoscopeData[sign], req.query.userId || 'anonymous');
    res.json(horoscopeData[sign]);
  } else {
    res.status(404).json({ error: 'Sign not found' });
  }
});

// Get chat history for a session
app.get('/api/chat/history/:sessionId', async (req, res) => {
  try {
    const chats = getChatsCollection();
    const history = await chats
      .find({ sessionId: req.params.sessionId })
      .sort({ timestamp: -1 })
      .limit(50)
      .toArray();
    res.json({ history: history.reverse() });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch chat history' });
  }
});

// Get horoscope history for a user
app.get('/api/horoscope/history/:userId', async (req, res) => {
  try {
    const horoscopes = getHoroscopesCollection();
    const history = await horoscopes
      .find({ userId: req.params.userId })
      .sort({ createdAt: -1 })
      .limit(30)
      .toArray();
    res.json({ history });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch horoscope history' });
  }
});

app.listen(PORT, () => {
  console.log(`🌟 Daily Horoscope Agent running at http://localhost:${PORT}`);
});
