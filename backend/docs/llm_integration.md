# LLM Integration Documentation

This document provides reference information and best practices for integrating Ollama and DeepSeek models into the SecureVideoSummarizer application.

## Ollama

[Ollama](https://ollama.ai/) is an open-source framework for running large language models locally. It simplifies the process of running, managing, and using various open-source LLMs.

### Installation & Setup

1. Install Ollama:
   - macOS: `curl -fsSL https://ollama.com/install.sh | sh`
   - Linux: `curl -fsSL https://ollama.com/install.sh | sh`
   - Windows: Download from [https://ollama.com/download](https://ollama.com/download)

2. Start Ollama service:
   ```
   ollama serve
   ```

3. Pull required models:
   ```
   # For DeepSeek-R1
   ollama pull deepseek-r1
   
   # Alternative smaller models
   ollama pull llama2:7b
   ollama pull mistral:7b
   ollama pull phi:latest
   ```

### API Reference

Ollama provides a REST API running at `http://localhost:11434/api` by default.

#### Key API Endpoints:

1. **Generate Text**:
   ```
   POST /api/generate
   {
     "model": "llama2:7b",
     "prompt": "Summarize the following text: ...",
     "system": "You are a helpful assistant that summarizes content.",
     "stream": false,
     "options": {
       "temperature": 0.7,
       "top_p": 0.9,
       "max_tokens": 2048
     }
   }
   ```

2. **Check Model Status**:
   ```
   POST /api/show
   {
     "name": "llama2:7b"
   }
   ```

3. **List Available Models**:
   ```
   GET /api/tags
   ```

### Best Practices for Ollama Integration

1. **Health Checks**: Always perform a health check before sending requests to ensure the service and model are available.

2. **Error Handling**: Implement robust error handling for network issues, timeouts, and model-specific errors.

3. **Rate Limiting**: Apply local rate limiting to prevent overloading the Ollama service.

4. **Prompt Engineering**: Use well-structured prompts with clear instructions:
   ```
   system: "You are an AI assistant that summarizes videos. Create a concise summary."
   prompt: "Summarize the following transcript of a lecture on AI: [TRANSCRIPT]"
   ```

5. **Model Selection**: Use the appropriate model size based on the complexity of the task:
   - Small models (7B parameters) for simple summaries
   - Larger models for more complex analysis
   - Specialized models when available (e.g., coding-specific models)

6. **Parameter Tuning**:
   - Lower temperature (0.1-0.4) for factual, concise summaries
   - Higher max_tokens for comprehensive summaries
   - Consider adjusting top_p, top_k for different generation styles

## DeepSeek

[DeepSeek](https://github.com/deepseek-ai/DeepSeek-R1) is a powerful open-source language model optimized for various tasks including summarization and reasoning.

### Official Resources

- GitHub Repository: [https://github.com/deepseek-ai/DeepSeek-R1](https://github.com/deepseek-ai/DeepSeek-R1)
- Documentation: [https://github.com/deepseek-ai/DeepSeek-R1/blob/main/README.md](https://github.com/deepseek-ai/DeepSeek-R1/blob/main/README.md)
- Model Card: [https://huggingface.co/deepseek-ai/deepseek-r1](https://huggingface.co/deepseek-ai/deepseek-r1)

### DeepSeek-R1 Model Variants

1. **DeepSeek-R1-ZH** - Optimized for Chinese content
2. **DeepSeek-R1-EN** - Optimized for English content
3. **DeepSeek-R1** - Base model with multilingual capability

### Best Practices for DeepSeek Integration

1. **Prompt Format**: DeepSeek models respond well to this format:
   ```
   <|im_start|>system
   You are an AI assistant that summarizes videos.
   <|im_end|>
   <|im_start|>user
   Summarize the following transcript: [TRANSCRIPT]
   <|im_end|>
   <|im_start|>assistant
   ```

2. **Context Window**: DeepSeek models have a large context window (up to 8K tokens), which is ideal for processing long video transcripts.

3. **Parameters for Summarization**:
   - temperature: 0.1-0.3 (for factual summaries)
   - top_p: 0.9
   - repetition_penalty: 1.1 (prevents redundant content in summaries)

4. **Resource Requirements**:
   - DeepSeek-R1: Requires 16GB+ VRAM for full model
   - Using 8-bit quantization can reduce this to ~8GB
   - For CPU-only, expect slower performance

## Integration Architecture in SecureVideoSummarizer

Our application uses a layered approach to LLM integration:

1. **Primary Layer**: Ollama API client for local model inference
2. **Fallback Layer**: Direct model loading via Transformers library
3. **Final Fallback**: Simple extractive summarization for when LLMs are unavailable

### Configuration

Update `.env` with appropriate settings:
```
OLLAMA_API_URL=http://localhost:11434/api
OLLAMA_MODEL=llama2:7b  # Or deepseek-r1 when available
OLLAMA_TIMEOUT=60
OLLAMA_MAX_TOKENS=2048
OLLAMA_CONTEXT_SIZE=8192
```

### Troubleshooting

1. **Model Not Found**:
   - Run `ollama list` to see available models
   - Pull the required model: `ollama pull MODEL_NAME`

2. **Performance Issues**:
   - Check system resources (CPU, RAM, GPU usage)
   - Consider using a smaller model
   - Try increasing timeout values

3. **Quality Issues**:
   - Adjust temperature and other generation parameters
   - Experiment with different system prompts
   - Consider chunking long transcripts

## References

- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Ollama Model Library](https://ollama.ai/library)
- [DeepSeek-R1 Paper](https://arxiv.org/abs/2404.01523)
- [HuggingFace Transformers Documentation](https://huggingface.co/docs/transformers/index) 