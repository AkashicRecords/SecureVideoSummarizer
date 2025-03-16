#!/usr/bin/env python3

import os
import sys
import logging
import argparse
import time
from dotenv import load_dotenv
from transformers import AutoModel, AutoTokenizer
from transformers import pipeline

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_deepseek.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Make sure environment variables are loaded
load_dotenv()

# Temporarily set the environment variable for the test
os.environ['OLLAMA_MODEL'] = 'deepseek-r1:1.5b'

def test_deepseek_availability():
    """Test if Deepseek R1 is available in Ollama"""
    logger.info("Testing Deepseek R1 availability in Ollama")
    
    try:
        from app.summarizer.ollama_client import ollama_client
        
        # Test health check
        logger.info("Checking if Ollama server and Deepseek R1 model are available...")
        health = ollama_client.health_check()
        
        if health:
            logger.info("✅ Ollama server and Deepseek R1 are available")
            return True
        else:
            logger.error("❌ Ollama server or Deepseek R1 model not available")
            logger.info("To install Deepseek R1, run: ollama pull deepseek-r1:1.5b")
            return False
    
    except Exception as e:
        logger.error(f"Error checking Deepseek R1 availability: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_token_handling():
    """Test token handling with Deepseek R1"""
    logger.info("Testing token handling with Deepseek R1")
    
    try:
        from app.summarizer.ollama_client import ollama_client
        
        # Create a test prompt with varying length
        texts = [
            # Short text (few tokens)
            "Summarize artificial intelligence.",
            
            # Medium text (moderate tokens)
            """
            Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to the natural 
            intelligence displayed by humans or animals. The term "artificial intelligence" is often used to 
            describe machines (or computers) that mimic cognitive functions that humans associate with 
            the human mind, such as learning and problem solving.
            """,
            
            # Long text (many tokens)
            """
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
            
            The field was founded on the assumption that human intelligence can be precisely described 
            in a way that a machine can simulate it. This raised philosophical arguments about the mind and
            ethical questions about creating artificial beings endowed with human-like intelligence.
            """
        ]
        
        # Test with different token lengths
        for i, text in enumerate(texts):
            print(f"\n{'='*80}")
            print(f"TEST {i+1}: TESTING WITH {len(text.split())} WORDS")
            print(f"{'='*80}")
            print(f"INPUT TEXT: {text[:100]}...")
            
            # Create a system prompt
            system_prompt = "You are a helpful assistant that summarizes text concisely."
            
            # Start timing
            start_time = time.time()
            
            # Generate response
            response = ollama_client.generate(
                prompt=f"Summarize this text: {text}",
                system_prompt=system_prompt,
                max_tokens=100 * (i + 1),  # Increase max tokens for longer texts
                temperature=0.3
            )
            
            # End timing
            elapsed = time.time() - start_time
            
            if response:
                word_count = len(response.split())
                char_count = len(response)
                logger.info(f"✅ Response generated in {elapsed:.2f}s: {word_count} words, {char_count} chars")
                
                # Print the full response to stdout
                print(f"\nRESPONSE ({word_count} words, generated in {elapsed:.2f}s):")
                print(f"{'-'*80}")
                print(response)
                print(f"{'-'*80}")
                
                logger.info(f"Sample: {response[:100]}...")
            else:
                logger.error(f"❌ Failed to generate response for test {i+1}")
                print(f"\nFAILED TO GENERATE RESPONSE")
                return False
        
        logger.info("All token handling tests passed!")
        return True
    
    except Exception as e:
        logger.error(f"Error testing token handling: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_summarization():
    """Test summarization with Deepseek R1"""
    logger.info("Testing summarization with Deepseek R1")
    
    try:
        from app.summarizer.ollama_client import ollama_client
        
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
        
        print(f"\n{'='*80}")
        print(f"SUMMARIZATION TEST TEXT ({len(text.split())} words):")
        print(f"{'='*80}")
        print(text)
        
        # Test summarization with different length settings
        for length, min_words, max_words in [
            ("short", 30, 50),
            ("medium", 80, 120),
            ("long", 150, 200)
        ]:
            print(f"\n{'='*80}")
            print(f"TESTING {length.upper()} SUMMARIZATION ({min_words}-{max_words} words)")
            print(f"{'='*80}")
            
            # Start timing
            start_time = time.time()
            
            # Generate summary
            summary = ollama_client.summarize(text, max_length=max_words, min_length=min_words)
            
            # End timing
            elapsed = time.time() - start_time
            
            if summary:
                word_count = len(summary.split())
                is_within_range = min_words <= word_count <= max_words * 1.2  # Allow 20% over max
                
                if is_within_range:
                    logger.info(f"✅ {length.capitalize()} summary generated in {elapsed:.2f}s: {word_count} words")
                    print(f"\nSUMMARY RESULT ({word_count} words, generated in {elapsed:.2f}s):")
                else:
                    logger.warning(f"⚠️ {length.capitalize()} summary has {word_count} words (expected {min_words}-{max_words})")
                    print(f"\nSUMMARY RESULT ({word_count} words - OUTSIDE TARGET RANGE, generated in {elapsed:.2f}s):")
                
                print(f"{'-'*80}")
                print(summary)
                print(f"{'-'*80}")
                
                logger.info(f"Summary: {summary[:150]}...")
            else:
                logger.error(f"❌ Failed to generate {length} summary")
                print(f"\nFAILED TO GENERATE {length.upper()} SUMMARY")
                return False
        
        logger.info("All summarization tests passed!")
        return True
    
    except Exception as e:
        logger.error(f"Error testing summarization: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to run the tests"""
    parser = argparse.ArgumentParser(description="Test Deepseek R1 integration")
    parser.add_argument("--availability", action="store_true", help="Test only the Deepseek R1 availability")
    parser.add_argument("--tokens", action="store_true", help="Test only token handling")
    parser.add_argument("--summarization", action="store_true", help="Test only summarization")
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("DEEPSEEK R1 INTEGRATION TEST")
    print("="*80 + "\n")
    
    success = True
    
    # Test based on arguments
    if args.availability:
        success = test_deepseek_availability()
    elif args.tokens:
        success = test_token_handling()
    elif args.summarization:
        success = test_summarization()
    else:
        # Run all tests
        avail_success = test_deepseek_availability()
        if avail_success:
            token_success = test_token_handling()
            summ_success = test_summarization()
            success = token_success and summ_success
        else:
            success = False
    
    print("\n" + "="*80)
    if success:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ TESTS FAILED")
    print("="*80 + "\n")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

# Option 1: Direct model loading - skip this for now as it's not working 
# model = AutoModel.from_pretrained("deepseek-ai/DeepSeek-R1", trust_remote_code=True)

# Option 2: Try different pipeline task type - skip this for now as it's not working
# summarizer = pipeline("text-generation", model="deepseek-ai/DeepSeek-R1", trust_remote_code=True) 