from sqlalchemy import Column, Integer, ForeignKey, Table
from .base import Base

# Association table for many-to-many relationship between plans and rules
plan_rules = Table(
    'plan_rules', Base.metadata,
    Column('plan_id', Integer, ForeignKey('plans.id'), primary_key=True),
    Column('rule_id', Integer, ForeignKey('rules.id'), primary_key=True)
)