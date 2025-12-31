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

# MongoDB for Cacheing

You can set up MongoDB for cacheing results. Set the `MONGODB_URI` variable in your `.env` file. You may use the default value `perceiver` for `MONGODB_DB` as per the `.env.template`, or change it if you prefer.

If set up, querying a file or URL twice will not reprocess the file/URL, but pull the data from the cache instead.

To force bypass the cache (and update the cache if the results have changed), pass the `--bypass-cache` argument. By default cacheing is enabled.

Cacheing is checked by using the file hash for local files, and normalized URL for links.

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