"""
Ollama API client for text generation and summarization with Deepseek R1.
"""
import os
import json
import logging
import requests
import time
from app.config import get_config

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama API, optimized for DeepSeek R1"""
    
    def __init__(self):
        """Initialize the Ollama client with configuration"""
        config = get_config()
        self.api_url = config.OLLAMA_API_URL
        self.model = config.OLLAMA_MODEL
        self.timeout = config.OLLAMA_TIMEOUT
        self.max_tokens = config.OLLAMA_MAX_TOKENS
        self.context_size = config.OLLAMA_CONTEXT_SIZE
        logger.debug(f"Initialized Ollama client with URL: {self.api_url}, model: {self.model}")
        logger.debug(f"Token settings: max_tokens={self.max_tokens}, context_size={self.context_size}")
        
    def health_check(self):
        """Check if Ollama is available"""
        try:
            # First check if the main server is running
            base_url = self.api_url.split('/api')[0]
            response = requests.get(f"{base_url}", timeout=5)
            
            if response.status_code != 200:
                logger.error(f"Ollama server not available: Status {response.status_code}")
                return False
                
            # Then check if the model is available
            model_url = f"{self.api_url}/show"
            model_response = requests.post(
                model_url,
                json={"name": self.model},
                timeout=5
            )
            
            if model_response.status_code != 200:
                logger.warning(f"Model {self.model} not loaded: Status {model_response.status_code}")
                logger.warning("You may need to run: ollama pull deepseek-r1")
                return False
                
            logger.info(f"Ollama server and model {self.model} are available")
            return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            return False
            
    def _call_ollama_api(self, endpoint, data):
        """Make a request to the Ollama API with proper timeout handling"""
        url = f"{self.api_url}/{endpoint}"
        logger.debug(f"Calling Ollama API: {url}")
        
        try:
            start_time = time.time()
            response = requests.post(
                url,
                json=data,
                timeout=self.timeout
            )
            elapsed = time.time() - start_time
            logger.debug(f"Ollama API call completed in {elapsed:.2f}s")
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code} {response.text}")
                return None
                
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"Ollama API timeout after {self.timeout}s")
            return None
        except Exception as e:
            logger.error(f"Ollama API call failed: {str(e)}")
            return None
            
    def generate(self, prompt, system_prompt=None, max_tokens=None, temperature=0.7):
        """
        Generate text using Ollama with Deepseek R1 optimizations
        
        Args:
            prompt: The user prompt to send to the model
            system_prompt: Optional system prompt to guide the model's behavior
            max_tokens: Maximum tokens to generate (uses config default if None)
            temperature: Controls randomness in generation (0.0-1.0)
            
        Returns:
            Generated text or None if generation failed
        """
        # Use default max_tokens from config if not specified
        if max_tokens is None:
            max_tokens = self.max_tokens
            
        # Prepare the request data
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "top_k": 40,                # Optimal for Deepseek R1
                "top_p": 0.9,               # Good for coherent summaries
                "repeat_penalty": 1.1,      # Helps avoid repetition
                "num_ctx": self.context_size
            }
        }
        
        # Add system prompt if provided
        if system_prompt:
            data["system"] = system_prompt
            
        token_estimate = len(prompt.split()) * 1.3  # Rough token estimate
        logger.debug(f"Generating with Ollama, approximate input tokens: {int(token_estimate)}")
        logger.debug(f"Max output tokens: {max_tokens}")
        
        # Make the API call
        result = self._call_ollama_api("generate", data)
        
        if result and "response" in result:
            # Log token usage if available
            if "eval_count" in result:
                logger.debug(f"Tokens used: {result['eval_count']}")
            if "prompt_eval_count" in result:
                logger.debug(f"Prompt tokens: {result['prompt_eval_count']}")
                
            return result["response"]
            
        return None
        
    def summarize(self, text, max_length=150, min_length=50):
        """
        Summarize text using Ollama with Deepseek R1 optimizations
        
        Args:
            text: The text to summarize
            max_length: Maximum word count for the summary
            min_length: Minimum word count for the summary
            
        Returns:
            Summarized text or None if summarization failed
        """
        # System prompt optimized for Deepseek R1
        system_prompt = """You are an expert summarization assistant. Your task is to create clear, 
concise, and informative summaries of text while preserving the key information and main points. 
Focus on extracting the most important concepts, facts, and arguments. Your summary should be 
well-structured and coherent, maintaining the original meaning without adding new information 
or personal opinions."""
        
        # User prompt with the text to summarize
        prompt = f"""Please provide a summary of the following text. 
The summary should be between {min_length} and {max_length} words, highlighting the key points and main ideas.

TEXT TO SUMMARIZE:
{text}

SUMMARY:"""
        
        logger.info(f"Summarizing text with Ollama (length: {len(text)} chars, approx {len(text.split())} words)")
        
        # Calculate appropriate max_tokens based on max_length
        # Deepseek R1 tends to generate more words per token than some other models
        tokens_per_word = 0.6  # Conservative estimate for Deepseek R1
        estimated_max_tokens = int(max_length / tokens_per_word) + 50  # Add buffer
        
        # Generate summary with optimized parameters
        summary = self.generate(
            prompt=prompt, 
            system_prompt=system_prompt,
            max_tokens=min(estimated_max_tokens, self.max_tokens),  # Don't exceed config max
            temperature=0.3  # Lower temperature for more focused summaries
        )
        
        if not summary:
            logger.error("Failed to generate summary with Ollama")
            return None
            
        # Clean up the summary (remove any potential formatting artifacts)
        summary = summary.strip()
        
        # Log summary stats
        logger.debug(f"Generated summary with {len(summary.split())} words ({len(summary)} chars)")
        return summary

# Create a singleton instance
ollama_client = OllamaClient()
