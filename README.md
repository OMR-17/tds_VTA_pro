## What We’ve Done
This project involved creating a FastAPI-based API to assist students by answering questions using scraped data from Discourse posts and GitHub repositories. Here’s what we accomplished:

- **Data Scraping**: Wrote `scrape_data.py` to fetch Discourse posts (Jan 1, 2025 - Apr 14, 2025) and GitHub content, storing them in `tds_data.json` for context.
- **API Development**: Built `app.py` with a `POST /api/` endpoint to process text and optional base64-encoded image questions, using the AI Proxy (`https://aiproxy.sanand.workers.dev/openai`) with `gpt-4o-mini` for responses.
- **Integration**: Configured environment variables (`AIPROXY_TOKEN`, `DISCOURSE_T_COOKIE`, etc.) to authenticate API calls and data access.
- **Local Testing**: Successfully tested the API locally on `http://localhost:7860/api/` with `curl`, returning JSON responses with answers and links.
- **Deployment Attempt**: Deployed on Hugging Face Spaces (`https://omr-17--tds_vta_prohf.hf.space/api/`) using a `Dockerfile`, but encountered a 404 error on the `/api/` endpoint, indicating a routing issue we’re resolving. It is tuffest thing to do because i got too many error and after lot of time sepending still it is failure for me , sorry for this...
- **GitHub Setup**: Prepared a public repository to share the project code and documentation.
