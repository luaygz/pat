# pat
Data ingestion CLI util similar to `cat`.

`pat` takes one command line argument, either a file path or URL, and will extract its contents for you as LLM-ready text. 

# Installation

`pat` was developed on Python 3.11.4, but other versions probably work.

```bash
conda create -n pat python==3.11.4
conda activate pat
pip install -e .
```

You can then bash alias it by putting the following in your `.bashrc` or similar file:

```bash
alias pat='conda activate pat && /path/to/pat.py'
```

# Environment Variables Setup

`pat` requires three API keys, OpenAI, Mistral, and Parallel. Please clone the `.env.template` file as `.env` file and put your API keys in there.

You can get your API keys at the following links:

- https://platform.openai.com/api-keys
- https://admin.mistral.ai/organization/api-keys
- https://platform.parallel.ai/settings?tab=api-keys

Note that these are paid services.

OpenAI is used for audio transcription, Mistral for document (PDR, docx) and image OCR, and Parallel for extracting the contents of webpages.

# Repomix Setup

If you want to use GitHub repos as a data source, you will need to install Repomix as per the maintainer's instructions:

- https://github.com/yamadashy/repomix

# MongoDB for Cacheing

You can set up MongoDB for cacheing results. Set the `MONGODB_URI` variable in your `.env` file. You may use the default value `perceiver` for `MONGODB_DB` as per the `.env.template`, or change it if you prefer.

If set up, querying a file or URL twice will not reprocess the file/URL, but pull the data from the cache instead.

To force bypass the cache (and update the cache if the results have changed), pass the `--bypass-cache` argument. By default cacheing is enabled.

Cacheing is checked by using the file hash for local files, and normalized URL for links.

# Supported Sources

`pat` automatically detects the source type and uses the appropriate adapter.

## Local Files

| Type | Extensions |
|------|------------|
| **Text & Code** | `.txt`, `.md`, `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.json`, `.yaml`, `.yml`, `.xml`, `.html`, `.css`, `.sh`, `.bat`, `.ps1`, `.java`, `.c`, `.cpp`, `.h`, `.cs`, `.go`, `.rs`, `.rb`, `.php`, `.swift`, `.kt`, `.sql`, `.env`, `.csv`, `.log`, `.ini`, `.cfg`, `.conf`, `.toml`, `.rst`, `.tex`, `.r`, `.scala`, `.groovy`, `.pl`, `.pm`, `.lua`, `.vim`, `.zsh`, `.bash`, `.fish`, `.awk`, `.sed` |
| **Documents** | `.pdf`, `.docx`, `.pptx`, `.epub`, `.odt` (via Mistral OCR) |
| **Images** | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp` (via Mistral OCR) |
| **Audio/Video** | `.flac`, `.mp3`, `.mp4`, `.mpeg`, `.mpga`, `.m4a`, `.ogg`, `.wav`, `.webm` (via OpenAI Whisper) |

Special filenames without extensions are also recognized: `Dockerfile`, `Makefile`, `Gemfile`, `Rakefile`, `Procfile`, `Vagrantfile`, `Jenkinsfile`, `README`, `LICENSE`, `.gitignore`, `.dockerignore`, `.editorconfig`, etc.

## URLs

| Source | Description |
|--------|-------------|
| **YouTube** | Video transcripts from `youtube.com/watch`, `youtu.be`, `youtube.com/shorts`, etc. |
| **GitHub** | Repository contents from `github.com/{owner}/{repo}` (uses Repomix) |
| **arXiv** | Paper content from `arxiv.org/abs`, `arxiv.org/pdf`, `arxiv.org/html` |
| **Web Pages** | Any other HTTP/HTTPS URL (via Parallel AI) |

URLs pointing directly to files (e.g., `https://example.com/file.pdf`) are downloaded and processed using the appropriate file adapter.

# Usage

```bash
python pat.py /home/user/Documents/report.pdf
python pat.py /home/user/Pictures/ocr.png
python pat.py https://en.wikipedia.org/wiki/Artificial_intelligence
python pat.py --bypass-cache https://en.wikipedia.org/wiki/Artificial_intelligence
```

Pat can be piped in to other commands as well

```bash
python pat.py /home/user/Documents/report.pdf | head
```