#!/usr/bin/env python3
"""
Daily Horoscope Agent - Full Implementation
Pipeline: INPUT → VALIDATOR → EPHEMERIS → TRANSIT → RAG → LLM → OUTPUT
"""

import json
import re
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Import database manager for saving chat data
from database import db_manager

# Import live horoscope API (legacy - ZODIAC_SIGNS only for reference)
from external_api import (
    ZODIAC_SIGNS as API_ZODIAC_SIGNS
)

# Import response formatter for clean output
from response_formatter import (
    format_lucky_guide,
    format_day_rating,
    format_notification_preview,
    format_greeting,
    format_error,
    format_comparison,
    format_sign_profile
)

# Prokerala API for daily horoscope (working ✅)
from tools.prokerala_api import (
    get_daily_horoscope_prokerala_sync,
    get_panchang_prokerala_sync,
    get_lucky_details_prokerala_sync,
    format_prokerala_horoscope_reply,
)

# freehoroscopeapi.com for weekly/monthly (Prokerala doesn't have these)
from external_api import (
    get_weekly_horoscope,
    get_monthly_horoscope,
    format_horoscope_reply,
)

# Swiss Ephemeris for real planetary calculations
try:
    import swisseph as swe
    SWISSEPH_AVAILABLE = True
except ImportError:
    SWISSEPH_AVAILABLE = False
    print("Warning: pyswisseph not installed. Install with: pip install pyswisseph")

# ============================================================================
# CONFIGURATION
# ============================================================================

ZODIAC_SIGNS = [
    "aries", "taurus", "gemini", "cancer",
    "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces"
]

ZODIAC_DATES = {
    "aries": ((3, 21), (4, 19)),
    "taurus": ((4, 20), (5, 20)),
    "gemini": ((5, 21), (6, 20)),
    "cancer": ((6, 21), (7, 22)),
    "leo": ((7, 23), (8, 22)),
    "virgo": ((8, 23), (9, 22)),
    "libra": ((9, 23), (10, 22)),
    "scorpio": ((10, 23), (11, 21)),
    "sagittarius": ((11, 22), (12, 21)),
    "capricorn": ((12, 22), (1, 19)),
    "aquarius": ((1, 20), (2, 18)),
    "pisces": ((2, 19), (3, 20))
}

# Define PLANETS only if swisseph is available
if SWISSEPH_AVAILABLE:
    PLANETS = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE,  # North Node
        "Ketu": swe.MEAN_NODE   # South Node calculated separately
    }
else:
    # Mock planet IDs for when swisseph is not available
    PLANETS = {
        "Sun": 0, "Moon": 1, "Mercury": 2, "Venus": 3, "Mars": 4,
        "Jupiter": 5, "Saturn": 6, "Rahu": 10, "Ketu": 10
    }

ASPECTS = {
    "conjunction": 0,
    "sextile": 60,
    "square": 90,
    "trine": 120,
    "opposition": 180
}

ASPECT_ORBS = {
    "conjunction": 8,
    "sextile": 6,
    "square": 8,
    "trine": 8,
    "opposition": 8
}

# Comprehensive Zodiac Knowledge Base (RAG)
ZODIAC_DATASET = {
    "aries": {
        "number": 1,
        "date_range": "March 21 - April 19",
        "element": "Fire",
        "ruling_planet": "Mars",
        "symbol": "Ram",
        "traits": ["Energetic", "Bold", "Confident", "Impulsive"],
        "strengths": ["Leadership", "Courage", "Determination"],
        "weaknesses": ["Impatience", "Aggression"],
        "love": "Passionate and intense, values honesty and excitement.",
        "career": "Best in leadership, startups, competitive fields.",
        "health": "Needs stress control and proper rest.",
        "lucky": {"color": "Red", "number": 9, "day": "Tuesday"},
        "compatibility": ["Leo", "Sagittarius", "Gemini"],
        "love_advice": "Be direct about your feelings today.",
        "career_advice": "Take initiative on new projects.",
        "health_advice": "Channel energy through physical activity.",
        "money_advice": "Bold investments may pay off."
    },
    "taurus": {
        "number": 2,
        "date_range": "April 20 - May 20",
        "element": "Earth",
        "ruling_planet": "Venus",
        "symbol": "Bull",
        "traits": ["Stable", "Patient", "Reliable", "Stubborn"],
        "strengths": ["Loyalty", "Persistence"],
        "weaknesses": ["Stubbornness", "Possessiveness"],
        "love": "Loyal and romantic, seeks long-term stability.",
        "career": "Strong in finance, real estate, design.",
        "health": "Needs balanced diet and exercise.",
        "lucky": {"color": "Green", "number": 6, "day": "Friday"},
        "compatibility": ["Virgo", "Capricorn", "Cancer"],
        "love_advice": "Show love through practical gestures.",
        "career_advice": "Steady progress brings rewards.",
        "health_advice": "Focus on neck and throat care.",
        "money_advice": "Conservative approach serves you well."
    },
    "gemini": {
        "number": 3,
        "date_range": "May 21 - June 20",
        "element": "Air",
        "ruling_planet": "Mercury",
        "symbol": "Twins",
        "traits": ["Communicative", "Curious", "Adaptable"],
        "strengths": ["Intelligence", "Versatility"],
        "weaknesses": ["Inconsistency", "Indecision"],
        "love": "Needs communication and excitement.",
        "career": "Good in media, marketing, writing.",
        "health": "Avoid anxiety and overthinking.",
        "lucky": {"color": "Yellow", "number": 5, "day": "Wednesday"},
        "compatibility": ["Libra", "Aquarius", "Aries"],
        "love_advice": "Witty conversation sparks romance.",
        "career_advice": "Networking opens new doors.",
        "health_advice": "Mental stimulation is key today.",
        "money_advice": "Multiple small gains are favored."
    },
    "cancer": {
        "number": 4,
        "date_range": "June 21 - July 22",
        "element": "Water",
        "ruling_planet": "Moon",
        "symbol": "Crab",
        "traits": ["Emotional", "Caring", "Intuitive"],
        "strengths": ["Empathy", "Loyalty"],
        "weaknesses": ["Mood swings", "Sensitivity"],
        "love": "Deeply emotional and protective partner.",
        "career": "Good in caregiving, HR, management.",
        "health": "Needs emotional balance.",
        "lucky": {"color": "White", "number": 2, "day": "Monday"},
        "compatibility": ["Scorpio", "Pisces", "Taurus"],
        "love_advice": "Create emotional safety for deep connection.",
        "career_advice": "Collaboration brings success.",
        "health_advice": "Focus on digestion and stomach.",
        "money_advice": "Home-related investments favored."
    },
    "leo": {
        "number": 5,
        "date_range": "July 23 - August 22",
        "element": "Fire",
        "ruling_planet": "Sun",
        "symbol": "Lion",
        "traits": ["Confident", "Creative", "Charismatic"],
        "strengths": ["Leadership", "Generosity"],
        "weaknesses": ["Ego", "Stubbornness"],
        "love": "Loyal and passionate lover.",
        "career": "Best in leadership, acting, public roles.",
        "health": "Take care of heart health.",
        "lucky": {"color": "Gold", "number": 1, "day": "Sunday"},
        "compatibility": ["Aries", "Sagittarius", "Libra"],
        "love_advice": "Express your heart boldly.",
        "career_advice": "Leadership opportunities arise.",
        "health_advice": "Heart and spine need attention.",
        "money_advice": "Generosity returns to you."
    },
    "virgo": {
        "number": 6,
        "date_range": "August 23 - September 22",
        "element": "Earth",
        "ruling_planet": "Mercury",
        "symbol": "Maiden",
        "traits": ["Analytical", "Practical", "Detail-oriented"],
        "strengths": ["Precision", "Reliability"],
        "weaknesses": ["Overthinking", "Critical"],
        "love": "Supportive and caring partner.",
        "career": "Great in analytics, healthcare.",
        "health": "Focus on digestion and stress.",
        "lucky": {"color": "Brown", "number": 4, "day": "Wednesday"},
        "compatibility": ["Taurus", "Capricorn", "Cancer"],
        "love_advice": "Practical care shows love best.",
        "career_advice": "Detail-oriented work shines.",
        "health_advice": "Digestive health is priority.",
        "money_advice": "Review contracts carefully."
    },
    "libra": {
        "number": 7,
        "date_range": "September 23 - October 22",
        "element": "Air",
        "ruling_planet": "Venus",
        "symbol": "Scales",
        "traits": ["Balanced", "Diplomatic", "Charming"],
        "strengths": ["Fairness", "Social skills"],
        "weaknesses": ["Indecision"],
        "love": "Romantic and harmony-seeking.",
        "career": "Good in law, design, partnerships.",
        "health": "Maintain lifestyle balance.",
        "lucky": {"color": "Pink", "number": 7, "day": "Friday"},
        "compatibility": ["Gemini", "Aquarius", "Leo"],
        "love_advice": "Harmony in partnership brings joy.",
        "career_advice": "Diplomatic skills lead to wins.",
        "health_advice": "Kidneys and skin need care.",
        "money_advice": "Fair deals favor you today."
    },
    "scorpio": {
        "number": 8,
        "date_range": "October 23 - November 21",
        "element": "Water",
        "ruling_planet": "Mars/Pluto",
        "symbol": "Scorpion",
        "traits": ["Intense", "Passionate", "Mysterious"],
        "strengths": ["Focus", "Determination"],
        "weaknesses": ["Jealousy", "Secretive"],
        "love": "Deep emotional connection.",
        "career": "Strong in research, strategy.",
        "health": "Manage emotional stress.",
        "lucky": {"color": "Black", "number": 8, "day": "Tuesday"},
        "compatibility": ["Cancer", "Pisces", "Virgo"],
        "love_advice": "Deep emotional bonds strengthen.",
        "career_advice": "Research and investigation succeed.",
        "health_advice": "Detoxification supports wellness.",
        "money_advice": "Hidden opportunities emerge."
    },
    "sagittarius": {
        "number": 9,
        "date_range": "November 22 - December 21",
        "element": "Fire",
        "ruling_planet": "Jupiter",
        "symbol": "Archer",
        "traits": ["Adventurous", "Optimistic", "Independent"],
        "strengths": ["Honesty", "Freedom"],
        "weaknesses": ["Carelessness"],
        "love": "Needs freedom and honesty.",
        "career": "Good in travel, teaching.",
        "health": "Avoid overexertion.",
        "lucky": {"color": "Purple", "number": 3, "day": "Thursday"},
        "compatibility": ["Aries", "Leo", "Aquarius"],
        "love_advice": "Freedom and fun attract romance.",
        "career_advice": "International connections help.",
        "health_advice": "Hips and thighs benefit from movement.",
        "money_advice": "Calculated risks may pay off."
    },
    "capricorn": {
        "number": 10,
        "date_range": "December 22 - January 19",
        "element": "Earth",
        "ruling_planet": "Saturn",
        "symbol": "Goat",
        "traits": ["Disciplined", "Responsible", "Practical"],
        "strengths": ["Hardworking", "Patience"],
        "weaknesses": ["Pessimistic"],
        "love": "Serious and loyal partner.",
        "career": "Best in management, finance.",
        "health": "Care for bones and stress.",
        "lucky": {"color": "Grey", "number": 10, "day": "Saturday"},
        "compatibility": ["Taurus", "Virgo", "Pisces"],
        "love_advice": "Commitment builds lasting bonds.",
        "career_advice": "Leadership roles favor you.",
        "health_advice": "Knees and bones need support.",
        "money_advice": "Long-term investments favored."
    },
    "aquarius": {
        "number": 11,
        "date_range": "January 20 - February 18",
        "element": "Air",
        "ruling_planet": "Saturn/Uranus",
        "symbol": "Water Bearer",
        "traits": ["Innovative", "Independent", "Humanitarian"],
        "strengths": ["Creativity", "Thinking"],
        "weaknesses": ["Detached"],
        "love": "Values freedom and friendship.",
        "career": "Great in tech and innovation.",
        "health": "Manage stress and circulation.",
        "lucky": {"color": "Cyan", "number": 11, "day": "Saturday"},
        "compatibility": ["Gemini", "Libra", "Sagittarius"],
        "love_advice": "Uniqueness is your romantic asset.",
        "career_advice": "Technology and teamwork shine.",
        "health_advice": "Circulation needs attention.",
        "money_advice": "Unexpected gains possible."
    },
    "pisces": {
        "number": 12,
        "date_range": "February 19 - March 20",
        "element": "Water",
        "ruling_planet": "Jupiter/Neptune",
        "symbol": "Fish",
        "traits": ["Creative", "Emotional", "Intuitive"],
        "strengths": ["Empathy", "Imagination"],
        "weaknesses": ["Escapism"],
        "love": "Romantic and deeply emotional.",
        "career": "Good in art, healing.",
        "health": "Avoid emotional overload.",
        "lucky": {"color": "Sea Green", "number": 12, "day": "Thursday"},
        "compatibility": ["Cancer", "Scorpio", "Capricorn"],
        "love_advice": "Soul connections deepen today.",
        "career_advice": "Creative solutions emerge.",
        "health_advice": "Feet and lymphatic system need care.",
        "money_advice": "Charity brings karmic returns."
    }
}

