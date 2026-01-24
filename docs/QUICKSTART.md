# 🚀 Quick Start Guide

Get Cortex running in 10 minutes!

## Prerequisites

- **Windows 10/11** (64-bit)
- **Python 3.10+** 
- **16GB RAM** minimum (32GB recommended)
- **50GB free disk space** (for models)
- **CUDA-capable GPU** (optional, but recommended)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/agent-os.git
cd agent-os
```

### 2. Create Python Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** If you have a CUDA GPU, install the GPU version of PyTorch:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 4. Download AI Models

```bash
python scripts/download_models.py
```

This will download ~10GB of models. Go grab a coffee ☕

**Models downloaded:**
- Phi-2 3B (Master Router)
- CodeLlama 7B (Code Expert)
- DeepSeek-Coder 6.7B (Debug Expert)

### 5. Enable Windows Event Tracing (Optional but Recommended)

For kernel-level event monitoring, run PowerShell as Administrator:

```powershell
# Enable ETW providers
logman query providers | findstr "Kernel"

# The script will auto-configure what it needs
```

## Running Cortex

### Interactive Mode (Recommended for Testing)

```bash
python core/main.py
```

You'll see:

```
🤖 Cortex Interactive Mode
============================================================

Commands:
  • Type your query to get AI assistance
  • 'stats' - Show system statistics
  • 'events' - Show recent system events
  • 'quit' - Exit

============================================================

You: _
```

### Example Queries to Try

**Debugging Assistance:**
```
You: Help me debug a null pointer exception in my C++ code
```

**File Operations:**
```
You: Find all Python files modified in the last hour
```

**Pattern Detection:**
```
# Just open Visual Studio and a .cpp file
# Cortex will auto-detect debugging session and offer help!
```

## Verify Installation

Run the test suite:

```bash
pytest tests/
```

Check if ETW monitoring is working:

```bash
python core/etw_monitor.py
```

You should see system events being captured in real-time.

## What You Should See

When everything is working:

1. **ETW Monitor**: Logs system events to console
2. **Master Router**: Routes queries to appropriate experts
3. **Expert Agents**: Execute specialized tasks
4. **Performance**: Routing decisions in <100ms

Example output:

```
🚀 Cortex initializing...
Initializing components...
Loading Master Router...
✅ Master router model loaded successfully
Loading Expert Agents...
🔍 DebuggingExpert initialized
📁 FileOperationsExpert initialized
Starting ETW Event Monitor...
✅ All components initialized
✅ Cortex started successfully
```

## Troubleshooting

### Model Loading Fails

**Error:** `Model file not found`

**Solution:** Run `python scripts/download_models.py` again

### ETW Events Not Captured

**Error:** `pywin32` not installed

**Solution:**
```bash
pip install pywin32
python venv\Scripts\pywin32_postinstall.py -install
```

### Out of Memory

**Error:** CUDA out of memory

**Solution:** 
- Close other GPU applications
- Use CPU-only mode (slower): Edit `master_router.py`, set `n_gpu_layers=0`

### Permission Denied for ETW

**Error:** Access denied when monitoring events

**Solution:** Run as Administrator (for full kernel-level monitoring)

## Next Steps

Now that you have it running:

1. **Read the Architecture**: [docs/architecture.md](../docs/architecture.md)
2. **Add Custom Experts**: [docs/adding-experts.md](../docs/adding-experts.md)
3. **Kernel Development**: [docs/kernel-dev.md](../docs/kernel-dev.md)

## Development Mode

Want to contribute? See [CONTRIBUTING.md](../CONTRIBUTING.md)

### Hot Reload During Development

```bash
# Install watchdog for auto-reload
pip install watchdog

# Run with auto-reload
watchmedo auto-restart -p "*.py" python core/main.py
```

## FAQ

**Q: Do I need a GPU?**
A: No, but it's highly recommended. CPU-only will be 5-10x slower.

**Q: Why is it downloading so many GB?**
A: The AI models are large. We use quantized versions to keep it manageable.

**Q: Is my data sent to the cloud?**
A: NO! Everything runs 100% locally on your machine.

**Q: What if I don't have 50GB free?**
A: You can download just the master router (1.6GB) to start. Expert models are optional.

**Q: Can I use this on Windows Server?**
A: Yes, but some ETW features may differ. Test thoroughly.

---

**Still stuck?** Open an issue on GitHub with:
- Your Windows version
- Python version (`python --version`)
- Error message (full traceback)
- Hardware specs (CPU, RAM, GPU)

We're here to help! 🚀