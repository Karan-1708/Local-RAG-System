import torch
import platform
import subprocess

def check_gpu():
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"PyTorch version: {torch.__version__}")
    
    cuda_available = torch.cuda.is_available()
    print(f"CUDA available: {cuda_available}")
    
    if cuda_available:
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
            print(f"  Capability: {torch.cuda.get_device_capability(i)}")
    else:
        print("CUDA is NOT available. PyTorch is running on CPU.")
        # Check if NVIDIA drivers are present
        try:
            smi = subprocess.check_output(['nvidia-smi']).decode('utf-8')
            print("NVIDIA drivers found (nvidia-smi works), but PyTorch isn't using them.")
        except Exception:
            print("NVIDIA drivers (nvidia-smi) not found or not in PATH.")

if __name__ == "__main__":
    check_gpu()
