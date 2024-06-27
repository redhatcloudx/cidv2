"""Functions for initial bootstrap activities."""

import logging

from cid.crud import update_image_data
from cid.database import SessionLocal

logger = logging.getLogger(__name__)


def populate_db() -> None:
    """Populate the database with image data during container builds."""
    logger.info("Only populating the database.")

    db = SessionLocal()
    update_image_data(db)

    logger.info("Database population complete. Exiting.")
