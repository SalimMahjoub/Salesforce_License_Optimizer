"""
Base repository classes with Generic types.

Provides abstract base classes for Repository pattern implementation
with full async support, retry logic, and error handling.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any
import logging

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from sqlalchemy.exc import OperationalError, DBAPIError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository with generic CRUD operations.
    
    Provides consistent interface for all repositories with
    built-in error handling and logging.
    
    Type parameter T represents the entity type.
    """
    
    @abstractmethod
    async def get_all(self, **filters) -> List[T]:
        """
        Retrieve all entities matching filters.
        
        Args:
            **filters: Field filters to apply
            
        Returns:
            List of entities
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """
        Retrieve single entity by ID.
        
        Args:
            id: Entity identifier
            
        Returns:
            Entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """
        Save entity (create or update).
        
        Args:
            entity: Entity to save
            
        Returns:
            Saved entity with updated fields
        """
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        Delete entity by ID.
        
        Args:
            id: Entity identifier
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    async def get_page(
        self,
        page: int = 1,
        page_size: int = 100,
        **filters
    ) -> tuple[List[T], int]:
        """
        Get paginated results.
        
        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            **filters: Additional filters
            
        Returns:
            Tuple of (items, total_count)
        """
        # Default implementation - subclasses can override for optimization
        all_items = await self.get_all(**filters)
        total = len(all_items)
        
        start = (page - 1) * page_size
        end = start + page_size
        page_items = all_items[start:end]
        
        return page_items, total


class DatabaseRepository(BaseRepository[T], ABC):
    """
    Base repository for database operations using SQLAlchemy.
    
    Adds retry logic for transient database errors and
    connection pool management.
    """
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((OperationalError, DBAPIError)),
        reraise=True,
    )
    async def _execute_with_retry(self, operation):
        """
        Execute database operation with automatic retry.
        
        Retries on transient errors like deadlocks or connection issues.
        """
        try:
            return await operation()
        except (OperationalError, DBAPIError) as e:
            logger.warning(f"Database error, retrying: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in database operation: {e}")
            raise


class CachedRepository(BaseRepository[T], ABC):
    """
    Base repository with caching support.
    
    Adds Redis caching layer for frequently accessed data.
    Subclasses define cache key generation and TTL.
    """
    
    def __init__(self, cache_ttl: int = 300):
        """
        Initialize cached repository.
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default 5 minutes)
        """
        self.cache_ttl = cache_ttl
    
    @abstractmethod
    def _get_cache_key(self, id: str) -> str:
        """Generate cache key for entity ID."""
        pass
    
    @abstractmethod
    async def _get_from_cache(self, key: str) -> Optional[T]:
        """Retrieve entity from cache."""
        pass
    
    @abstractmethod
    async def _set_in_cache(self, key: str, entity: T) -> None:
        """Store entity in cache."""
        pass
    
    @abstractmethod
    async def _invalidate_cache(self, key: str) -> None:
        """Remove entity from cache."""
        pass

