"""
Analytics utility functions for service layer.

Provides shared helper functions for analytics operations.
"""

import pandas as pd
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession


async def query_to_dataframe(db: AsyncSession, query: Select) -> pd.DataFrame:
    """
    Execute an async SQLAlchemy query and convert results to pandas DataFrame.

    Args:
        db: Async database session
        query: SQLAlchemy Select statement

    Returns:
        pandas DataFrame with query results
    """
    result = await db.execute(query)
    rows = result.all()
    return pd.DataFrame([dict(row._mapping) for row in rows])
