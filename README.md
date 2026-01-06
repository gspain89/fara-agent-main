# FARA-7B Browser Agent (Playwright + LM Studio)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LM Studio Compatible](https://img.shields.io/badge/LM%20Studio-Compatible-green.svg)](https://lmstudio.ai/)
[![Ollama Compatible](https://img.shields.io/badge/Ollama-Compatible-green.svg)](https://ollama.ai/)
[![llama.cpp](https://img.shields.io/badge/llama.cpp-Powered-orange.svg)](https://github.com/ggerganov/llama.cpp)

> 🚀 **Run Microsoft's FARA-7B browser agent 100% locally using llama.cpp engines (LM Studio/Ollama)**

## 🎯 Why This Project?

**Problem**: Magentic-UI only supported vLLM, limiting local deployment options
**Solution**: This project bridges FARA-7B with llama.cpp-based engines (LM Studio/Ollama)

**Key Achievement**:
- ✅ Run FARA-7B on consumer GPUs (8GB+ VRAM with quantization)
- ✅ No cloud dependencies - 100% local execution
- ✅ OpenAI-compatible API for easy integration
- ✅ Two implementation approaches: **Playwright Agent** (standalone) + **Magentic-UI Agent** (integrated framework)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [LM Studio Setup](#lm-studio-setup)
- [Usage](#usage)
  - [Playwright Agent](#playwright-agent)
  - [Magentic-UI Agent](#magentic-ui-agent)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Troubleshooting Journey](#troubleshooting-journey)
- [Limitations](#limitations)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This project provides **two implementations** for browser automation using **Microsoft FARA-7B** (7B parameter agentic model):

1. **Playwright Agent**: Fast, CLI-based standalone agent for automation scripts
2. **Magentic-UI Agent**: Web UI-based framework with user approval and co-planning

### Core Features

- **100% Local Execution** (LM Studio/Ollama via llama.cpp)
- **Vision-Centric Approach** (Screenshot-based control)
- **OpenAI API Compatible**
- **No DOM/Accessibility Tree Required**
- **GPU Optimized** (Quantized model support)

---

## Key Features

| Feature | Playwright Agent | Magentic-UI Agent |
|---------|------------------|-------------------|
| **Execution** | CLI (Terminal) | Web UI (localhost:8081) |
| **Speed** | Fast | Moderate (orchestration overhead) |
| **User Approval** | None (auto-execution) | Co-planning (approval before execution) |
| **Safety** | Low | High (Action guards) |
| **Best For** | Repetitive automation, scripts | Complex tasks, interactive planning |
| **Live View** | None | Docker browser (VNC) |

### Comparison: vLLM vs llama.cpp (LM Studio/Ollama)

| Aspect | vLLM (Original) | llama.cpp (This Project) |
|--------|-----------------|--------------------------|
| **Deployment** | Server-grade (A100/H100) | Consumer GPUs (RTX 3060+) |
| **Memory** | 16GB+ VRAM required | 8GB VRAM (with quantization) |
| **Setup** | Complex (Python env, CUDA) | Simple (Download LM Studio) |
| **Cost** | Cloud hosting required | Free, local execution |
| **Speed** | Faster (FP16) | Moderate (quantized) |

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **LM Studio** ([Download](https://lmstudio.ai/)) or **Ollama** ([Download](https://ollama.ai/))
- **FARA-7B Model** (Download in LM Studio/Ollama)
- **Playwright** (Browser automation)
- **(Magentic-UI only) Docker** (For Live View)

### LM Studio Setup

1. Launch LM Studio
2. Download and load FARA-7B model
   - Model name: `microsoft/Fara-7B` or `microsoft_fara-7b`
3. Start Local Server
   - Port: `1234` (default)
   - **Important**: Set `max_tokens` to **15000** (for Vision requests)
4. Verify server:
   ```bash
   curl http://127.0.0.1:1234/v1/models
   ```

### Ollama Setup (Alternative)

```bash
# Pull FARA-7B model
ollama pull fara:7b

# Run model with increased context
ollama run fara:7b --num-ctx 15000

# Verify
curl http://127.0.0.1:11434/api/tags
```

---

## Usage

### Playwright Agent

Fast CLI-based agent for automation scripts.

#### Installation

```bash
cd playwright-agent
pip install -r requirements.txt
python -m playwright install chromium
```

#### Running

```bash
# Basic execution (headless mode)
python run_agent.py --task "Go to GitHub and search for 'playwright'"

# Show browser GUI (for debugging)
python run_agent.py --task "Go to GitHub and search for 'playwright'" --headful

# Keep browser open after task completion
python run_agent.py --task "Your task here" --headful --keep-open
```

#### Configuration

Edit `playwright-agent/config.json`:
```json
{
  "model": "microsoft_fara-7b",
  "base_url": "http://127.0.0.1:1234/v1",
  "api_key": "lm-studio",
  "max_rounds": 20,
  "max_n_images": 1,
  "temperature": 0.0
}
```

#### Example Tasks

1. **GitHub Search**
   ```bash
   python run_agent.py --task "Go to GitHub and search for 'fastapi'" --headful
   ```

2. **Wikipedia Navigation**
   ```bash
   python run_agent.py --task "Go to Wikipedia and search for 'Python programming', click the article" --headful --keep-open
   ```

3. **Google Search + Click Result**
   ```bash
   python run_agent.py --task "Go to Google and search for 'machine learning tutorial', click the first result"
   ```

See [Playwright CLI Usage Guide](./docs/USAGE_GUIDE_%20Playwright%20CLI.md) for more examples.

---

### Magentic-UI Agent

Web UI-based agent with user approval and planning features.

#### Installation

```bash
cd magentic-ui-agent
pip install -r requirements.txt
```

#### Running

```bash
magentic-ui --fara --port 8081 --config fara_config.yaml
```

Open browser at **http://localhost:8081**

#### Configuration

Edit `magentic-ui-agent/fara_config.yaml`:
```yaml
model_config_local_surfer: &client_surfer
  provider: OpenAIChatCompletionClient
  config:
    model: "microsoft_fara-7b"
    base_url: http://127.0.0.1:1234/v1
    api_key: lm-studio
    model_info:
      vision: true
      function_calling: true
```

**Critical Modification**:
- Edit `/opt/homebrew/lib/python3.11/site-packages/magentic_ui/agents/web_surfer/fara/_fara_web_surfer.py`:
  - Line 64: Change `model_call_timeout: int = 20` to `model_call_timeout: int = 120`
  - Reason: Vision processing requires 15-20 seconds per request

---

## Project Structure

```
fara-agent-main/
├── README.md                      # This file
├── LICENSE                        # MIT License
├── .gitignore                     # Git configuration
│
├── playwright-agent/              # Playwright-based standalone agent
│   ├── agent.py                   # FaraAgent class (main logic)
│   ├── browser.py                 # SimpleBrowser class (Playwright wrapper)
│   ├── run_agent.py               # CLI entry point
│   ├── message_types.py           # LLM message data structures
│   ├── prompts.py                 # System prompt generation
│   ├── utils.py                   # URL utilities
│   ├── config.json                # Agent configuration
│   ├── requirements.txt           # Python dependencies
│   ├── README.md                  # Playwright Agent docs
│   └── downloads/                 # Downloaded files storage
│
├── magentic-ui-agent/             # Magentic-UI integration
│   ├── fara_config.yaml           # Magentic-UI config (working version)
│   ├── requirements.txt           # Python dependencies
│   └── README.md                  # Magentic-UI Agent docs
│
└── docs/                                      # Detailed documentation
    ├── USAGE_GUIDE_MAGENTIC_UI.md            # Magentic-UI Usage Guide (LM Studio integration)
    ├── USAGE_GUIDE_ Playwright CLI.md        # Playwright CLI Usage Guide
    └── FARA_7B_Capability_분석_보고서.md      # Capability Analysis (Playwright-based)
```

---

## Documentation

### Usage Guides

- **[Magentic-UI Usage Guide (LM Studio Integration)](./docs/USAGE_GUIDE_MAGENTIC_UI.md)** ⭐ Recommended
  - **Project Core**: How to run Magentic-UI (originally vLLM-only) with LM Studio
  - LM Studio vs vLLM comparison
  - Detailed troubleshooting (blank screenshot, timeout, proxy)
  - Web UI usage instructions

- **[Playwright CLI Usage Guide](./docs/USAGE_GUIDE_%20Playwright%20CLI.md)**
  - Fast CLI-based execution
  - 10 practical examples
  - Troubleshooting tips

### Reference Documentation

- **[FARA Capability Analysis Report](./docs/FARA_7B_Capability_분석_보고서.md)** (Playwright CLI-based)
  - FARA-7B model capability analysis
  - List of 11 supported actions
  - Vision-only constraints detailed

### External Resources

- [FARA-7B Paper (ArXiv)](https://arxiv.org/abs/2511.19663)
- [FARA-7B HuggingFace](https://huggingface.co/microsoft/Fara-7B)
- [Magentic-UI GitHub](https://github.com/microsoft/magentic-ui)
- [LM Studio Documentation](https://lmstudio.ai/docs)
- [Ollama Documentation](https://ollama.ai/docs)

---

## Troubleshooting Journey

> **Note**: This section documents challenges encountered during development.
> All issues are now resolved. See [Magentic-UI Usage Guide](./docs/USAGE_GUIDE_MAGENTIC_UI.md) for details.

Key problems solved during development:

### 1. Blank Screenshot Issue
**Symptom**: Model couldn't see screenshots, responded with "blank image"
**Cause**: LM Studio `max_tokens` limited to 4000, truncating image data
**Solution**: Increased LM Studio `max_tokens` to **15000**

### 2. Client Disconnected Messages
**Symptom**: Repeated "Client disconnected" messages during Vision requests
**Cause**: `model_call_timeout: int = 20` (20 seconds) shorter than Vision processing time (15-20 seconds)
**Solution**: Increased `model_call_timeout` in `_fara_web_surfer.py` to **60 seconds**

### 3. Proxy Unnecessary
**Attempt**: Implemented middleware proxy for tool calling
**Conclusion**: Magentic-UI FARA agent directly parses `<tool_call>` XML format
**Solution**: Direct connection to LM Studio (removed proxy)

---

## Limitations and Use Cases

FARA-7B uses a Vision-based approach. **Capabilities vary by execution environment**:

### Magentic-UI Environment (Recommended)

**Supported Tasks**:
- **Web Navigation**: Visit websites, click, scroll, multi-page workflows
- **Information Gathering/Summarization**: Read and summarize web pages (Vision-based)
- **Form Filling**: Text input, button clicks, dropdown selection
- **Complex Tasks**: Multi-agent collaboration, user approval-based execution (Co-planning)
- **Session Management**: Task history, Live View (Docker VNC)

### Playwright CLI Environment

**Supported Tasks**:
- **Web Navigation**: Visit websites, click, scroll
- **Form Filling**: Text input, button clicks
- **Search**: Enter search queries and click results
- **Visual Verification**: Check page arrival, layout confirmation
- **Repetitive Automation**: Repeat standardized web tasks

**Limitations** (Playwright CLI implementation):
- Simplified demo version without multi-turn/session management
- Structured data extraction not implemented

See [FARA Capability Analysis Report](./docs/FARA_7B_Capability_분석_보고서.md) (Playwright CLI-based) for details.

---

## Troubleshooting

### LM Studio Connection Failed

```bash
# Check server status
curl http://127.0.0.1:1234/v1/models

# If no response:
# 1. Verify LM Studio is running
# 2. Start Local Server (port 1234)
# 3. Confirm FARA-7B model is loaded
```

### Playwright Browser Errors

```bash
# Reinstall Playwright Chromium
python -m playwright install chromium

# If permission issues
sudo python -m playwright install chromium
```

### Magentic-UI Docker Image Issues

```bash
# Check Docker status
docker ps

# Restart Magentic-UI
# Press Ctrl+C to stop, then restart
magentic-ui --fara --port 8081 --config fara_config.yaml
```

More troubleshooting solutions in [Usage Guides](./docs/USAGE_GUIDE_%20Playwright%20CLI.md) and [Magentic-UI Usage Guide](./docs/USAGE_GUIDE_MAGENTIC_UI.md).

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### How to Contribute

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project follows the licenses of the following open-source projects:

- **FARA-7B Model**: [MIT License](https://huggingface.co/microsoft/Fara-7B) (Microsoft)
- **Magentic-UI**: [MIT License](https://github.com/microsoft/magentic-ui) (Microsoft)
- **Playwright**: [Apache License 2.0](https://github.com/microsoft/playwright) (Microsoft)

### Project Code

MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Star History

If you find this project useful, please consider giving it a star! ⭐

---

## Acknowledgments

- **Microsoft** for FARA-7B, Magentic-UI, and Playwright
- **llama.cpp community** for enabling local LLM inference
- **LM Studio & Ollama teams** for user-friendly local LLM platforms

---

**Project Created**: 2025-12-15
**Last Updated**: 2025-01-06

### Reference

Official Microsoft FARA Project: [github.com/microsoft/fara](https://github.com/microsoft/fara)