# Knowledge base alias for backward compatibility
KNOWLEDGE_BASE = ZODIAC_DATASET

# Lucky mappings
LUCKY_COLORS = {
    "aries": "Red", "taurus": "Green", "gemini": "Yellow",
    "cancer": "Silver", "leo": "Gold", "virgo": "Brown",
    "libra": "Pink", "scorpio": "Black", "sagittarius": "Purple",
    "capricorn": "Navy", "aquarius": "Electric Blue", "pisces": "Sea Green"
}

LUCKY_NUMBERS = {
    "aries": 9, "taurus": 6, "gemini": 5, "cancer": 2,
    "leo": 1, "virgo": 5, "libra": 6, "scorpio": 4,
    "sagittarius": 3, "capricorn": 8, "aquarius": 11, "pisces": 7
}

LUCKY_DIRECTIONS = {
    "aries": "East", "taurus": "South", "gemini": "West",
    "cancer": "North", "leo": "East", "virgo": "South",
    "libra": "West", "scorpio": "North", "sagittarius": "East",
    "capricorn": "South", "aquarius": "West", "pisces": "North"
}

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PlanetaryPosition:
    planet: str
    sign: str
    degree: float
    retrograde: bool

@dataclass
class Transit:
    planet: str
    target_sign: str
    aspect: str
    angle: float
    orb: float
    effect: str  # 'positive', 'negative', 'neutral'

@dataclass
class HoroscopeReading:
    sign: str
    date: str
    day_rating: int
    overall_summary: str
    love_prediction: str
    love_score: float
    love_advice: str
    career_prediction: str
    career_score: float
    career_advice: str
    health_prediction: str
    health_score: float
    health_advice: str
    money_prediction: str
    money_score: float
    money_advice: str
    lucky_colour: str
    lucky_number: int
    lucky_direction: str
    best_time_window: str
    avoid_time_window: str
    morning_affirmation: str
    planetary_highlight: str
    raw_transits: List[Dict]

# ============================================================================
# STEP 1: INPUT VALIDATOR
# ============================================================================

class InputValidator:
    @staticmethod
    def validate_sign(sign: str) -> Optional[str]:
        sign = sign.lower().strip()
        return sign if sign in ZODIAC_SIGNS else None
    
    @staticmethod
    def date_to_sign(day: int, month: int) -> Optional[str]:
        for sign, ((start_m, start_d), (end_m, end_d)) in ZODIAC_DATES.items():
            if start_m == end_m:
                if month == start_m and start_d <= day <= end_d:
                    return sign
            else:
                if (month == start_m and day >= start_d) or (month == end_m and day <= end_d):
                    return sign
        return None
    
    @staticmethod
    def validate_birth_date(date_str: str) -> Optional[Tuple[str, int, int, int]]:
        formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]
        for fmt in formats:
            try:
                date = datetime.strptime(date_str, fmt)
                sign = InputValidator.date_to_sign(date.day, date.month)
                return (sign, date.day, date.month, date.year) if sign else None
            except ValueError:
                continue
        return None
    
    @staticmethod
    def validate_language(lang: str) -> str:
        supported = ["en", "es", "fr", "de", "hi", "gu"]
        return lang if lang in supported else "en"

# ============================================================================
# STEP 2: EPHEMERIS FETCHER
# ============================================================================

