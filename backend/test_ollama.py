#!/usr/bin/env python3

import os
import sys
import logging
import argparse
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_ollama.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Make sure environment variables are loaded
load_dotenv()

def test_ollama_client():
    """Test the Ollama client directly"""
    logger.info("Testing Ollama client...")
    
    try:
        from app.summarizer.ollama_client import ollama_client
        
        # Test health check
        logger.info("Testing Ollama health check...")
        health = ollama_client.health_check()
        if health:
            logger.info("✅ Ollama is available")
        else:
            logger.error("❌ Ollama is not available")
            return False
        
        # Test text generation
        logger.info("Testing Ollama text generation...")
        prompt = "Hello, I am testing the Ollama API. Please respond with a short greeting."
        response = ollama_client.generate(prompt, max_tokens=50)
        
        if response:
            logger.info(f"✅ Ollama responded: {response}")
        else:
            logger.error("❌ Ollama text generation failed")
            return False
        
        # Test summarization
        logger.info("Testing Ollama summarization...")
        text = """
        Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to the natural 
        intelligence displayed by humans or animals. The term "artificial intelligence" is often used to 
        describe machines (or computers) that mimic cognitive functions that humans associate with 
        the human mind, such as learning and problem solving.
        
        As machines become increasingly capable, tasks considered to require "intelligence" are often 
        removed from the definition of AI, a phenomenon known as the AI effect. For instance, optical 
        character recognition is frequently excluded from things considered to be AI, having become 
        a routine technology.
        
        Modern machine capabilities generally classified as AI include successfully understanding 
        human speech, competing at the highest level in strategic game systems, autonomously 
        operating cars, intelligent routing in content delivery networks, and military simulations.
        """
        
        summary = ollama_client.summarize(text)
        if summary:
            logger.info(f"✅ Ollama summarized text: {summary}")
        else:
            logger.error("❌ Ollama summarization failed")
            return False
        
        logger.info("All Ollama client tests passed!")
        return True
    
    except Exception as e:
        logger.error(f"Error testing Ollama client: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_summarizer_with_ollama():
    """Test the summarizer module with Ollama integration"""
    logger.info("Testing summarizer with Ollama integration...")
    
    try:
        from app.summarizer.processor import summarize_text_enhanced
        
        # Test text to summarize
        text = """
        Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to the natural 
        intelligence displayed by humans or animals. The term "artificial intelligence" is often used to 
        describe machines (or computers) that mimic cognitive functions that humans associate with 
        the human mind, such as learning and problem solving.
        
        As machines become increasingly capable, tasks considered to require "intelligence" are often 
        removed from the definition of AI, a phenomenon known as the AI effect. For instance, optical 
        character recognition is frequently excluded from things considered to be AI, having become 
        a routine technology.
        
        Modern machine capabilities generally classified as AI include successfully understanding 
        human speech, competing at the highest level in strategic game systems, autonomously 
        operating cars, intelligent routing in content delivery networks, and military simulations.
        """
        
        # Test different summarization options
        options = [
            {"length": "short"},
            {"length": "medium"},
            {"length": "long"},
            {"focus": ["key_points"]},
            {"format": "bullets"}
        ]
        
        for option in options:
            logger.info(f"Testing summarization with options: {option}")
            summary = summarize_text_enhanced(text, option)
            if summary:
                logger.info(f"✅ Summary with options {option}: {summary[:100]}...")
            else:
                logger.error(f"❌ Summarization failed with options {option}")
                return False
        
        logger.info("All summarizer tests passed!")
        return True
    
    except Exception as e:
        logger.error(f"Error testing summarizer: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to run the tests"""
    parser = argparse.ArgumentParser(description="Test Ollama integration")
    parser.add_argument("--client-only", action="store_true", help="Test only the Ollama client")
    parser.add_argument("--summarizer-only", action="store_true", help="Test only the summarizer with Ollama")
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("OLLAMA INTEGRATION TEST")
    print("="*80 + "\n")
    
    success = True
    
    # Test based on arguments
    if args.client_only:
        success = test_ollama_client()
    elif args.summarizer_only:
        success = test_summarizer_with_ollama()
    else:
        # Run all tests
        client_success = test_ollama_client()
        summarizer_success = test_summarizer_with_ollama()
        success = client_success and summarizer_success
    
    print("\n" + "="*80)
    if success:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ TESTS FAILED")
    print("="*80 + "\n")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 