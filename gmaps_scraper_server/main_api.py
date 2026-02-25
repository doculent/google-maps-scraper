from fastapi import FastAPI, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
import logging
import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from gmaps_scraper_server.auth import verify_api_key
from gmaps_scraper_server.database import get_session
from gmaps_scraper_server.models.scrape_job import ScrapeJob
from gmaps_scraper_server.repositories.scrape_job_repository import ScrapeJobRepository

# Import the scraper function (adjust path if necessary)
try:
    from gmaps_scraper_server.scraper import scrape_google_maps
except ImportError:
    # Handle case where scraper might be in a different structure later
    logging.error("Could not import scrape_google_maps from scraper.py")
    # Define a dummy function to allow API to start, but fail on call
    def scrape_google_maps(*args, **kwargs):
        raise ImportError("Scraper function not available.")

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="Google Maps Scraper API",
    description="API to trigger Google Maps scraping based on a query.",
    version="0.2.0",
)


# ── Scrape endpoints (protected) ────────────────────────────────────────────

async def _run_scrape(
    query: str,
    max_places: Optional[int],
    lang: str,
    headless: bool,
    concurrency: int,
    session: AsyncSession,
) -> List[Dict[str, Any]]:
    """Shared scrape logic: creates a job record, runs the scrape, updates the job."""
    repo = ScrapeJobRepository(session)

    job = ScrapeJob(
        query=query,
        status="running",
        max_places=max_places,
        lang=lang,
        started_at=datetime.now(timezone.utc),
    )
    job = await repo.create(job)

    try:
        results = await asyncio.wait_for(
            scrape_google_maps(
                query=query,
                max_places=max_places,
                lang=lang,
                headless=headless,
                concurrency=concurrency,
            ),
            timeout=300,
        )
        await repo.update_status(
            job.id,
            "completed",
            results_count=len(results),
            completed_at=datetime.now(timezone.utc),
        )
        logging.info(f"Scraping finished for query: '{query}'. Found {len(results)} results.")
        return results
    except asyncio.TimeoutError:
        await repo.update_status(
            job.id,
            "failed",
            error_message="Scraping timed out after 300 seconds",
            completed_at=datetime.now(timezone.utc),
        )
        logging.error(f"Scraping timeout for query '{query}' after 300 seconds")
        raise HTTPException(status_code=504, detail="Scraping request timed out after 5 minutes")
    except ImportError as e:
        await repo.update_status(
            job.id,
            "failed",
            error_message=str(e),
            completed_at=datetime.now(timezone.utc),
        )
        logging.error(f"ImportError during scraping for query '{query}': {e}")
        raise HTTPException(status_code=500, detail="Server configuration error: Scraper not available.")
    except Exception as e:
        await repo.update_status(
            job.id,
            "failed",
            error_message=str(e),
            completed_at=datetime.now(timezone.utc),
        )
        logging.error(f"An error occurred during scraping for query '{query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred during scraping: {str(e)}")


@app.post("/scrape", response_model=List[Dict[str, Any]], dependencies=[Depends(verify_api_key)])
async def run_scrape(
    query: str = Query(..., description="The search query for Google Maps (e.g., 'restaurants in New York')"),
    max_places: Optional[int] = Query(None, description="Maximum number of places to scrape. Scrapes all found if None."),
    lang: str = Query("en", description="Language code for Google Maps results (e.g., 'en', 'es')."),
    headless: bool = Query(True, description="Run the browser in headless mode (no UI). Set to false for debugging locally."),
    concurrency: int = Query(5, description="Number of concurrent tabs for scraping details. Default is 5."),
    session: AsyncSession = Depends(get_session),
):
    """Triggers the Google Maps scraping process for the given query."""
    logging.info(f"Received scrape request for query: '{query}', max_places: {max_places}, lang: {lang}, "
                 f"headless: {headless}, concurrency: {concurrency}")
    return await _run_scrape(query, max_places, lang, headless, concurrency, session)


@app.get("/scrape-get", response_model=List[Dict[str, Any]], dependencies=[Depends(verify_api_key)])
async def run_scrape_get(
    query: str = Query(..., description="The search query for Google Maps (e.g., 'restaurants in New York')"),
    max_places: Optional[int] = Query(None, description="Maximum number of places to scrape. Scrapes all found if None."),
    lang: str = Query("en", description="Language code for Google Maps results (e.g., 'en', 'es')."),
    headless: bool = Query(True, description="Run the browser in headless mode (no UI). Set to false for debugging locally."),
    concurrency: int = Query(5, description="Number of concurrent tabs for scraping details. Default is 5."),
    session: AsyncSession = Depends(get_session),
):
    """Triggers the Google Maps scraping process for the given query via GET request."""
    logging.info(f"Received GET scrape request for query: '{query}', max_places: {max_places}, lang: {lang}, "
                 f"headless: {headless}, concurrency: {concurrency}")
    return await _run_scrape(query, max_places, lang, headless, concurrency, session)


# ── Job history endpoints (protected) ───────────────────────────────────────

@app.get("/jobs", dependencies=[Depends(verify_api_key)])
async def list_jobs(
    limit: int = Query(50, ge=1, le=200, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session: AsyncSession = Depends(get_session),
):
    """List scrape jobs, most recent first."""
    repo = ScrapeJobRepository(session)
    jobs = await repo.list_jobs(limit=limit, offset=offset)
    return [
        {
            "id": str(j.id),
            "query": j.query,
            "status": j.status,
            "max_places": j.max_places,
            "lang": j.lang,
            "results_count": j.results_count,
            "error_message": j.error_message,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            "created_at": j.created_at.isoformat(),
        }
        for j in jobs
    ]


@app.get("/jobs/{job_id}", dependencies=[Depends(verify_api_key)])
async def get_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get details of a single scrape job."""
    repo = ScrapeJobRepository(session)
    job = await repo.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": str(job.id),
        "query": job.query,
        "status": job.status,
        "max_places": job.max_places,
        "lang": job.lang,
        "results_count": job.results_count,
        "error_message": job.error_message,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "created_at": job.created_at.isoformat(),
    }


# ── Health check (public) ──────────────────────────────────────────────────

@app.get("/")
async def read_root():
    return {"message": "Google Maps Scraper API is running."}
