import { MongoClient } from 'mongodb';

const MONGODB_URL = "mongodb+srv://web_db_user:nency2004@dailyhoroscope.buhj27w.mongodb.net/";
const DB_NAME = "daily_horoscope";

let client;
let db;

export async function connectDB() {
  try {
    client = new MongoClient(MONGODB_URL);
    await client.connect();
    db = client.db(DB_NAME);
    console.log("Connected to MongoDB");
    return db;
  } catch (error) {
    console.error("MongoDB connection error:", error);
    throw error;
  }
}

export function getDB() {
  if (!db) {
    throw new Error("Database not connected. Call connectDB() first.");
  }
  return db;
}

export async function closeDB() {
  if (client) {
    await client.close();
    console.log("MongoDB connection closed");
  }
}

// Collection helpers
export function getHoroscopesCollection() {
  return getDB().collection('horoscopes');
}

export function getChatsCollection() {
  return getDB().collection('chats');
}

export function getUsersCollection() {
  return getDB().collection('users');
}