class EphemerisFetcher:
    def __init__(self):
        self.swisseph_available = SWISSEPH_AVAILABLE
        if self.swisseph_available:
            swe.set_ephe_path(None)
    
    def get_julian_day(self, date: datetime) -> float:
        return swe.julday(date.year, date.month, date.day, 12.0)
    
    def get_planetary_positions(self, date: datetime) -> List[PlanetaryPosition]:
        if not self.swisseph_available:
            return self._get_mock_positions(date)
        
        jd = self.get_julian_day(date)
        positions = []
        
        for planet_name, planet_id in PLANETS.items():
            if planet_name == "Ketu":
                continue  # Calculate separately
            
            result = swe.calc_ut(jd, planet_id, swe.FLG_EQUATORIAL)
            longitude = result[0][0]
            
            sign_index = int(longitude // 30)
            sign = ZODIAC_SIGNS[sign_index]
            degree_in_sign = longitude % 30
            
            # Check retrograde
            result_tomorrow = swe.calc_ut(jd + 1, planet_id, swe.FLG_EQUATORIAL)
            retrograde = result_tomorrow[0][0] < longitude
            
            positions.append(PlanetaryPosition(
                planet=planet_name,
                sign=sign,
                degree=degree_in_sign,
                retrograde=retrograde
            ))
        
        # Add Ketu (opposite of Rahu)
        rahu = next(p for p in positions if p.planet == "Rahu")
        ketu_longitude = (ZODIAC_SIGNS.index(rahu.sign) * 30 + rahu.degree + 180) % 360
        ketu_sign_index = int(ketu_longitude // 30)
        ketu_degree = ketu_longitude % 30
        
        positions.append(PlanetaryPosition(
            planet="Ketu",
            sign=ZODIAC_SIGNS[ketu_sign_index],
            degree=ketu_degree,
            retrograde=True
        ))
        
        return positions
    
    def _get_mock_positions(self, date: datetime) -> List[PlanetaryPosition]:
        """Generate deterministic mock positions based on date"""
        day_of_year = date.timetuple().tm_yday
        positions = []
        
        for i, (planet_name, _) in enumerate(PLANETS.items()):
            if planet_name == "Ketu":
                continue
            sign_index = (day_of_year + i * 30) % 12
            degree = (day_of_year * 1.5 + i * 5) % 30
            positions.append(PlanetaryPosition(
                planet=planet_name,
                sign=ZODIAC_SIGNS[sign_index],
                degree=degree,
                retrograde=False
            ))
        
        # Add Ketu
        rahu = next(p for p in positions if p.planet == "Rahu")
        ketu_sign_index = (ZODIAC_SIGNS.index(rahu.sign) + 6) % 12
        positions.append(PlanetaryPosition(
            planet="Ketu",
            sign=ZODIAC_SIGNS[ketu_sign_index],
            degree=rahu.degree,
            retrograde=True
        ))
        
        return positions
    
    def get_moon_phase(self, date: datetime) -> str:
        if not self.swisseph_available:
            return "Waxing Crescent"
        
        jd = self.get_julian_day(date)
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_EQUATORIAL)[0][0]
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_EQUATORIAL)[0][0]
        
        angle = (moon_pos - sun_pos) % 360
        
        if angle < 45:
            return "New Moon"
        elif angle < 90:
            return "Waxing Crescent"
        elif angle < 135:
            return "First Quarter"
        elif angle < 180:
            return "Waxing Gibbous"
        elif angle < 225:
            return "Full Moon"
        elif angle < 270:
            return "Waning Gibbous"
        elif angle < 315:
            return "Last Quarter"
        else:
            return "Waning Crescent"
    
    def get_day_energy_score(self, positions: List[PlanetaryPosition]) -> int:
        """Calculate overall day energy based on planetary alignments"""
        sun_pos = next(p for p in positions if p.planet == "Sun")
        moon_pos = next(p for p in positions if p.planet == "Moon")
        
        # Good day if Sun and Moon are in harmonious signs
        sun_idx = ZODIAC_SIGNS.index(sun_pos.sign)
        moon_idx = ZODIAC_SIGNS.index(moon_pos.sign)
        
        angle = abs((moon_idx - sun_idx) * 30)
        
        if angle in [0, 120, 60]:  # Conjunction, Trine, Sextile
            base_score = 8
        elif angle == 180:  # Opposition
            base_score = 5
        elif angle == 90:  # Square
            base_score = 6
        else:
            base_score = 7
        
        return min(10, max(1, base_score))

# ============================================================================
# STEP 3: TRANSIT CALCULATOR
# ============================================================================

class TransitCalculator:
    def __init__(self, positions: List[PlanetaryPosition]):
        self.positions = {p.planet: p for p in positions}
    
    def calculate_aspect(self, planet_pos: PlanetaryPosition, target_sign: str) -> Optional[Transit]:
        planet_sign_idx = ZODIAC_SIGNS.index(planet_pos.sign)
        target_sign_idx = ZODIAC_SIGNS.index(target_sign)
        
        angle = abs((planet_sign_idx - target_sign_idx) * 30)
        if angle > 180:
            angle = 360 - angle
        
        for aspect_name, aspect_angle in ASPECTS.items():
            orb = abs(angle - aspect_angle)
            if orb <= ASPECT_ORBS[aspect_name]:
                effect = self._get_aspect_effect(aspect_name, planet_pos.planet)
                return Transit(
                    planet=planet_pos.planet,
                    target_sign=target_sign,
                    aspect=aspect_name,
                    angle=angle,
                    orb=orb,
                    effect=effect
                )
        return None
    
    def _get_aspect_effect(self, aspect: str, planet: str) -> str:
        benefic_planets = ["Sun", "Moon", "Venus", "Jupiter"]
        malefic_planets = ["Saturn", "Mars", "Rahu", "Ketu"]
        













        
        if aspect in ["trine", "sextile", "conjunction"]:
            return "positive" if planet in benefic_planets else "mixed"
        elif aspect == "square":
            return "negative" if planet in malefic_planets else "challenge"
        elif aspect == "opposition":
            return "negative"
        return "neutral"
    
    def get_transits_for_sign(self, sign: str) -> List[Transit]:
        transits = []
        for planet_name, position in self.positions.items():
            transit = self.calculate_aspect(position, sign)
            if transit:
                transits.append(transit)
        return transits
    
    def calculate_life_area_scores(self, sign: str) -> Dict[str, float]:
        transits = self.get_transits_for_sign(sign)
        
        # Life area associations with planets
        areas = {
            "love": ["Venus", "Moon", "Sun"],
            "career": ["Saturn", "Sun", "Mars"],
            "health": ["Sun", "Moon", "Mars", "Saturn"],
            "money": ["Jupiter", "Venus", "Mercury"]
        }
        
        scores = {}
        for area, planets in areas.items():
            score = 5.0  # Neutral base
            for transit in transits:
                if transit.planet in planets:
                    if transit.effect == "positive":
                        score += 1.5
                    elif transit.effect == "negative":
                        score -= 1.5
                    elif transit.effect == "challenge":
                        score -= 0.5
                    elif transit.effect == "mixed":
                        score += 0.5
            scores[area] = round(max(1, min(10, score)), 1)
        
        return scores

# ============================================================================
# STEP 4: RAG ENGINE (In-Memory)
# ============================================================================

