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
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Configure Google Gemini client
genai.configure(api_key=settings.google_api_key)


class GeminiService:
    def __init__(self):
        self.model = settings.gemini_model
        self.text_model = genai.GenerativeModel(settings.gemini_model)
        # Use the same model for both text and vision if it supports it, otherwise fallback
        try:
            self.vision_model = genai.GenerativeModel(settings.gemini_model)
        except Exception:
            # Fallback to a model that definitely supports vision
            self.vision_model = genai.GenerativeModel('gemini-1.5-pro-latest')
        self.executor = ThreadPoolExecutor(max_workers=4)
    
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
            # System prompt for content moderation with strict JSON formatting
            system_prompt = """You are a content moderation expert. Analyze the given text and classify it into one of these categories:
            - SAFE: Appropriate content that follows community guidelines
            - TOXIC: Content that is harmful, offensive, or promotes hate speech
            - SPAM: Unwanted promotional content or repetitive messages
            - HARASSMENT: Content that targets individuals with abuse or threats
            - INAPPROPRIATE: Content that is unsuitable for general audiences
            
            IMPORTANT: You must respond with ONLY valid JSON in this exact format:
            {
                "classification": "SAFE",
                "confidence": 0.8,
                "reasoning": "This content appears to be appropriate and follows community guidelines."
            }
            
            Do not include any other text, explanations, or formatting outside the JSON object.
            """
            
            user_prompt = f"Analyze this text for content moderation and respond with JSON only:\n\n{text_content}"
            
            # Combine system and user prompt for Gemini
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Run the synchronous Gemini API call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                lambda: self.text_model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,  # Low temperature for consistent results
                        max_output_tokens=300,
                        top_p=0.8
                    )
                )
            )
            
            # Parse the response
            llm_response = response.text.strip()
            
            # Log the raw response for debugging
            logger.info(f"Raw Gemini response: {llm_response}")
            
            # Clean the response - remove any markdown formatting
            if llm_response.startswith('```json'):
                llm_response = llm_response[7:]
            if llm_response.endswith('```'):
                llm_response = llm_response[:-3]
            llm_response = llm_response.strip()
            
            logger.info(f"Cleaned Gemini response: {llm_response}")
            
            try:
                # Try to parse JSON response
                parsed_response = json.loads(llm_response)
                # Convert classification to lowercase to match enum values
                classification_str = parsed_response.get('classification', 'SAFE').lower()
                classification = ContentClassification(classification_str)
                confidence = float(parsed_response.get('confidence', 0.5))
                reasoning = parsed_response.get('reasoning', 'No reasoning provided')
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                # Fallback parsing if JSON is malformed
                logger.warning(f"Failed to parse Gemini response as JSON: {llm_response}")
                logger.warning(f"JSON parsing error: {e}")
                
                # Try to extract classification from the response text
                classification = ContentClassification.SAFE
                confidence = 0.5
                reasoning = "Failed to parse AI response"
                
                # Simple fallback parsing
                if any(word in llm_response.upper() for word in ['TOXIC', 'HARMFUL', 'OFFENSIVE']):
                    classification = ContentClassification.TOXIC
                    confidence = 0.7
                    reasoning = "Detected potentially harmful content"
                elif any(word in llm_response.upper() for word in ['SPAM', 'PROMOTIONAL', 'ADVERTISING']):
                    classification = ContentClassification.SPAM
                    confidence = 0.6
                    reasoning = "Detected spam-like content"
                elif any(word in llm_response.upper() for word in ['HARASSMENT', 'ABUSE', 'THREAT']):
                    classification = ContentClassification.HARASSMENT
                    confidence = 0.7
                    reasoning = "Detected harassment or abuse"
                elif any(word in llm_response.upper() for word in ['INAPPROPRIATE', 'UNSUITABLE']):
                    classification = ContentClassification.INAPPROPRIATE
                    confidence = 0.6
                    reasoning = "Detected inappropriate content"
                else:
                    # Default to safe if no keywords found
                    classification = ContentClassification.SAFE
                    confidence = 0.8
                    reasoning = "Content appears safe based on keyword analysis"
            
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
            # System prompt for image moderation with strict JSON formatting
            system_prompt = """You are an image content moderation expert. Analyze the given image and classify it into one of these categories:
            - SAFE: Appropriate image that follows community guidelines
            - TOXIC: Image that is harmful, offensive, or promotes hate speech
            - SPAM: Unwanted promotional content or repetitive images
            - HARASSMENT: Image that targets individuals with abuse or threats
            - INAPPROPRIATE: Image that is unsuitable for general audiences
            
            IMPORTANT: You must respond with ONLY valid JSON in this exact format:
            {
                "classification": "SAFE",
                "confidence": 0.8,
                "reasoning": "This image appears to be appropriate and follows community guidelines."
            }
            
            Do not include any other text, explanations, or formatting outside the JSON object.
            """
            
            user_prompt = "Analyze this image for content moderation and respond with JSON only."
            
            # Convert base64 to PIL Image for Gemini
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Combine system and user prompt
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Run the synchronous Gemini API call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                lambda: self.vision_model.generate_content(
                    [full_prompt, image],
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=300,
                        top_p=0.8
                    )
                )
            )
            
            # Parse the response
            llm_response = response.text.strip()
            
            # Log the raw response for debugging
            logger.info(f"Raw Gemini Vision response: {llm_response}")
            
            # Clean the response - remove any markdown formatting
            if llm_response.startswith('```json'):
                llm_response = llm_response[7:]
            if llm_response.endswith('```'):
                llm_response = llm_response[:-3]
            llm_response = llm_response.strip()
            
            logger.info(f"Cleaned Gemini Vision response: {llm_response}")
            
            try:
                # Try to parse JSON response
                parsed_response = json.loads(llm_response)
                # Convert classification to lowercase to match enum values
                classification_str = parsed_response.get('classification', 'SAFE').lower()
                classification = ContentClassification(classification_str)
                confidence = float(parsed_response.get('confidence', 0.5))
                reasoning = parsed_response.get('reasoning', 'No reasoning provided')
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                # Fallback parsing if JSON is malformed
                logger.warning(f"Failed to parse Gemini response as JSON: {llm_response}")
                logger.warning(f"JSON parsing error: {e}")
                
                # Try to extract classification from the response text
                classification = ContentClassification.SAFE
                confidence = 0.5
                reasoning = "Failed to parse AI response"
                
                # Simple fallback parsing
                if any(word in llm_response.upper() for word in ['TOXIC', 'HARMFUL', 'OFFENSIVE']):
                    classification = ContentClassification.TOXIC
                    confidence = 0.7
                    reasoning = "Detected potentially harmful content"
                elif any(word in llm_response.upper() for word in ['SPAM', 'PROMOTIONAL', 'ADVERTISING']):
                    classification = ContentClassification.SPAM
                    confidence = 0.6
                    reasoning = "Detected spam-like content"
                elif any(word in llm_response.upper() for word in ['HARASSMENT', 'ABUSE', 'THREAT']):
                    classification = ContentClassification.HARASSMENT
                    confidence = 0.7
                    reasoning = "Detected harassment or abuse"
                elif any(word in llm_response.upper() for word in ['INAPPROPRIATE', 'UNSUITABLE']):
                    classification = ContentClassification.INAPPROPRIATE
                    confidence = 0.6
                    reasoning = "Detected inappropriate content"
                else:
                    # Default to safe if no keywords found
                    classification = ContentClassification.SAFE
                    confidence = 0.8
                    reasoning = "Content appears safe based on keyword analysis"
            
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
