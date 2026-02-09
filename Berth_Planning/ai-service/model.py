"""
SmartBerth AI Service - LLM Model Loader
Uses Anthropic Claude API for cloud-based AI inference
Provides intelligent berth planning assistance with state-of-the-art language understanding
"""

import logging
from typing import Optional, Dict, Any, List, Generator
from config import get_settings

logger = logging.getLogger(__name__)

# Try to import Anthropic SDK
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic SDK not available. Run: pip install anthropic")

# SmartBerth System Prompt - Domain-specific for port berth planning
SMARTBERTH_SYSTEM_PROMPT = """You are SmartBerth AI, an intelligent assistant specialized in port berth planning and resource optimization for JNPT (Jawaharlal Nehru Port Trust), India's largest container port.

Your expertise includes:
- Berth allocation optimization considering vessel specifications (LOA, beam, draft, DWT)
- Tide and weather impact analysis for safe berthing operations
- Resource scheduling (cranes, pilots, tugs, forklifts)
- Conflict detection and resolution in berth schedules
- ETA prediction and delay analysis
- Terminal efficiency optimization
- UKC (Under Keel Clearance) safety calculations

When analyzing berth planning scenarios:
1. Consider hard constraints: vessel dimensions vs berth capacity, tide windows, weather limits
2. Apply soft constraints: minimize waiting time, maximize berth utilization, prioritize by cargo priority
3. Check resource availability: cranes, pilots, tugs for each operation phase
4. Evaluate safety factors: weather conditions, tide levels, night operations restrictions

JNPT Port Details:
- Location: 18.9388°N, 72.8354°E
- Terminals: JNPT Container Terminal, NSICT, GTI, BMCT, NSIGT
- Approach Channel: 14.5m depth, max 400m LOA vessels
- Tidal Range: ~5m (requires tidal window planning for deep-draft vessels)

Provide structured, actionable recommendations with clear reasoning. Use data-driven analysis when vessel/berth data is provided. Be concise and professional."""


class SmartBerthLLM:
    """
    LLM Model wrapper using Anthropic Claude API.
    Provides cloud-based AI inference for berth planning reasoning tasks.
    """
    
    _instance: Optional["SmartBerthLLM"] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Singleton pattern to ensure only one model instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.settings = get_settings()
        self.client: Optional[Any] = None
        self._model_loaded = False
        self._initialized = True
    
    @property
    def model(self) -> Optional[Any]:
        """Property alias for client to support legacy code checking model.model"""
        return self.client if self._model_loaded else None
        
    def initialize(self) -> bool:
        """
        Initialize the Anthropic Claude API client.
        Returns True if successful, False otherwise.
        """
        if not ANTHROPIC_AVAILABLE:
            logger.error("Anthropic SDK not installed. Run: pip install anthropic")
            return False
            
        try:
            logger.info("Initializing Anthropic Claude API client...")
            logger.info(f"Using model: {self.settings.claude_model}")
            
            # Create Anthropic client
            self.client = anthropic.Anthropic(
                api_key=self.settings.anthropic_api_key
            )
            
            # Test connection with a minimal request
            try:
                test_response = self.client.messages.create(
                    model=self.settings.claude_model,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Hi"}]
                )
                self._model_loaded = True
                logger.info("✅ Anthropic Claude API connection successful!")
                logger.info(f"Model: {self.settings.claude_model} ready for inference")
                return True
            except Exception as e:
                if "401" in str(e) or "authentication" in str(e).lower():
                    logger.error("❌ Claude API authentication failed. Check your API key.")
                    return False
                elif "429" in str(e) or "rate" in str(e).lower():
                    logger.warning("⚠️ Rate limited, but connection works. Proceeding...")
                    self._model_loaded = True
                    return True
                else:
                    logger.error(f"Claude API test failed: {e}")
                    return False
            
        except Exception as e:
            logger.error(f"Failed to initialize Claude client: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate text response using Claude API.
        
        Args:
            prompt: User's input prompt
            system_prompt: Optional system context (uses SmartBerth default if None)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter (not used by Claude)
            
        Returns:
            Dictionary with generated text and metadata
        """
        if self.client is None:
            raise RuntimeError("Model not initialized. Call initialize() first.")
        
        # Use defaults from settings if not provided
        max_tokens = max_tokens or self.settings.max_new_tokens
        temperature = temperature or self.settings.temperature
        
        # Use SmartBerth system prompt if not provided
        if system_prompt is None:
            system_prompt = SMARTBERTH_SYSTEM_PROMPT
        
        try:
            # Generate using Anthropic Claude API
            response = self.client.messages.create(
                model=self.settings.claude_model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract generated text
            generated_text = ""
            if response.content:
                generated_text = response.content[0].text
            
            return {
                "success": True,
                "text": generated_text,
                "tokens_generated": response.usage.output_tokens if response.usage else 0,
                "tokens_prompt": response.usage.input_tokens if response.usage else 0,
                "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0,
                "model": self.settings.claude_model,
                "stop_reason": response.stop_reason,
            }
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                logger.warning(f"Rate limited: {e}")
                return {
                    "success": False,
                    "error": "Rate limited. Please wait and try again.",
                    "text": "",
                }
            logger.error(f"Claude API error: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
            }
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Generator[str, None, None]:
        """
        Stream text generation for real-time responses.
        
        Yields:
            Chunks of generated text
        """
        if self.client is None:
            raise RuntimeError("Model not initialized. Call initialize() first.")
        
        max_tokens = max_tokens or self.settings.max_new_tokens
        temperature = temperature or self.settings.temperature
        
        if system_prompt is None:
            system_prompt = SMARTBERTH_SYSTEM_PROMPT
        
        # Stream generation using Claude API
        with self.client.messages.stream(
            model=self.settings.claude_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield text
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and status"""
        if self.client is None or not self._model_loaded:
            return {
                "status": "not_loaded",
                "model_name": self.settings.claude_model,
                "provider": "Anthropic Claude",
            }
        
        return {
            "status": "loaded",
            "model_name": self.settings.claude_model,
            "model_type": "Anthropic Claude API",
            "provider": "Anthropic",
            "context_window": 200000,  # Claude's context window
            "max_output_tokens": self.settings.max_new_tokens,
        }
    
    def cleanup(self):
        """Release resources"""
        if self.client is not None:
            self.client = None
            self._model_loaded = False
        logger.info("Claude client disconnected")


# Global model instance
smartberth_llm = SmartBerthLLM()


def get_model() -> SmartBerthLLM:
    """Get the global SmartBerth LLM instance"""
    return smartberth_llm