class RAGEngine:
    def __init__(self):
        self.knowledge_base = KNOWLEDGE_BASE
        self.dataset = ZODIAC_DATASET
        self.rag_documents = []
        self.load_rag_dataset()
    
    def load_rag_dataset(self):
        """Load RAG dataset from JSON file"""
        import json
        import os
        
        dataset_path = os.path.join(os.path.dirname(__file__), 'rag_dataset.json')
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.rag_documents = data.get('rag_dataset', {}).get('documents', [])
                print(f"Loaded {len(self.rag_documents)} RAG documents")
        except FileNotFoundError:
            print("RAG dataset file not found, using in-memory dataset")
            self.rag_documents = []
        except Exception as e:
            print(f"Error loading RAG dataset: {e}")
            self.rag_documents = []
    
    def search_documents(self, query: str, sign: str = None, limit: int = 5) -> List[Dict]:
        """Search RAG documents based on query and optional sign filter"""
        query_lower = query.lower()
        results = []
        
        for doc in self.rag_documents:
            # Filter by sign if provided
            if sign and doc.get('sign', '').lower() != sign.lower():
                continue
            
            # Calculate relevance score based on keyword matching
            score = 0
            text = doc.get('text', '').lower()
            keywords = doc.get('keywords', [])
            
            # Check if query words appear in text
            query_words = query_lower.split()
            for word in query_words:
                if word in text:
                    score += 1
                if word in [k.lower() for k in keywords]:
                    score += 2
            
            # Category-specific boosts
            category = doc.get('category', '')
            if 'planet' in query_lower and 'planet' in category:
                score += 3
            elif 'aspect' in query_lower and 'aspect' in category:
                score += 3
            elif 'moon' in query_lower and 'moon' in category:
                score += 3
            elif 'lucky' in query_lower and 'lucky' in category:
                score += 3
            
            if score > 0:
                results.append((doc, score))
        
        # Sort by score and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in results[:limit]]
    
    def retrieve_context(self, sign: str, transits: List[Transit]) -> Dict[str, str]:
        sign_data = self.knowledge_base.get(sign, {})
        
        # Build context from transit influences
        dominant_planets = [t.planet for t in transits if t.effect in ["positive", "mixed"]]
        challenging_planets = [t.planet for t in transits if t.effect in ["negative", "challenge"]]
        
        context = {
            "sign_traits": sign_data.get("traits", ""),
            "love_advice": sign_data.get("love_advice", ""),
            "career_advice": sign_data.get("career_advice", ""),
            "health_advice": sign_data.get("health_advice", ""),
            "money_advice": sign_data.get("money_advice", ""),
            "dominant_influences": ", ".join(dominant_planets) if dominant_planets else "Balanced energies",
            "challenges": ", ".join(challenging_planets) if challenging_planets else "None major"
        }
        
        return context
    
    def answer_question(self, question: str, sign: Optional[str] = None) -> str:
        """
        Answer questions about zodiac signs using the comprehensive RAG dataset
        """
        question_lower = question.lower()
        
        # Detect sign in question if not provided
        detected_sign = sign
        if not detected_sign:
            for zodiac in ZODIAC_SIGNS:
                if zodiac in question_lower:
                    detected_sign = zodiac
                    break
        
        # Search RAG documents first
        rag_results = self.search_documents(question, sign=detected_sign, limit=3)
        
        if rag_results:
            # Use RAG results to build answer
            return self._build_rag_answer(question, rag_results, detected_sign)
        
        # Fallback to in-memory dataset if no RAG results
        if not detected_sign:
            return "Please mention a zodiac sign so I can answer your question! (e.g., 'Tell me about Leo traits')"
        
        data = self.dataset.get(detected_sign, {})
        if not data:
            return f"Sorry, I don't have information about {detected_sign}."
        
        sign_name = detected_sign.title()
        
        # Answer based on question type
        if any(word in question_lower for word in ["trait", "personality", "characteristic", "like"]):
            traits = data.get("traits", [])
            strengths = data.get("strengths", [])
            weaknesses = data.get("weaknesses", [])
            return f"**{sign_name} Traits & Personality**\n\n" \
                   f"**Element:** {data.get('element', 'N/A')}\n" \
                   f"**Ruling Planet:** {data.get('ruling_planet', 'N/A')}\n" \
                   f"**Symbol:** {data.get('symbol', 'N/A')}\n\n" \
                   f"**Key Traits:** {', '.join(traits)}\n\n" \
                   f"**Strengths:** {', '.join(strengths)}\n\n" \
                   f"**Weaknesses:** {', '.join(weaknesses)}"
        
        elif any(word in question_lower for word in ["love", "relationship", "romance", "dating", "marriage"]):
            love_info = data.get("love", "")
            compatibility = data.get("compatibility", [])
            return f"**{sign_name} in Love & Relationships**\n\n" \
                   f"{love_info}\n\n" \
                   f"**Best Matches:** {', '.join(compatibility)}\n\n" \
                   f"**Advice:** {data.get('love_advice', '')}"
        
        elif any(word in question_lower for word in ["career", "job", "work", "profession", "business"]):
            career = data.get("career", "")
            return f"**{sign_name} Career & Profession**\n\n" \
                   f"{career}\n\n" \
                   f"**Advice:** {data.get('career_advice', '')}"
        
        elif any(word in question_lower for word in ["health", "wellness", "fitness", "body"]):
            health = data.get("health", "")
            return f"**{sign_name} Health & Wellness**\n\n" \
                   f"{health}\n\n" \
                   f"**Advice:** {data.get('health_advice', '')}"
        
        elif any(word in question_lower for word in ["lucky", "fortune", "color", "number", "day"]):
            lucky = data.get("lucky", {})
            return f"**{sign_name} Lucky Guide**\n\n" \
                   f"🎨 **Lucky Color:** {lucky.get('color', 'N/A')}\n" \
                   f"🔢 **Lucky Number:** {lucky.get('number', 'N/A')}\n" \
                   f"📅 **Lucky Day:** {lucky.get('day', 'N/A')}\n\n" \
                   f"**Money Advice:** {data.get('money_advice', '')}"
        
        elif any(word in question_lower for word in ["date", "birthday", "born", "range", "when"]):
            return f"**{sign_name} Date Range**\n\n" \
                   f"📅 **Dates:** {data.get('date_range', 'N/A')}\n" \
                   f"**Element:** {data.get('element', 'N/A')}\n" \
                   f"**Ruling Planet:** {data.get('ruling_planet', 'N/A')}"
        
        elif any(word in question_lower for word in ["compatible", "match", "compatibility", "best with", "worst with"]):
            compatibility = data.get("compatibility", [])
            return f"**{sign_name} Compatibility**\n\n" \
                   f"**Best Matches:** {', '.join(compatibility)}\n\n" \
                   f"**In Love:** {data.get('love', '')}"
        
        elif any(word in question_lower for word in ["element", "fire", "earth", "air", "water"]):
            return f"**{sign_name} Element**\n\n" \
                   f"**Element:** {data.get('element', 'N/A')}\n" \
                   f"**Traits:** {', '.join(data.get('traits', []))}\n\n" \
                   f"The {data.get('element', '').lower()} element makes {sign_name} " \
                   f"{'passionate and energetic' if data.get('element') == 'Fire' else ''}" \
                   f"{'practical and grounded' if data.get('element') == 'Earth' else ''}" \
                   f"{'intellectual and communicative' if data.get('element') == 'Air' else ''}" \
                   f"{'emotional and intuitive' if data.get('element') == 'Water' else ''}."
        
        elif any(word in question_lower for word in ["ruling planet", "planet", "mars", "venus", "mercury", "moon", "sun", "jupiter", "saturn"]):
            return f"**{sign_name} Ruling Planet**\n\n" \
                   f"**Planet:** {data.get('ruling_planet', 'N/A')}\n" \
                   f"**Element:** {data.get('element', 'N/A')}\n\n" \
                   f"The influence of {data.get('ruling_planet', '').split('/')[0]} gives {sign_name} " \
                   f"its characteristic {', '.join(data.get('traits', [])[:2])}."
        
        elif any(word in question_lower for word in ["symbol", "sign meaning", "represent", "icon"]):
            return f"**{sign_name} Symbol**\n\n" \
                   f"**Symbol:** {data.get('symbol', 'N/A')}\n" \
                   f"**Represents:** The {data.get('symbol', '').lower()} symbolizes " \
                   f"the core nature of {sign_name}: {', '.join(data.get('traits', [])[:3])}."
        
        # General info if no specific question type detected
        return f"**About {sign_name}**\n\n" \
               f"**Date Range:** {data.get('date_range', 'N/A')}\n" \
               f"**Element:** {data.get('element', 'N/A')}\n" \
               f"**Ruling Planet:** {data.get('ruling_planet', 'N/A')}\n" \
               f"**Symbol:** {data.get('symbol', 'N/A')}\n\n" \
               f"**Traits:** {', '.join(data.get('traits', []))}\n\n" \
               f"**Love:** {data.get('love', '')}\n\n" \
               f"**Career:** {data.get('career', '')}\n\n" \
               f"Ask me about: traits, love, career, health, lucky, compatibility, element, ruling planet!"
    
    def _build_rag_answer(self, question: str, results: List[Dict], sign: Optional[str]) -> str:
        """Build answer from RAG search results"""
        if not results:
            return "I couldn't find relevant information in my knowledge base. Please try rephrasing your question."
        
        answer_parts = []
        sign_name = sign.title() if sign else ""
        
        for i, doc in enumerate(results[:3], 1):
            category = doc.get('category', '')
            text = doc.get('text', '')
            doc_sign = doc.get('sign', '')
            
            if category == 'zodiac_sign':
                if sign_name:
                    answer_parts.append(f"**{sign_name} Information:**\n{text}")
                else:
                    answer_parts.append(f"**{doc_sign.title()} Information:**\n{text}")
            
            elif category == 'planet_sign_meaning':
                planet = doc.get('planet', '')
                doc_sign = doc.get('sign', '')
                answer_parts.append(f"**{planet} in {doc_sign.title()}:**\n{text}")
            
            elif category == 'aspect_interpretation':
                aspect = doc.get('aspect_type', '')
                p1 = doc.get('planet_1', '')
                p2 = doc.get('planet_2', '')
                answer_parts.append(f"**{p1} {aspect} {p2}:**\n{text}")
            
            elif category == 'zodiac_daily_profile':
                doc_sign = doc.get('sign', '')
                best_time = doc.get('best_time_window', '')
                avoid_time = doc.get('avoid_time_window', '')
                answer_parts.append(f"**{doc_sign.title()} Daily Profile:**\n{text}\n\n⏰ Best time: {best_time}\n⚠️ Avoid: {avoid_time}")
            
            elif category == 'moon_phase_impact':
                phase = doc.get('moon_phase', '')
                energy = doc.get('energy_level', '')
                answer_parts.append(f"**{phase} Moon:**\n{text}\n\nEnergy Level: {energy}")
            
            elif category == 'lucky_items':
                doc_sign = doc.get('sign', '')
                colors = doc.get('lucky_colours', [])
                numbers = doc.get('lucky_numbers', [])
                gemstone = doc.get('lucky_gemstone', '')
                answer_parts.append(f"**{doc_sign.title()} Lucky Items:**\n{text}\n\n🎨 Colors: {', '.join(colors)}\n🔢 Numbers: {', '.join(map(str, numbers))}\n💎 Gemstone: {gemstone}")
            
            else:
                answer_parts.append(f"**Information:**\n{text}")
            
            answer_parts.append("\n" + "-" * 50 + "\n")
        
        return "\n".join(answer_parts)

