import google.generativeai as genai
from app.config import settings
from app.models import ContentClassification
import logging
import hashlib
import json
from typing import Dict, Any, Tuple
import base64
from PIL import Image
import io

logger = logging.getLogger(__name__)

# Configure Google Gemini client
genai.configure(api_key=settings.google_api_key)


class GeminiService:
    def __init__(self):
        self.model = settings.gemini_model
        self.text_model = genai.GenerativeModel(settings.gemini_model)
        self.vision_model = genai.GenerativeModel('gemini-1.5-pro-latest')
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash of content for deduplication"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def analyze_text_content(self, text_content: str) -> Tuple[ContentClassification, float, str, str]:
        """
        Analyze text content using Google Gemini for moderation
        
        Returns:
            Tuple of (classification, confidence, reasoning, llm_response)
        """
        try:
            # System prompt for content moderation
            system_prompt = """You are a content moderation expert. Analyze the given text and classify it into one of these categories:
            - SAFE: Appropriate content that follows community guidelines
            - TOXIC: Content that is harmful, offensive, or promotes hate speech
            - SPAM: Unwanted promotional content or repetitive messages
            - HARASSMENT: Content that targets individuals with abuse or threats
            - INAPPROPRIATE: Content that is unsuitable for general audiences
            
            Provide your response in JSON format with:
            - classification: one of the above categories
            - confidence: confidence score (0.0 to 1.0)
            - reasoning: brief explanation for your classification
            """
            
            user_prompt = f"Please analyze this text for content moderation:\n\n{text_content}"
            
            # Combine system and user prompt for Gemini
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            response = self.text_model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent results
                    max_output_tokens=500
                )
            )
            
            # Parse the response
            llm_response = response.text
            
            try:
                # Try to parse JSON response
                parsed_response = json.loads(llm_response)
                classification = ContentClassification(parsed_response.get('classification', 'SAFE').upper())
                confidence = float(parsed_response.get('confidence', 0.5))
                reasoning = parsed_response.get('reasoning', 'No reasoning provided')
                
            except (json.JSONDecodeError, ValueError, KeyError):
                # Fallback parsing if JSON is malformed
                logger.warning(f"Failed to parse OpenAI response as JSON: {llm_response}")
                classification = ContentClassification.SAFE
                confidence = 0.5
                reasoning = "Failed to parse AI response"
            
            # Validate confidence range
            confidence = max(0.0, min(1.0, confidence))
            
            logger.info(f"Text analysis completed: {classification} (confidence: {confidence})")
            return classification, confidence, reasoning, llm_response
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            # Return safe defaults on error
            return ContentClassification.SAFE, 0.5, f"Error during analysis: {str(e)}", ""
    
    async def analyze_image_content(self, image_data: str) -> Tuple[ContentClassification, float, str, str]:
        """
        Analyze image content using Google Gemini Vision
        
        Returns:
            Tuple of (classification, confidence, reasoning, llm_response)
        """
        try:
            # System prompt for image moderation
            system_prompt = """You are an image content moderation expert. Analyze the given image and classify it into one of these categories:
            - SAFE: Appropriate image that follows community guidelines
            - TOXIC: Image that is harmful, offensive, or promotes hate speech
            - SPAM: Unwanted promotional content or repetitive images
            - HARASSMENT: Image that targets individuals with abuse or threats
            - INAPPROPRIATE: Image that is unsuitable for general audiences
            
            Provide your response in JSON format with:
            - classification: one of the above categories
            - confidence: confidence score (0.0 to 1.0)
            - reasoning: brief explanation for your classification
            """
            
            user_prompt = "Please analyze this image for content moderation."
            
            # Convert base64 to PIL Image for Gemini
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Combine system and user prompt
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            response = self.vision_model.generate_content(
                [full_prompt, image],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=500
                )
            )
            
            # Parse the response
            llm_response = response.text
            
            try:
                # Try to parse JSON response
                parsed_response = json.loads(llm_response)
                classification = ContentClassification(parsed_response.get('classification', 'SAFE').upper())
                confidence = float(parsed_response.get('confidence', 0.5))
                reasoning = parsed_response.get('reasoning', 'No reasoning provided')
                
            except (json.JSONDecodeError, ValueError, KeyError):
                # Fallback parsing if JSON is malformed
                logger.warning(f"Failed to parse OpenAI response as JSON: {llm_response}")
                classification = ContentClassification.SAFE
                confidence = 0.5
                reasoning = "Failed to parse AI response"
            
            # Validate confidence range
            confidence = max(0.0, min(1.0, confidence))
            
            logger.info(f"Image analysis completed: {classification} (confidence: {confidence})")
            return classification, confidence, reasoning, llm_response
            
        except Exception as e:
            logger.error(f"Gemini Vision API error: {e}")
            # Return safe defaults on error
            return ContentClassification.SAFE, 0.5, f"Error during analysis: {str(e)}", ""
    
    def get_content_hash(self, content: str) -> str:
        """Get content hash for deduplication"""
        return self._generate_content_hash(content)
