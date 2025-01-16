# Configuration constants
MODEL = 'models/gemini-2.0-flash-exp'
HOST = 'generativelanguage.googleapis.com'

# Audio configuration
WAVE_CHANNELS = 1  # Mono audio
WAVE_RATE = 24000  # 24kHz output
WAVE_SAMPLE_WIDTH = 2  # 16-bit PCM
INPUT_SAMPLE_RATE = 16000  # 16kHz for input
ALIGNMENT_THRESHOLD = 0.8  # Minimum acceptable alignment score
CHUNK_SIZE = 1024  # Audio buffer size

# API limits
MAX_BATCH_SIZE = 100
MAX_INPUT_TOKENS = 1048576
MAX_OUTPUT_TOKENS = 8192
RATE_LIMIT_RPM = 10
RATE_LIMIT_TPM = 4000000
RATE_LIMIT_RPD = 1500

# Validation constants
MAX_WORDS = 200
MIN_WORDS = 10

# Content options
VOICES = ["Aoede", "Charon", "Fenrir", "Kore", "Puck"]
CATEGORIES = [
	"Tech Review", "Gaming", "Cooking", "Vlog", "Comedy", "DIY", "Travel",
	"Educational", "Music", "Product Review", "Fitness", "Book Review",
	"Movie Analysis", "Interview", "Science", "Art Tutorial", "Life Advice",
	"Personal Story", "Podcast", "Photography", "Fashion", "Health", "Meditation",
	"Language Learning", "Home Improvement", "Pet Care", "Car Review"
]
STYLES = ["energetic and enthusiastic", "calm and informative", "humorous and entertaining",
		  "professional and detailed", "casual and friendly", "inspirational and motivating"]

CONTENT_TYPES = [
	"Blog Post", "Product Review", "Tutorial", "Story", "News Article",
	"Educational Content", "Interview", "Podcast Script"
]

NICHES = [
	"Technology", "Gaming", "Health & Fitness", "Business", "Education",
	"Entertainment", "Science", "Lifestyle", "Travel", "Food & Cooking",
	"Sports", "Arts & Culture"
]

VOICE_DESCRIPTIONS = {
	"Aoede": "Warm and engaging - perfect for storytelling and personal content",
	"Charon": "Deep and authoritative - ideal for educational and serious topics",
	"Fenrir": "Energetic and dynamic - great for gaming and action content",
	"Kore": "Clear and professional - suited for tutorials and reviews",
	"Puck": "Friendly and conversational - best for vlogs and casual content"
}

TONE_PRESETS = {
	"Default": "TONE: READ TEXT EXACTLY AS WRITTEN, VERBATIM, WITHOUT ANY COMMENTARY OR RESPONSE",
	"Professional": "TONE: READ TEXT VERBATIM WITH PROFESSIONAL CLARITY AND ENUNCIATION, NO COMMENTARY",
	"Casual": "TONE: READ TEXT WORD FOR WORD WITH NATURAL PACING, NO ADDED CONVERSATION",
	"Custom": "Enter your own tone instruction"
}

# Status messages
STATUS_MESSAGES = {
	"connecting": "Connecting to Gemini API...",
	"generating": "Generating audio...",
	"saving": "Saving audio file...",
	"complete": "Audio generation complete",
	"error_api_key": "Invalid API key. Please check your API key and try again.",
	"error_rate_limit": "API rate limit exceeded. Please wait a moment and try again.",
	"error_session_limit": f"Maximum concurrent sessions (3) reached",
	"error_token_limit": f"Token rate limit (4,000,000/min) exceeded",
	"error_duration": "Session duration limit exceeded (15 minutes)",
	"error_no_audio": "No audio data received",
	"error_alignment": "Low audio quality detected (alignment score below threshold)",
	"error_rate_limit": "API rate limit exceeded. Please try again in a minute.",
	"error_token_limit": "Token limit exceeded. Please try with shorter text.",
	"error_daily_limit": "Daily request limit reached. Please try again tomorrow.",
	"error_batch_limit": f"Batch size exceeds limit of {MAX_BATCH_SIZE} items.",
	"error_session_timeout": "Session timeout after 15 minutes. Please start a new session."
}