# ============================================================================
# STEP 5: LLM CORE (Rule-Based Generator)
# ============================================================================

class HoroscopeGenerator:
    def __init__(self):
        self.templates = {
            "love_positive": [
                "Romantic energy is flowing strongly today. Venus smiles upon your relationships.",
                "A special connection may deepen. Open your heart to love's possibilities.",
                "Passion and harmony blend beautifully. Express your feelings boldly."
            ],
            "love_neutral": [
                "Steady energy in relationships. Focus on building trust through consistency.",
                "A day for reflection on love's meaning. Quality over quantity matters.",
                "Relationships require patience today. Small gestures speak volumes."
            ],
            "love_challenge": [
                "Relationship tensions may surface. Stay calm and communicate with compassion.",
                "Old patterns may resurface. Use this as a chance for growth.",
                "Take time for self-love today. Your relationship with yourself sets the tone."
            ],
            "career_positive": [
                "Professional opportunities align in your favor. Leadership energy is strong.",
                "Your efforts gain recognition. Step confidently into the spotlight.",
                "Strategic moves pay dividends. Trust your professional instincts."
            ],
            "career_neutral": [
                "Steady progress at work. Focus on completing existing projects well.",
                "A day for planning and organizing. Set foundations for future success.",
                "Collaboration brings better results than solo efforts today."
            ],
            "career_challenge": [
                "Workplace friction may arise. Stay diplomatic and solution-focused.",
                "Delays or obstacles are temporary. Patience is your ally.",
                "Review your approach carefully. Attention to detail prevents errors."
            ]
        }
    
    def generate(self, sign: str, date: str, positions: List[PlanetaryPosition],
                 transits: List[Transit], scores: Dict[str, float],
                 rag_context: Dict[str, str], day_rating: int) -> HoroscopeReading:
        
        # Generate predictions based on scores
        love_prediction = self._get_prediction("love", scores["love"])
        career_prediction = self._get_prediction("career", scores["career"])
        health_prediction = self._get_prediction("health", scores["health"])
        money_prediction = self._get_prediction("money", scores["money"])
        
        # Build overall summary
        dominant_planet = self._get_dominant_planet(positions)
        overall_summary = self._build_summary(sign, day_rating, dominant_planet, rag_context)
        
        # Get lucky attributes
        lucky_color = LUCKY_COLORS.get(sign, "Blue")
        lucky_number = LUCKY_NUMBERS.get(sign, 7)
        lucky_direction = LUCKY_DIRECTIONS.get(sign, "East")
        
        # Calculate best time window based on Moon
        moon_pos = next(p for p in positions if p.planet == "Moon")
        best_time = self._calculate_best_time(moon_pos)
        avoid_time = self._calculate_avoid_time(positions)
        
        # Affirmation based on sign traits
        affirmation = self._generate_affirmation(sign, rag_context)
        
        # Planetary highlight
        planetary_highlight = self._build_planetary_highlight(transits)
        
        return HoroscopeReading(
            sign=sign,
            date=date,
            day_rating=day_rating,
            overall_summary=overall_summary,
            love_prediction=love_prediction,
            love_score=scores["love"],
            love_advice=rag_context.get("love_advice", ""),
            career_prediction=career_prediction,
            career_score=scores["career"],
            career_advice=rag_context.get("career_advice", ""),
            health_prediction=health_prediction,
            health_score=scores["health"],
            health_advice=rag_context.get("health_advice", ""),
            money_prediction=money_prediction,
            money_score=scores["money"],
            money_advice=rag_context.get("money_advice", ""),
            lucky_colour=lucky_color,
            lucky_number=lucky_number,
            lucky_direction=lucky_direction,
            best_time_window=best_time,
            avoid_time_window=avoid_time,
            morning_affirmation=affirmation,
            planetary_highlight=planetary_highlight,
            raw_transits=[asdict(t) for t in transits]
        )
    
    def _get_prediction(self, area: str, score: float) -> str:
        if score >= 7:
            key = f"{area}_positive"
        elif score >= 5:
            key = f"{area}_neutral"
        else:
            key = f"{area}_challenge"
        
        import random
        templates = self.templates.get(key, ["Energy is flowing today."])
        return random.choice(templates)
    
    def _get_dominant_planet(self, positions: List[PlanetaryPosition]) -> str:
        # Planet closest to 0 degrees of sign is most potent
        potent_planets = sorted(positions, key=lambda p: abs(p.degree - 15))
        return potent_planets[0].planet
    
    def _build_summary(self, sign: str, rating: int, dominant: str, context: Dict) -> str:
        if rating >= 8:
            return f"Today brings powerful energy for {sign.title()}. With {dominant} prominently positioned, embrace opportunities for growth and expansion. Trust your intuition and take bold action."
        elif rating >= 6:
            return f"A balanced day for {sign.title()}. {dominant} influences steady progress. Focus on maintaining harmony between action and reflection."
        else:
            return f"A day for patience and inner work, {sign.title()}. {dominant} asks you to slow down and reassess. Use this time for planning rather than major decisions."
    
    def _calculate_best_time(self, moon_pos: PlanetaryPosition) -> str:
        # Simplified calculation
        hour = int(6 + (ZODIAC_SIGNS.index(moon_pos.sign) * 2)) % 24
        return f"{hour:02d}:00 - {(hour+2):02d}:00"
    
    def _calculate_avoid_time(self, positions: List[PlanetaryPosition]) -> str:
        # Simplified - when Saturn is strongest
        saturn = next((p for p in positions if p.planet == "Saturn"), None)
        if saturn:
            hour = int(12 + saturn.degree) % 24
            return f"{hour:02d}:00 - {(hour+1):02d}:30"
        return "09:00 - 10:30"
    
    def _generate_affirmation(self, sign: str, context: Dict) -> str:
        traits = context.get("sign_traits", "unique and capable")
        affirmations = [
            f"I embrace my {traits} nature and create my destiny today.",
            f"As a {sign.title()}, I trust my intuition and move forward with confidence.",
            f"Today I embody the best qualities of {sign.title()}: {traits}."
        ]
        import random
        return random.choice(affirmations)
    
    def _build_planetary_highlight(self, transits: List[Transit]) -> str:
        if not transits:
            return "Balanced cosmic energies support steady progress."
        
        positive = [t for t in transits if t.effect == "positive"]
        if positive:
            return f"{positive[0].planet} forms a harmonious {positive[0].aspect} to your sign, bringing supportive energy."
        
        challenging = [t for t in transits if t.effect == "negative"]
        if challenging:
            return f"{challenging[0].planet} presents a {challenging[0].aspect} challenge—growth comes through patience."
        
        return f"{transits[0].planet} influences your day through a {transits[0].aspect} aspect."

