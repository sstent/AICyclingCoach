"""
Rule service for TUI application.
Manages training rules without HTTP dependencies.
"""
from typing import Dict, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.rule import Rule


class RuleService:
    """Service for training rule operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_rules(self) -> List[Dict]:
        """Get all training rules."""
        try:
            result = await self.db.execute(
                select(Rule).order_by(desc(Rule.created_at))
            )
            rules = result.scalars().all()
            
            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "user_defined": r.user_defined,
                    "rule_text": r.rule_text,
                    "version": r.version,
                    "parent_rule_id": r.parent_rule_id,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                } for r in rules
            ]
            
        except Exception as e:
            raise Exception(f"Error fetching rules: {str(e)}")
    
    async def get_rule(self, rule_id: int) -> Optional[Dict]:
        """Get a specific rule by ID."""
        try:
            rule = await self.db.get(Rule, rule_id)
            if not rule:
                return None
                
            return {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "user_defined": rule.user_defined,
                "rule_text": rule.rule_text,
                "version": rule.version,
                "parent_rule_id": rule.parent_rule_id,
                "created_at": rule.created_at.isoformat() if rule.created_at else None
            }
            
        except Exception as e:
            raise Exception(f"Error fetching rule {rule_id}: {str(e)}")
    
    async def create_rule(
        self, 
        name: str, 
        rule_text: str, 
        description: Optional[str] = None,
        user_defined: bool = True,
        version: int = 1,
        parent_rule_id: Optional[int] = None
    ) -> Dict:
        """Create a new training rule."""
        try:
            db_rule = Rule(
                name=name,
                description=description,
                user_defined=user_defined,
                rule_text=rule_text,
                version=version,
                parent_rule_id=parent_rule_id
            )
            self.db.add(db_rule)
            await self.db.commit()
            await self.db.refresh(db_rule)
            
            return {
                "id": db_rule.id,
                "name": db_rule.name,
                "description": db_rule.description,
                "user_defined": db_rule.user_defined,
                "rule_text": db_rule.rule_text,
                "version": db_rule.version,
                "parent_rule_id": db_rule.parent_rule_id,
                "created_at": db_rule.created_at.isoformat() if db_rule.created_at else None
            }
            
        except Exception as e:
            raise Exception(f"Error creating rule: {str(e)}")
    
    async def update_rule(
        self,
        rule_id: int,
        name: Optional[str] = None,
        rule_text: Optional[str] = None,
        description: Optional[str] = None,
        version: Optional[int] = None
    ) -> Dict:
        """Update an existing rule."""
        try:
            db_rule = await self.db.get(Rule, rule_id)
            if not db_rule:
                raise Exception("Rule not found")
            
            if name is not None:
                db_rule.name = name
            if rule_text is not None:
                db_rule.rule_text = rule_text
            if description is not None:
                db_rule.description = description
            if version is not None:
                db_rule.version = version
            
            await self.db.commit()
            await self.db.refresh(db_rule)
            
            return {
                "id": db_rule.id,
                "name": db_rule.name,
                "description": db_rule.description,
                "user_defined": db_rule.user_defined,
                "rule_text": db_rule.rule_text,
                "version": db_rule.version,
                "parent_rule_id": db_rule.parent_rule_id,
                "created_at": db_rule.created_at.isoformat() if db_rule.created_at else None
            }
            
        except Exception as e:
            raise Exception(f"Error updating rule: {str(e)}")
    
    async def delete_rule(self, rule_id: int) -> Dict:
        """Delete a rule."""
        try:
            rule = await self.db.get(Rule, rule_id)
            if not rule:
                raise Exception("Rule not found")
            
            await self.db.delete(rule)
            await self.db.commit()
            
            return {"message": "Rule deleted successfully"}
            
        except Exception as e:
            raise Exception(f"Error deleting rule: {str(e)}")
    
    async def get_user_defined_rules(self) -> List[Dict]:
        """Get only user-defined rules."""
        try:
            result = await self.db.execute(
                select(Rule)
                .where(Rule.user_defined == True)
                .order_by(desc(Rule.created_at))
            )
            rules = result.scalars().all()
            
            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "rule_text": r.rule_text,
                    "version": r.version,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                } for r in rules
            ]
            
        except Exception as e:
            raise Exception(f"Error fetching user-defined rules: {str(e)}")
    
    async def get_system_rules(self) -> List[Dict]:
        """Get only system-defined rules."""
        try:
            result = await self.db.execute(
                select(Rule)
                .where(Rule.user_defined == False)
                .order_by(desc(Rule.created_at))
            )
            rules = result.scalars().all()
            
            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "rule_text": r.rule_text,
                    "version": r.version,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                } for r in rules
            ]
            
        except Exception as e:
            raise Exception(f"Error fetching system rules: {str(e)}")
    
    async def create_rule_version(self, parent_rule_id: int, rule_text: str, description: Optional[str] = None) -> Dict:
        """Create a new version of an existing rule."""
        try:
            parent_rule = await self.db.get(Rule, parent_rule_id)
            if not parent_rule:
                raise Exception("Parent rule not found")
            
            # Get the highest version number for this rule family
            result = await self.db.execute(
                select(Rule.version)
                .where(Rule.parent_rule_id == parent_rule_id)
                .order_by(desc(Rule.version))
                .limit(1)
            )
            max_version = result.scalar_one_or_none() or parent_rule.version
            new_version = max_version + 1
            
            new_rule = Rule(
                name=parent_rule.name,
                description=description or parent_rule.description,
                user_defined=parent_rule.user_defined,
                rule_text=rule_text,
                version=new_version,
                parent_rule_id=parent_rule_id
            )
            self.db.add(new_rule)
            await self.db.commit()
            await self.db.refresh(new_rule)
            
            return {
                "id": new_rule.id,
                "name": new_rule.name,
                "description": new_rule.description,
                "user_defined": new_rule.user_defined,
                "rule_text": new_rule.rule_text,
                "version": new_rule.version,
                "parent_rule_id": new_rule.parent_rule_id,
                "created_at": new_rule.created_at.isoformat() if new_rule.created_at else None
            }
            
        except Exception as e:
            raise Exception(f"Error creating rule version: {str(e)}")