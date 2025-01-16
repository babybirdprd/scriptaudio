import logging
import os
import glob
from datetime import datetime, date
from .config import *

class RateLimit:
	def __init__(self):
		self.requests = 0
		self.tokens = 0
		self.last_reset = datetime.now()
		self.daily_requests = 0
		self.daily_reset = date.today()
		logging.info("Rate limiter initialized")
	
	def check_and_update(self, tokens: int = 0) -> tuple[bool, str]:
		now = datetime.now()
		
		# Reset counters if minute has passed
		if (now - self.last_reset).total_seconds() >= 60:
			logging.info(f"Rate limit reset - Previous minute: {self.requests} requests, {self.tokens} tokens")
			self.requests = 0
			self.tokens = 0
			self.last_reset = now
		
		# Reset daily counter if day has changed
		if now.date() != self.daily_reset:
			logging.info(f"Daily limit reset - Previous day: {self.daily_requests} requests")
			self.daily_requests = 0
			self.daily_reset = now.date()
		
		# Check limits
		if self.requests >= RATE_LIMIT_RPM:
			logging.warning(f"Rate limit exceeded: {self.requests}/{RATE_LIMIT_RPM} RPM")
			return False, f"Rate limit exceeded: {RATE_LIMIT_RPM} requests per minute"
		if self.tokens + tokens >= RATE_LIMIT_TPM:
			logging.warning(f"Token limit exceeded: {self.tokens + tokens}/{RATE_LIMIT_TPM} TPM")
			return False, f"Token limit exceeded: {RATE_LIMIT_TPM} tokens per minute"
		if self.daily_requests >= RATE_LIMIT_RPD:
			logging.warning(f"Daily limit exceeded: {self.daily_requests}/{RATE_LIMIT_RPD} RPD")
			return False, f"Daily limit exceeded: {RATE_LIMIT_RPD} requests per day"
		
		# Update counters
		self.requests += 1
		self.tokens += tokens
		self.daily_requests += 1
		logging.info(f"API request - Minute: {self.requests}/{RATE_LIMIT_RPM}, Tokens: {self.tokens}/{RATE_LIMIT_TPM}, Day: {self.daily_requests}/{RATE_LIMIT_RPD}")
		return True, ""

def validate_text(text: str) -> tuple[bool, str]:
	"""Validate text input"""
	if not text:
		return False, STATUS_MESSAGES["error_no_audio"]
	
	word_count = len(text.split())
	if word_count > MAX_WORDS:
		return False, f"Text too long ({word_count} words). Please limit to {MAX_WORDS} words."
	if word_count < MIN_WORDS:
		return False, f"Text too short ({word_count} words). Please provide at least {MIN_WORDS} words."
	
	return True, ""

def validate_batch_size(size: int) -> tuple[bool, str]:
	"""Validate batch size"""
	if size < 1:
		return False, "Batch size must be at least 1"
	if size > MAX_BATCH_SIZE:
		return False, f"Batch size too large. Maximum is {MAX_BATCH_SIZE} items."
	return True, ""

def ensure_venv():
	"""Ensure running in virtual environment"""
	if not os.environ.get('VIRTUAL_ENV'):
		print("WARNING: Not running in a virtual environment. Please activate the venv first.")
		print("Run: venv\\Scripts\\activate")
		exit(1)

def list_generated_files():
	"""List all generated audio files"""
	output_dir = 'generated_audio'
	if not os.path.exists(output_dir):
		return "No files generated yet"
	
	files = glob.glob(os.path.join(output_dir, '*.wav'))
	if not files:
		return "No audio files found"
	
	return "\n".join([os.path.basename(f) for f in sorted(files)])