# ============================================================================
# STEP 6: OUTPUT FORMATTER
# ============================================================================

class OutputFormatter:
    @staticmethod
    def to_json(reading: HoroscopeReading) -> Dict:
        return {
            "sign": reading.sign,
            "date": reading.date,
            "day_rating": reading.day_rating,
            "overall_summary": reading.overall_summary,
            "love": {
                "prediction": reading.love_prediction,
                "score": reading.love_score,
                "advice": reading.love_advice
            },
            "career": {
                "prediction": reading.career_prediction,
                "score": reading.career_score,
                "advice": reading.career_advice
            },
            "health": {
                "prediction": reading.health_prediction,
                "score": reading.health_score,
                "advice": reading.health_advice
            },
            "money": {
                "prediction": reading.money_prediction,
                "score": reading.money_score,
                "advice": reading.money_advice
            },
            "lucky_colour": reading.lucky_colour,
            "lucky_number": reading.lucky_number,
            "lucky_direction": reading.lucky_direction,
            "best_time_window": reading.best_time_window,
            "avoid_time_window": reading.avoid_time_window,
            "morning_affirmation": reading.morning_affirmation,
            "planetary_highlight": reading.planetary_highlight,
            "raw_transits": reading.raw_transits
        }
    
    @staticmethod
    def to_markdown(reading: HoroscopeReading) -> str:
        stars = "⭐" * reading.day_rating + "☆" * (10 - reading.day_rating)
        
        return f"""## 🌟 {reading.sign.title()} Horoscope for {reading.date}

**Day Rating:** {stars} ({reading.day_rating}/10)

### Overall
{reading.overall_summary}

**Planetary Highlight:** {reading.planetary_highlight}

---

### 💕 Love (Score: {reading.love_score}/10)
{reading.love_prediction}

*Advice: {reading.love_advice}*

### 💼 Career (Score: {reading.career_score}/10)
{reading.career_prediction}

*Advice: {reading.career_advice}*

### 🏥 Health (Score: {reading.health_score}/10)
{reading.health_prediction}

*Advice: {reading.health_advice}*

### 💰 Money (Score: {reading.money_score}/10)
{reading.money_prediction}

*Advice: {reading.money_advice}*

---

### 🍀 Lucky Guide
- **Color:** {reading.lucky_colour}
- **Number:** {reading.lucky_number}
- **Direction:** {reading.lucky_direction}
- **Best Time:** {reading.best_time_window}
- **Avoid:** {reading.avoid_time_window}

### 🌅 Morning Affirmation
"{reading.morning_affirmation}"
"""
    
    @staticmethod
    def to_plain_text(reading: HoroscopeReading) -> str:
        return f"""{reading.sign.title()} - {reading.date} - Day Rating: {reading.day_rating}/10

{reading.overall_summary}

Love {reading.love_score}/10: {reading.love_prediction}
Career {reading.career_score}/10: {reading.career_prediction}
Health {reading.health_score}/10: {reading.health_prediction}
Money {reading.money_score}/10: {reading.money_prediction}

Lucky: {reading.lucky_colour}, {reading.lucky_number}, {reading.lucky_direction}
Best time: {reading.best_time_window}

Affirmation: {reading.morning_affirmation}"""

# ============================================================================
# MAIN AGENT CLASS
# ============================================================================

class DailyHoroscopeAgent:
    def __init__(self):
        self.validator = InputValidator()
        self.ephemeris = EphemerisFetcher()
        self.rag = RAGEngine()
        self.generator = HoroscopeGenerator()
        self.formatter = OutputFormatter()
        
        # In-memory cache for yesterday's data (comparison feature)
        self.cache = {}
    
    def generate_horoscope(self, sign_or_date: str, date_str: Optional[str] = None,
                          language: str = "en", user_id: str = "default") -> Dict:
        """
        Main entry point for horoscope generation
        """
        # Step 1: Validate Input
        sign = self.validator.validate_sign(sign_or_date)
        birth_date_info = None
        
        if not sign:
            birth_date_info = self.validator.validate_birth_date(sign_or_date)
            if birth_date_info:
                sign, day, month, year = birth_date_info
            else:
                raise ValueError(f"Invalid input: {sign_or_date}. Please provide a zodiac sign or birth date.")
        
        # Validate and set date
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                date = datetime.now()
        else:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        language = self.validator.validate_language(language)
        
        # Check cache
        cache_key = f"{sign}_{date_str}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Step 2: Fetch Ephemeris
        positions = self.ephemeris.get_planetary_positions(date)
        moon_phase = self.ephemeris.get_moon_phase(date)
        day_rating = self.ephemeris.get_day_energy_score(positions)
        
        # Step 3: Calculate Transits
        transit_calc = TransitCalculator(positions)
        transits = transit_calc.get_transits_for_sign(sign)
        scores = transit_calc.calculate_life_area_scores(sign)
        
        # Step 4: Retrieve Knowledge Context
        rag_context = self.rag.retrieve_context(sign, transits)
        
        # Step 5: Generate Horoscope
        reading = self.generator.generate(
            sign=sign,
            date=date_str,
            positions=positions,
            transits=transits,
            scores=scores,
            rag_context=rag_context,
            day_rating=day_rating
        )
        
        # Step 6: Format Output
        result = {
            "structured_data": self.formatter.to_json(reading),
            "markdown_report": self.formatter.to_markdown(reading),
            "plain_text_summary": self.formatter.to_plain_text(reading),
            "images": [f"https://placehold.co/600x400/1a1a2e/9d4edd?text={sign.title()}+Horoscope"]
        }
        
        # Cache result
        self.cache[cache_key] = result
        
        return result
    
    def compare_with_yesterday(self, sign: str, user_id: str = "default") -> Dict:
        """Compare today's horoscope with yesterday's"""
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        today_result = self.generate_horoscope(sign, today.strftime("%Y-%m-%d"), "en", user_id)
        yesterday_result = self.generate_horoscope(sign, yesterday.strftime("%Y-%m-%d"), "en", user_id)
        
        today_data = today_result["structured_data"]
        yesterday_data = yesterday_result["structured_data"]
        
        # Calculate deltas
        areas = ["love", "career", "health", "money"]
        comparison = {}
        
        for area in areas:
            today_score = today_data[area]["score"]
            yesterday_score = yesterday_data[area]["score"]
            delta = today_score - yesterday_score
            
            if delta > 0.5:
                trend = "↗️ Improving"
            elif delta < -0.5:
                trend = "↘️ Declining"
            else:
                trend = "→ Stable"
            
            comparison[area] = {
                "yesterday": yesterday_score,
                "today": today_score,
                "delta": round(delta, 1),
                "trend": trend
            }
        
        return {
            "sign": sign,
            "comparison": comparison,
            "summary": f"Overall trend from {yesterday_data['day_rating']} to {today_data['day_rating']} stars",
            "markdown": self._format_comparison_markdown(sign, comparison, yesterday_data, today_data),
            "advice": "Focus on areas marked as improving. Be cautious in declining areas."
        }
    
    def _format_comparison_markdown(self, sign: str, comparison: Dict, yesterday: Dict, today: Dict) -> str:
        md = f"## 📊 {sign.title()}: Yesterday vs Today\n\n"
        md += f"**Overall:** {yesterday['day_rating']}⭐ → {today['day_rating']}⭐\n\n"
        md += "| Area | Yesterday | Today | Change | Trend |\n"
        md += "|------|-----------|-------|--------|-------|\n"
        
        for area, data in comparison.items():
            emoji = {"love": "💕", "career": "💼", "health": "🏥", "money": "💰"}[area]
            md += f"| {emoji} {area.title()} | {data['yesterday']}/10 | {data['today']}/10 | {data['delta']:+.1f} | {data['trend']} |\n"
        
        return md

