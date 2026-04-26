"""
Base Salesforce repository with API client management.

Provides common functionality for all Salesforce API interactions
including authentication, rate limiting, and error handling.
"""
from typing import Generic, TypeVar, Optional, Dict, Any, List
from abc import ABC
import logging

from simple_salesforce import Salesforce
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SalesforceAPIError(Exception):
    """Custom exception for Salesforce API errors."""
    pass


class SalesforceRepository(BaseRepository[T], ABC, Generic[T]):
    """
    Base repository for Salesforce API operations.
    
    Handles authentication, rate limiting, and provides SOQL query utilities.
    Implements retry logic for transient API errors.
    """
    
    def __init__(self, sf_client: Salesforce):
        """
        Initialize Salesforce repository.
        
        Args:
            sf_client: Authenticated Salesforce client
        """
        self.sf_client = sf_client
        self._logger = logger
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def _query(self, soql: str) -> List[Dict[str, Any]]:
        """
        Execute SOQL query with retry logic.
        
        Args:
            soql: SOQL query string
            
        Returns:
            List of records
            
        Raises:
            SalesforceAPIError: On API errors
        """
        try:
            self._logger.debug(f"Executing SOQL: {soql}")
            result = self.sf_client.query_all(soql)
            records = result.get('records', [])
            self._logger.info(f"Query returned {len(records)} records")
            return records
        except Exception as e:
            self._logger.error(f"SOQL query failed: {e}")
            raise SalesforceAPIError(f"Query failed: {str(e)}") from e
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=30),
    )
    async def _query_one(self, soql: str) -> Optional[Dict[str, Any]]:
        """
        Execute SOQL query expecting single result.
        
        Args:
            soql: SOQL query string
            
        Returns:
            Single record or None
        """
        records = await self._query(soql)
        return records[0] if records else None
    
    def _build_soql(
        self,
        fields: List[str],
        sobject: str,
        where: Optional[str] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> str:
        """
        Build SOQL query string.
        
        Args:
            fields: List of field names to select
            sobject: Salesforce object name
            where: WHERE clause (without WHERE keyword)
            order_by: ORDER BY clause (without ORDER BY keyword)
            limit: Number of records to limit
            
        Returns:
            Complete SOQL query string
        """
        fields_str = ", ".join(fields)
        query = f"SELECT {fields_str} FROM {sobject}"
        
        if where:
            query += f" WHERE {where}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return query
    
    async def delete(self, id: str) -> bool:
        """
        Salesforce repositories don't support delete.
        
        Raises:
            NotImplementedError: Always raised
        """
        raise NotImplementedError("Salesforce repositories are read-only")
