"""
Base Repository Pattern Implementation
Provides common CRUD operations for all repositories
"""

from typing import Generic, TypeVar, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Base repository providing common CRUD operations"""
    
    def __init__(self, db: Session, model: type[T]):
        self.db = db
        self.model = model
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get entity by ID"""
        return await self.db.query(self.model).filter(
            self.model.id == id
        ).first()
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all entities with pagination"""
        return await self.db.query(self.model).offset(offset).limit(limit).all()
    
    async def create(self, data: Dict[str, Any]) -> T:
        """Create new entity"""
        entity = self.model(**data)
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """Update entity"""
        entity = await self.get_by_id(id)
        if not entity:
            return None
        
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        await self.db.commit()
        await self.db.refresh(entity)
        return entity
    
    async def delete(self, id: str) -> bool:
        """Delete entity"""
        entity = await self.get_by_id(id)
        if not entity:
            return False
        
        await self.db.delete(entity)
        await self.db.commit()
        return True
    
    async def count(self) -> int:
        """Count all entities"""
        return await self.db.query(self.model).count()
