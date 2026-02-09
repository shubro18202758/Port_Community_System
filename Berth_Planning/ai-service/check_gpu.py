"""
GPU/CUDA System Check and Configuration
"""
import torch
import os
import sys

print('='*70)
print('GPU/CUDA SYSTEM CHECK')
print('='*70)

print(f'\nPython: {sys.version}')
print(f'PyTorch Version: {torch.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')

if torch.cuda.is_available():
    print(f'CUDA Version: {torch.version.cuda}')
    print(f'cuDNN Version: {torch.backends.cudnn.version()}')
    print(f'GPU Count: {torch.cuda.device_count()}')
    
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print(f'\nGPU {i}: {props.name}')
        print(f'  Memory: {props.total_memory / 1024**3:.1f} GB')
        print(f'  Compute Capability: {props.major}.{props.minor}')
        print(f'  Multi Processors: {props.multi_processor_count}')
    
    # Current memory status
    print(f'\nCurrent GPU Memory:')
    print(f'  Allocated: {torch.cuda.memory_allocated() / 1024**2:.1f} MB')
    print(f'  Cached: {torch.cuda.memory_reserved() / 1024**2:.1f} MB')
    
    # Set default device
    torch.set_default_device('cuda')
    print('\n✓ Set default PyTorch device to CUDA')
else:
    print('\n⚠ No CUDA GPU available - will use CPU')

# Check environment
cuda_devices = os.environ.get('CUDA_VISIBLE_DEVICES', 'not set')
print(f'\nCUDA_VISIBLE_DEVICES: {cuda_devices}')

# Test tensor operation
print('\nTesting GPU computation...')
if torch.cuda.is_available():
    x = torch.randn(1000, 1000, device='cuda')
    y = torch.randn(1000, 1000, device='cuda')
    
    import time
    start = time.time()
    for _ in range(100):
        z = torch.mm(x, y)
    torch.cuda.synchronize()
    gpu_time = time.time() - start
    print(f'  GPU: 100x matrix multiply (1000x1000): {gpu_time*1000:.1f}ms')
    
    x_cpu = x.cpu()
    y_cpu = y.cpu()
    start = time.time()
    for _ in range(100):
        z_cpu = torch.mm(x_cpu, y_cpu)
    cpu_time = time.time() - start
    print(f'  CPU: 100x matrix multiply (1000x1000): {cpu_time*1000:.1f}ms')
    print(f'  Speedup: {cpu_time/gpu_time:.1f}x')

print('\n' + '='*70)