# ============================================================================
# CHAT INTERFACE
# ============================================================================

class ChatInterface:
    def __init__(self):
        self.agent = DailyHoroscopeAgent()
        self.rag = RAGEngine()
        self.sessions = {}
    
    def chat(self, message: str, session_id: str = "default") -> str:
        """Process chat message and return response, saving to database"""
        msg_lower = message.lower().strip()
        
        # Initialize session with conversation state
        if session_id not in self.sessions:
            self.sessions[session_id] = {"sign": None, "last_topic": None, "pending_question": None}
        session = self.sessions[session_id]
        
        reply = None
        sign = None
        metadata = {}
        
        # Handle pending questions (user is answering a previous question)
        if session.get("pending_question"):
            pending = session["pending_question"]
            # Try to extract sign from user reply
            for zodiac in ZODIAC_SIGNS:
                if zodiac in msg_lower:
                    sign = zodiac
                    session["sign"] = sign
                    session["pending_question"] = None
                    break
            
            # If still no sign, try birth date
            if not sign:
                date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', message)
                if date_match:
                    day, month, year = date_match.groups()
                    birth_info = self.agent.validator.validate_birth_date(f"{day}/{month}/{year}")
                    if birth_info:
                        sign, _, _, _ = birth_info
                        session["sign"] = sign
                        session["pending_question"] = None
            
            # If sign was found from pending question, handle the original request
            if sign and pending in ["lucky_number", "birth_date_lucky"]:
                result = self.agent.generate_horoscope(sign)
                d = result["structured_data"]
                reply = format_lucky_guide(d, sign)
                metadata["type"] = "lucky_answer"
                metadata["source"] = "local"
            
            # Clear pending if we got a valid answer
            if sign:
                session["pending_question"] = None
        
        # Simple greetings and conversation
        greetings = ["hello", "hi", "hey", "howdy", "good morning", "good afternoon", "good evening"]
        how_are_you = ["how are you", "how's it going", "what's up", "how are you doing"]
        
        if any(g in msg_lower for g in greetings):
            reply = format_greeting()
            metadata["type"] = "greeting"
        elif any(h in msg_lower for h in how_are_you):
            reply = "✨ I'm doing great, ready to read the stars for you!\n\nWhat can I tell you about your horoscope today?"
            metadata["type"] = "conversation"
        
        # Check for comparison request
        if any(word in msg_lower for word in ["compare", "yesterday", "trend", "vs"]):
            if session["sign"]:
                result = self.agent.compare_with_yesterday(session["sign"], session_id)
                reply = result["markdown"]
                sign = session["sign"]
                metadata["type"] = "comparison"
            else:
                reply = format_error("Please tell me your zodiac sign first (e.g., 'Leo', 'Scorpio')!")
                metadata["type"] = "error"
        
        # Check for push notification / daily summary requests
        if reply is None and any(word in msg_lower for word in ["notification", "push", "morning alert", "daily alert", "send me daily", "notify me"]):
            if session["sign"]:
                sign = session["sign"]
                result = self.agent.generate_horoscope(sign)
                data = result["structured_data"]
                reply = format_notification_preview(data, sign)
                metadata["type"] = "notification_preview"
                metadata["source"] = "local"
            else:
                reply = format_error("Please tell me your zodiac sign first so I can show you a daily notification preview!")
                metadata["type"] = "error"
        
        # Check for calendar / day rating requests
        if reply is None and any(word in msg_lower for word in ["calendar", "good day", "bad day", "day rating", "rate my day", "is today good"]):
            if session["sign"]:
                sign = session["sign"]
                result = self.agent.generate_horoscope(sign)
                data = result["structured_data"]
                
                scores = [data['love']['score'], data['career']['score'], data['health']['score'], data['money']['score']]
                avg = sum(scores) / len(scores)
                
                reply = format_day_rating(data, sign, avg)
                metadata["type"] = "calendar_rating"
                metadata["source"] = "local"
            else:
                reply = format_error("Please tell me your zodiac sign first so I can rate your day for the calendar!")
                metadata["type"] = "error"

        # ── Prokerala Panchang / Auspicious details ──
        prokerala_triggers = [
            "panchang", "prokerala", "auspicious", "tithi", "nakshatra",
            "shubh", "muhurat", "muhurta", "rahukalam", "yamagandam",
            "good time", "bad time", "favourable time"
        ]
        if reply is None and any(t in msg_lower for t in prokerala_triggers):
            if session["sign"]:
                sign = session["sign"]
                try:
                    result = get_lucky_details_prokerala_sync(sign)
                    panchang = result.get("panchang", {})
                    p_data = panchang.get("data", {})
                    tithi = result.get("tithi", "N/A")
                    nakshatra = result.get("nakshatra", "N/A")
                    lines = [
                        f"## 🕉️ Prokerala Panchang for {sign.title()}",
                        f"**Date:** {result.get('date', 'Today')}",
                        "",
                        f"**Tithi:** {tithi}",
                        f"**Nakshatra:** {nakshatra}",
                        "",
                    ]
                    if isinstance(p_data, dict):
                        for key in ["sunrise", "sunset", "rahukalam", "yamagandam", "gulikai"]:
                            val = p_data.get(key)
                            if val:
                                lines.append(f"**{key.replace('_', ' ').title()}:** {val}")
                    lines += [
                        "",
                        f"🎨 **Lucky Colour:** {result.get('lucky_colour', 'N/A')}",
                        f"🔢 **Lucky Number:** {result.get('lucky_number', 'N/A')}",
                        f"🧭 **Lucky Direction:** {result.get('lucky_direction', 'N/A')}",
                        "",
                        "_Powered by Prokerala API_",
                    ]
                    reply = "\n".join(lines)
                    metadata["type"] = "prokerala_panchang"
                    metadata["source"] = "prokerala"
                except Exception as e:
                    reply = f"⚠️ Could not fetch Prokerala data: {str(e)}\n\nFalling back to local lucky guide..."
                    try:
                        result = self.agent.generate_horoscope(sign)
                        reply += "\n\n" + format_lucky_guide(result["structured_data"], sign)
                    except Exception:
                        pass
                    metadata["type"] = "prokerala_error"
            else:
                reply = format_error("Please tell me your zodiac sign first so I can fetch Prokerala Panchang details!")
                metadata["type"] = "error"
        
        # Natural language triggers for a FULL daily horoscope (no specific topic)
        full_horoscope_triggers = [
            "my horoscope", "my daily", "what is my horoscope", "give me my horoscope",
            "tell me my horoscope", "show my horoscope", "what about today", "today's horoscope",
            "todays horoscope", "daily horoscope", "my reading", "my prediction",
            "predict my day", "what will happen today", "how is my day", "how is today"
        ]
        wants_full_horoscope = any(t in msg_lower for t in full_horoscope_triggers)

        # If user asks for full horoscope and we have a session sign, return it
        if reply is None and wants_full_horoscope and session["sign"]:
            sign = session["sign"]
            try:
                api_result = get_daily_horoscope_prokerala_sync(sign)
                if api_result and "error" not in api_result:
                    reply = format_prokerala_horoscope_reply(api_result)
                    metadata["type"] = "daily_horoscope"
                    metadata["source"] = "prokerala"
                else:
                    result = self.agent.generate_horoscope(sign)
                    reply = result["markdown_report"]
                    metadata["type"] = "full_horoscope"
                    metadata["source"] = "local_fallback"
            except Exception as e:
                reply = f"Error fetching horoscope: {str(e)}"
                metadata["type"] = "error"
                metadata["error"] = str(e)

        # Check for knowledge-based questions (traits, compatibility, element, etc.)
        if reply is None:
            knowledge_keywords = [
                "trait", "personality", "characteristic", "like", "what is", "tell me about",
                "compatible", "match", "compatibility", "best with", "worst with",
                "element", "fire", "earth", "air", "water",
                "ruling planet", "planet", "symbol", "represent", "icon",
                "date", "birthday", "born", "range", "when is"
            ]
            is_knowledge_question = any(kw in msg_lower for kw in knowledge_keywords)

            # Try to get sign from message
            for zodiac in ZODIAC_SIGNS:
                if zodiac in msg_lower:
                    sign = zodiac
                    session["sign"] = sign
                    break

            # Try birth date
            if not sign:
                date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', message)
                if date_match:
                    day, month, year = date_match.groups()
                    birth_info = self.agent.validator.validate_birth_date(f"{day}/{month}/{year}")
                    if birth_info:
                        sign, _, _, _ = birth_info
                        session["sign"] = sign

            # If knowledge question with sign, use RAG to answer
            if is_knowledge_question:
                rag_sign = sign or session["sign"]
                if rag_sign:
                    reply = self.rag.answer_question(message, rag_sign)
                    metadata["type"] = "knowledge"
                    metadata["rag_sign"] = rag_sign
                else:
                    reply = format_error("Please mention a zodiac sign so I can answer! (e.g., 'Tell me about Leo traits')")
                    metadata["type"] = "error"
            # If user just mentioned their sign (no specific topic question), return LIVE daily horoscope
            elif sign and not is_knowledge_question:
                # Check for topic keywords (lucky, love, career, health, money)
                topics = ["love", "career", "health", "money", "lucky"]
                requested_topic = None
                for topic in topics:
                    if topic in msg_lower:
                        requested_topic = topic
                        break

                # Determine period: daily, weekly, or monthly
                period = "daily"
                if any(w in msg_lower for w in ["weekly", "week", "this week"]):
                    period = "weekly"
                elif any(w in msg_lower for w in ["monthly", "month", "this month"]):
                    period = "monthly"

                try:
                    if requested_topic == "lucky":
                        result = self.agent.generate_horoscope(sign)
                        d = result["structured_data"]
                        reply = format_lucky_guide(d, sign)
                        metadata["type"] = "lucky"
                        metadata["source"] = "local"
                    elif period == "weekly":
                        api_result = get_weekly_horoscope(sign)
                        if api_result:
                            reply = format_horoscope_reply(api_result)
                            metadata["type"] = "weekly_horoscope"
                            metadata["source"] = "freehoroscopeapi.com"
                    elif period == "monthly":
                        api_result = get_monthly_horoscope(sign)
                        if api_result:
                            reply = format_horoscope_reply(api_result)
                            metadata["type"] = "monthly_horoscope"
                            metadata["source"] = "freehoroscopeapi.com"
                    else:
                        # Default: daily horoscope from Prokerala API
                        api_result = get_daily_horoscope_prokerala_sync(sign)
                        if api_result and "error" not in api_result:
                            reply = format_prokerala_horoscope_reply(api_result)
                            metadata["type"] = "daily_horoscope"
                            metadata["source"] = "prokerala"

                    if reply is None:
                        result = self.agent.generate_horoscope(sign)
                        reply = result["markdown_report"]
                        metadata["type"] = "full_horoscope"
                        metadata["source"] = "local_fallback"
                except Exception as e:
                    reply = f"Error fetching horoscope: {str(e)}"
                    metadata["type"] = "error"
                    metadata["error"] = str(e)

        # Check for specific topic requests (daily horoscope topics)
        if reply is None:
            topics = ["love", "career", "health", "money", "lucky"]
            requested_topic = None
            for topic in topics:
                if topic in msg_lower:
                    requested_topic = topic
                    break

            # Determine period: daily, weekly, or monthly
            period = "daily"
            if any(w in msg_lower for w in ["weekly", "week", "this week"]):
                period = "weekly"
            elif any(w in msg_lower for w in ["monthly", "month", "this month"]):
                period = "monthly"

            # If we have a sign, fetch live horoscope from API
            if sign:
                try:
                    # SPECIAL CASE: user asked specifically for lucky info
                    if requested_topic == "lucky":
                        result = self.agent.generate_horoscope(sign)
                        d = result["structured_data"]
                        reply = format_lucky_guide(d, sign)
                        metadata["type"] = "lucky"
                        metadata["source"] = "local"
                    elif period == "weekly":
                        api_result = get_weekly_horoscope(sign)
                        metadata["period"] = "weekly"
                        if api_result:
                            reply = format_horoscope_reply(api_result)
                            metadata["type"] = "weekly_horoscope"
                            metadata["source"] = "freehoroscopeapi.com"
                    elif period == "monthly":
                        api_result = get_monthly_horoscope(sign)
                        metadata["period"] = "monthly"
                        if api_result:
                            reply = format_horoscope_reply(api_result)
                            metadata["type"] = "monthly_horoscope"
                            metadata["source"] = "freehoroscopeapi.com"
                    else:
                        # Default: daily horoscope from Prokerala API
                        api_result = get_daily_horoscope_prokerala_sync(sign)
                        metadata["period"] = "daily"
                        if api_result and "error" not in api_result:
                            reply = format_prokerala_horoscope_reply(api_result)
                            metadata["type"] = "daily_horoscope"
                            metadata["source"] = "prokerala"

                    # If API didn't return anything, fallback to local
                    if reply is None:
                        result = self.agent.generate_horoscope(sign)
                        reply = result["markdown_report"]
                        metadata["type"] = "full_horoscope"
                        metadata["source"] = "local_fallback"
                except Exception as e:
                    reply = f"Error fetching horoscope: {str(e)}"
                    metadata["type"] = "error"
                    metadata["error"] = str(e)

            # If we have session sign and topic request (no sign in current message)
            elif session["sign"] and reply is None:
                try:
                    sign = session["sign"]
                    # SPECIAL CASE: user asked for lucky info with known session sign
                    if requested_topic == "lucky":
                        result = self.agent.generate_horoscope(sign)
                        d = result["structured_data"]
                        reply = format_lucky_guide(d, sign)
                        metadata["type"] = "lucky"
                        metadata["source"] = "local"
                    else:
                        api_result = get_daily_horoscope_prokerala_sync(sign)
                        if api_result and "error" not in api_result:
                            reply = format_prokerala_horoscope_reply(api_result)
                            metadata["type"] = "daily_horoscope"
                            metadata["source"] = "prokerala"
                        else:
                            result = self.agent.generate_horoscope(sign)
                            reply = result["markdown_report"]
                            metadata["type"] = "full_horoscope"
                            metadata["source"] = "local_fallback"
                except Exception as e:
                    reply = f"Error: {str(e)}"
                    metadata["type"] = "error"
                    metadata["error"] = str(e)

            # If user asks about lucky number/color but NO sign provided anywhere
            elif requested_topic == "lucky" and not session["sign"] and not sign and reply is None:
                session["pending_question"] = "lucky_number"
                reply = "🍀 I'd love to tell you your lucky number and color!\n\n" \
                       "**What is your zodiac sign?** (e.g., Leo, Scorpio, Aries)\n\n" \
                       "Or tell me your **birth date** (e.g., 15/08/1990) and I'll find it for you!"
                metadata["type"] = "question_asked"
                metadata["question"] = "lucky_number"
        
        # Default welcome message
        if reply is None:
            reply = """👋 Welcome to the Daily Horoscope Agent! 🌟

I provide professional astrology readings using:
• Real planetary positions (Swiss Ephemeris)
• Transit calculations
• Vedic & Western astrology knowledge
• Comprehensive zodiac database

**How to use:**
1. Tell me your zodiac sign (e.g., "Leo", "Scorpio")
2. Or your birth date (e.g., "15/08/1990", "2004-12-12")

**Daily Horoscope Topics:**
• `love` - Romance prediction
• `career` - Work & success
• `health` - Wellness advice
• `money` - Financial outlook
• `lucky` - Lucky color, number, direction
• `compare` - Yesterday vs Today comparison

**Knowledge Questions (powered by RAG):**
• "What are Leo's traits?" - Personality & characteristics
• "Tell me about Scorpio love" - Relationship info & compatibility
• "What element is Taurus?" - Element analysis
• "What's the ruling planet of Gemini?" - Planetary influences
• "What dates for Aquarius?" - Date ranges
• "Who is compatible with Cancer?" - Best matches

**Try:** "I'm a Gemini, what's my career outlook?" or "What are Leo traits?"
"""
            metadata["type"] = "welcome"
        
        # Save chat to database
        db_manager.save_chat_message(
            session_id=session_id,
            user_message=message,
            bot_reply=reply,
            sign=sign or session.get("sign"),
            metadata=metadata
        )
        
        return reply
