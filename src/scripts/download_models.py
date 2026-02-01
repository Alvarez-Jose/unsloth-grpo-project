
import os
from pathlib import Path
import urllib.request
from tqdm import tqdm


class DownloadProgressBar(tqdm):
    """Progress bar for downloads"""
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_file(url: str, output_path: Path):

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with DownloadProgressBar(
        unit='B',
        unit_scale=True,
        miniters=1,
        desc=output_path.name
    ) as t:
        urllib.request.urlretrieve(
            url,
            filename=output_path,
            reporthook=t.update_to
        )


def main():

    print("🚀 AgentOS Model Downloader")
    print("="*60)
    

    models_dir = Path(__file__).parent.parent / "models"
    models_dir.mkdir(exist_ok=True)
    

    models = {
        'master_router': {
            'name': 'Phi-2 3B (Q4_K_M quantized)',
            'url': 'https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf',
            'filename': 'phi-2.Q4_K_M.gguf',
            'size': '1.6 GB'
        },
        'code_expert': {
            'name': 'CodeLlama 7B (Q4_K_M quantized)',
            'url': 'https://huggingface.co/TheBloke/CodeLlama-7B-GGUF/resolve/main/codellama-7b.Q4_K_M.gguf',
            'filename': 'codellama-7b.Q4_K_M.gguf',
            'size': '4.1 GB'
        },
        'debug_expert': {
            'name': 'DeepSeek-Coder 6.7B (Q4_K_M quantized)',
            'url': 'https://huggingface.co/TheBloke/deepseek-coder-6.7B-instruct-GGUF/resolve/main/deepseek-coder-6.7b-instruct.Q4_K_M.gguf',
            'filename': 'deepseek-coder-6.7b.Q4_K_M.gguf',
            'size': '3.9 GB'
        }
    }
    
    print("\nModels to download:")
    total_size = 0
    for key, model in models.items():
        print(f"  • {model['name']} ({model['size']})")
    print()
    

    response = input("Download all models? (y/n): ")
    if response.lower() != 'y':
        print("Download cancelled")
        return
    
    print("\nStarting downloads...")
    print("This may take a while depending on your internet connection.\n")
    

    for key, model in models.items():
        output_path = models_dir / model['filename']
        
        if output_path.exists():
            print(f"✓ {model['name']} already exists, skipping")
            continue
        
        print(f"\n📥 Downloading {model['name']}...")
        try:
            download_file(model['url'], output_path)
            print(f"✅ Downloaded: {output_path}")
        except Exception as e:
            print(f"❌ Error downloading {model['name']}: {e}")
            print("You can try downloading manually from:")
            print(f"   {model['url']}")
    
    print("\n" + "="*60)
    print("✅ Download complete!")
    print(f"Models saved to: {models_dir.absolute()}")
    print("\nYou can now run: python core/main.py")
    print("="*60)


if __name__ == "__main__":
    main()