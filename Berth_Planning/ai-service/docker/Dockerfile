# NVIDIA Nemotron Nano 9B v2 Docker Container
# Uses vLLM for optimized inference with support for hybrid architectures

FROM vllm/vllm-openai:latest

# Set environment variables
ENV HF_HOME=/app/hf_cache
ENV VLLM_ALLOW_RUNTIME_LORA_UPDATING=True

# Expose the API port (vLLM default)
EXPOSE 8000

# Run vLLM with Nemotron model
# Using 4-bit quantization for 8GB VRAM GPUs
CMD ["--model", "nvidia/NVIDIA-Nemotron-Nano-9B-v2", \
     "--trust-remote-code", \
     "--dtype", "float16", \
     "--max-model-len", "8192", \
     "--gpu-memory-utilization", "0.9", \
     "--quantization", "bitsandbytes", \
     "--load-format", "bitsandbytes"]
