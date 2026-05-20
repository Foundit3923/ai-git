# 🤖 Ollama Git Commit - AI-Powered Commit Messages

[![PyPI version](https://img.shields.io/pypi/v/ollama-git-commit.svg)](https://pypi.org/project/ollama-git-commit/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/ollama-git-commit)](https://pypi.org/project/ollama-git-commit/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/himanshu231204/ai-commit?style=social)](https://github.com/himanshu231204/ai-commit)

Generate intelligent git commit messages using your local Ollama instance. No API keys, completely free, and runs offline!

---

## ✨ Features

- 🤖 **AI-Powered**: Uses local Ollama models to generate commit messages
- 🔒 **Privacy First**: Everything runs locally, no data sent to external APIs
- 🎯 **Multiple Styles**: Conventional commits, semantic, or detailed formats
- 💰 **Free**: No API costs, uses your local Ollama instance
- ⚡ **Fast**: Quick generation with local models
- 🎨 **Interactive**: Review, regenerate, or edit messages before committing
- 🌐 **Offline**: Works completely offline

---

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install ollama-git-commit
```

### From Source

```bash
git clone https://github.com/himanshu231204/ai-commit.git
cd ai-commit
pip install -e .
```

---

## 📋 Prerequisites

Before using Ollama Git Commit, you need:

1. **Python 3.8+**
   ```bash
   python --version
   ```

2. **Git**
   ```bash
   git --version
   ```

3. **Ollama** - [Install Ollama](https://ollama.ai)
   ```bash
   # Install Ollama (macOS/Linux)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull a model (e.g., llama2)
   ollama pull llama2
   
   # Start Ollama server
   ollama serve
   ```

---

## 💡 Usage

### Basic Usage

1. **Stage your changes**:
   ```bash
   git add .
   ```

2. **Generate commit message**:
   ```bash
   ai-commit
   ```

3. **Review and choose**:
   - `y` - Accept and commit
   - `r` - Regenerate message
   - `e` - Edit message manually
   - `n` - Cancel

### Example Workflow

```bash
# Make some changes to your code
echo "print('Hello World')" > hello.py

# Stage the changes
git add hello.py

# Generate AI commit message
ai-commit

# Output:
╔═══════════════════════════════════════════╗
║         🤖 AI Commit Message Tool         ║
║      Powered by Local Ollama 🦙           ║
╚═══════════════════════════════════════════╝

🔍 Checking Ollama server...
✓ Ollama server is running

📊 Changes:
  + 1 lines added
  - 0 lines removed

🤖 Generating commit message...

Generated Commit Message:
──────────────────────────────────────────────────
feat: add hello world script
──────────────────────────────────────────────────

Options:
  y - Accept and commit
  r - Regenerate message
  e - Edit message
  n - Cancel
```

### Advanced Usage

#### Generate a commit message for an existing commit
1. **Find and store a commit hash**:
   ```bash
   git log
   ```
   or search your logs by keyword
   ```bash
   git log --grep=<keyword>
   ```
   select the commit and copy the hash
   ```bash
   git log --grep=update
   commit f01279fa49a06f049dae4b379907a7d3723c1700
   Author: User <user_email@gmail.com>
   Date:   Fri Mar 13 19:52:38 2026 -0400
      update
   ```
   the hash in this example is `f01279fa49a06f049dae4b379907a7d3723c1700`

2. **Generate commit message**:
   ```bash
   ai-commit -c f01279fa49a06f049dae4b379907a7d3723c1700
   ```

3. **Review and choose**:
   - `y` - Accept and commit
   - `r` - Regenerate message
   - `e` - Edit message manually
   - `n` - Cancel

#### Generate a commit message for the diff of two commits
1. **Find and store a commit hash**:
   ```bash
   git log
   ```
   or search your logs by keyword
   ```bash
   git log --grep=<keyword>
   ```
   select the commit and copy the hash
   ```bash
   git log --grep=update
   commit f01279fa49a06f049dae4b379907a7d3723c1700
   Author: User <user_email@gmail.com>
   Date:   Fri Mar 13 19:52:38 2026 -0400
      update
   ```
   the hash in this example is `f01279fa49a06f049dae4b379907a7d3723c1700`

2. **Find and store a second commit hash**
   ```bash
   git log
   ```
   or search your logs by keyword
   ```bash
   git log --grep=<keyword>
   ```
   select the commit and copy the hash
   ```bash
   git log --grep=update
   commit 575e541f630d3b9a53d6110519e7e4330b1a7281
   Author: User <user_email@gmail.com>
   Date:   Tue Mar 3 14:31:25 2026 -0500
      update
   ```
   the hash in this example is `575e541f630d3b9a53d6110519e7e4330b1a7281`

3.**Generate commit message**:
   The order of commit args here does not change the result
   ```bash
   ai-commit -r 575e541f630d3b9a53d6110519e7e4330b1a7281 f01279fa49a06f049dae4b379907a7d3723c1700
   ```

5. **Review and choose**:
   - `y` - Accept and commit
   - `r` - Regenerate message
   - `e` - Edit message manually
   - `n` - Cancel
---

## ⚙️ Configuration

### Custom Ollama Server

If your Ollama server is running on a different host/port, edit `ai_commit.py`:

```python
ollama = OllamaClient(base_url="http://192.168.1.100:11434")
```

### Change AI Model

```python
ollama = OllamaClient(model="codellama")  # or "mistral", "llama2", etc.
```

### Commit Message Styles

The tool supports three commit message styles:

1. **Conventional Commits** (default):
   ```
   feat(auth): add user login functionality
   ```

2. **Semantic**:
   ```
   Add user login functionality
   ```

3. **Detailed**:
   ```
   Add user authentication system
   
   - Implement JWT-based authentication
   - Add login and logout endpoints
   - Create user session management

   New Files
   - Authenticate.cs

   AlteredFiles
   - SessionManager.cs
   -- LogIn()
   -- LogOut()
   ```

---


## 🤖 Auto Model Selection

AI Commit automatically selects the best available model on your system, **prioritizing lighter and faster models** for optimal performance.

### Priority Order (Fastest to Slowest):

1. **phi** - Smallest, fastest (Recommended for quick commits)
2. **mistral** - Great balance of speed and quality
3. **qwen** - Fast alternative
4. **gemma** - Google's lightweight model
5. **codellama** - Optimized for code
6. **llama2** - Reliable but slower
7. **llama3** - Most powerful but slowest

### How It Works:

When you run `ai-commit`, the tool will:
1. Check all installed Ollama models
2. Automatically select the lightest/fastest available
3. Display which model was chosen
4. Generate your commit message

### Example Output:

```bash
$ ai-commit

╔═══════════════════════════════════════════╗
║         🤖 AI Commit Message Tool         ║
║      Powered by Local Ollama 🦙           ║
╚═══════════════════════════════════════════╝

summarize staged changes
🔍 Checking Ollama server...
✓ Ollama server is running

Available models (3):
  • phi:latest
  • mistral:latest
  • llama2:latest

✓ Auto-selected: phi:latest
  (Prioritizing lighter/faster models)

📊 Changes:
  + 8 lines added
  - 0 lines removed

🤖 Generating conventional commit message...
```

## 🤖 Manual Model Selection

A specific model may be selected by adding `-m <model name>` or `--model <model name>` after `ai-commit`

### How It Works:

When you run `ai-commit -m <model name>`, the tool will:
1. Check all installed Ollama models
2. Ensure that the specified model is available
3. Auto select if the specified model is not available
4. Generate your commit message

### Example Output:

```bash
$ ai-commit -m mistral

╔═══════════════════════════════════════════╗
║         🤖 AI Commit Message Tool         ║
║      Powered by Local Ollama 🦙           ║
╚═══════════════════════════════════════════╝

summarize staged changes
🔍 Checking Ollama server...
✓ Ollama server is running

Available models (3):
  • phi:latest
  • mistral:latest
  • llama2:latest

✓ Selected: mistral

📊 Changes:
  + 8 lines added
  - 0 lines removed

🤖 Generating conventional commit message...
```

### Recommended Setup:

For best performance, install a lightweight model:

```bash
# Fastest (Recommended)
ollama pull phi

# Good balance
ollama pull mistral

# For code-heavy projects
ollama pull codellama
```

### Manual Model Override:

If you want to use a specific model, you can set an environment variable:

**Windows:**
```cmd
set OLLAMA_MODEL=mistral
ai-commit
```

**Linux/Mac:**
```bash
export OLLAMA_MODEL=mistral
ai-commit
```

---



---

## 📝 Examples

### Example 1: Adding a New Feature

```bash
$ git add new_feature.py
$ ai-commit

Generated: feat: add user profile management feature
```

### Example 2: Bug Fix

```bash
$ git add bug_fix.py
$ ai-commit

Generated: fix: resolve null pointer exception in login
```

### Example 3: Documentation

```bash
$ git add README.md
$ ai-commit

Generated: docs: update installation instructions
```

---

## 🐛 Troubleshooting

### Ollama Not Running
```
Error: Cannot connect to Ollama
Solution: Start Ollama server with `ollama serve`
```

### No Staged Changes
```
Error: No staged changes found
Solution: Stage your changes with `git add <files>`
```

### Model Not Found
```
Error: Model not found
Solution: Pull the model with `ollama pull llama2`
```

---

## 🤝 Contributing

Contributions are what make the open-source community amazing! Any contributions you make are **greatly appreciated**.

### How to Contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (when available)
5. Commit using ai-commit! 😄
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Ollama** - For making local LLMs accessible
- **Git** - The best version control system
- **Python** - For being awesome
- **You** - For using this tool!

---

## 🗺️ Roadmap

- [x] Initial release on PyPI
- [x] Configuration file support (`.ai-commit.yml`)
- [ ] More commit message formats
- [ ] Interactive model selection
- [ ] Emoji support in commits 🎉
- [ ] Multiple language support
- [ ] Git hooks integration
- [ ] VSCode extension
- [ ] Custom prompt templates
- [ ] Commit message history
- [ ] Auto-detect commit type from files
- [ ] Batch commit support
- [ ] Integration with GitHub CLI

---

## 👨‍💻 Author

**Himanshu Kumar**

- 🌐 GitHub: [@himanshu231204](https://github.com/himanshu231204)
- 💼 LinkedIn: [himanshu231204](https://www.linkedin.com/in/himanshu231204)
- 🐦 Twitter/X: [@himanshu231204](https://twitter.com/himanshu231204)
- 📧 Email: himanshu231204@gmail.com

---

## 💖 Support

If you find this project helpful, please consider:

- ⭐ Starring the repository
- 🐛 Reporting bugs
- 💡 Suggesting new features
- 🔀 Contributing code
- ☕ [Buy me a coffee](https://www.buymeacoffee.com/himanshu231204)
- 💝 [Sponsor on GitHub](https://github.com/sponsors/himanshu231204)

---

## 📊 Stats

![GitHub stars](https://img.shields.io/github/stars/himanshu231204/ai-commit?style=social)
![GitHub forks](https://img.shields.io/github/forks/himanshu231204/ai-commit?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/himanshu231204/ai-commit?style=social)
![PyPI downloads](https://img.shields.io/pypi/dm/ollama-git-commit)

---

## 🔗 Links

- **PyPI Package**: https://pypi.org/project/ollama-git-commit/
- **Documentation**: [GitHub Wiki](https://github.com/himanshu231204/ai-commit/wiki)
- **Issues**: [GitHub Issues](https://github.com/himanshu231204/ai-commit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/himanshu231204/ai-commit/discussions)
- **Releases**: [GitHub Releases](https://github.com/himanshu231204/ai-commit/releases)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=himanshu231204/ai-commit&type=Date)](https://star-history.com/#himanshu231204/ai-commit&Date)

---

## 📣 Show Your Support

Give a ⭐️ if this project helped you!

---

**Made with ❤️ by [Himanshu Kumar](https://github.com/himanshu231204)**

---

## 🚀 Quick Links

| Resource | Link |
|----------|------|
| 📦 **Install** | `pip install ollama-git-commit` |
| 📖 **Docs** | [GitHub](https://github.com/himanshu231204/ai-commit) |
| 🐛 **Issues** | [Report Bug](https://github.com/himanshu231204/ai-commit/issues/new?template=bug_report.md) |
| 💡 **Feature Request** | [Request Feature](https://github.com/himanshu231204/ai-commit/issues/new?template=feature_request.md) |
| 💬 **Discussions** | [Join Discussion](https://github.com/himanshu231204/ai-commit/discussions) |
| ⭐ **Star** | [Star on GitHub](https://github.com/himanshu231204/ai-commit) |

---

