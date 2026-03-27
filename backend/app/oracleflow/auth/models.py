from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.oracleflow.models.base import Base

class Organization(Base):
    __tablename__ = 'organizations'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    plan = Column(String(50), default='free')  # free/scout/strategist/commander/sovereign
    stripe_customer_id = Column(String(200))
    max_users = Column(Integer, default=1)
    max_sites = Column(Integer, default=1)
    max_simulations_per_month = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    users = relationship('User', back_populates='organization')
    subscriptions = relationship('Subscription', back_populates='organization')

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(200), nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    role = Column(String(50), default='admin')  # admin/member/viewer
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime)
    organization = relationship('Organization', back_populates='users')

class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    stripe_subscription_id = Column(String(200))
    plan = Column(String(50), nullable=False)
    status = Column(String(50), default='active')  # active/cancelled/past_due
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    monthly_price = Column(Float, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    organization = relationship('Organization', back_populates='subscriptions')

# Plan limits
PLAN_LIMITS = {
    'free':       {'max_users': 1,   'max_sites': 3,   'max_simulations': 3,   'max_panels': 10, 'max_categories': 5, 'price': 0},
    'scout':      {'max_users': 1,   'max_sites': 2,   'max_simulations': 3,   'max_panels': 10, 'max_categories': 5, 'price': 49},
    'strategist': {'max_users': 3,   'max_sites': 5,   'max_simulations': 10,  'max_panels': 15, 'max_categories': 8, 'price': 199},
    'commander':  {'max_users': 10,  'max_sites': 25,  'max_simulations': 50,  'max_panels': 30, 'max_categories': 12, 'price': 999},
    'sovereign':  {'max_users': 999, 'max_sites': 999, 'max_simulations': 999, 'max_panels': 999, 'max_categories': 12, 'price': 5000},
}


class UserPreferences(Base):
    __tablename__ = 'user_preferences'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False, index=True)
    persona_shortcut = Column(String(50), nullable=True)  # trader, political, security, corporate, humanitarian, custom
    interest_categories = Column(JSON, default=list)  # ["finance", "cyber", ...]
    dashboard_config = Column(JSON, default=dict)  # {panel_order: [...], removed_panels: [...]}
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
