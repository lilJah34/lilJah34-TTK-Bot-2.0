#!/usr/bin/env python3
"""
TTK Bot 2.0 - Scheduler Service
Extracted from main scheduler for service integration
"""

import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from config import get_config
from utils import get_eastern_time

logger = logging.getLogger(__name__)

class TTKBotScheduler:
    """
    Comprehensive job scheduling system for TTK Bot 2.0
    """
    
    def __init__(self):
        self.config = get_config()
        
        # Configure timezone
        self.timezone = pytz.timezone(self.config.scheduler.timezone)
        
        # Configure APScheduler
        self.scheduler = AsyncIOScheduler(
            jobstores={'default': MemoryJobStore()},
            executors={'default': AsyncIOExecutor()},
            job_defaults={
                'coalesce': False,
                'max_instances': self.config.scheduler.max_job_instances,
                'misfire_grace_time': self.config.scheduler.misfire_grace_time_seconds
            },
            timezone=self.timezone
        )
        
        # Data storage
        self.muted_users: Dict[str, datetime] = {}
        self.abandoned_carts: Dict[str, datetime] = {}
        self.fire_sales: Dict[str, datetime] = {}
        self.pending_reups: List[Dict] = []
        
        # Service status
        self.services_running = False
        
        # Load persistent data
        self._load_persistent_data()
    
    def _load_persistent_data(self):
        """Load persistent data from storage"""
        try:
            # Ensure data directory exists
            os.makedirs('data', exist_ok=True)
            
            # Load muted users
            if os.path.exists('data/muted_users.json'):
                with open('data/muted_users.json', 'r') as f:
                    data = json.load(f)
                    self.muted_users = {
                        user_id: datetime.fromisoformat(timestamp)
                        for user_id, timestamp in data.items()
                    }
            
            # Load abandoned carts
            if os.path.exists('data/abandoned_carts.json'):
                with open('data/abandoned_carts.json', 'r') as f:
                    data = json.load(f)
                    self.abandoned_carts = {
                        user_id: datetime.fromisoformat(timestamp)
                        for user_id, timestamp in data.items()
                    }
            
            # Load fire sales
            if os.path.exists('data/fire_sales.json'):
                with open('data/fire_sales.json', 'r') as f:
                    data = json.load(f)
                    self.fire_sales = {
                        sale_id: datetime.fromisoformat(timestamp)
                        for sale_id, timestamp in data.items()
                    }
            
            # Load pending re-ups
            if os.path.exists('data/pending_reups.json'):
                with open('data/pending_reups.json', 'r') as f:
                    self.pending_reups = json.load(f)
            
            logger.info("Loaded scheduler persistent data successfully")
            
        except Exception as e:
            logger.error(f"Error loading scheduler persistent data: {e}")
    
    def _save_persistent_data(self):
        """Save persistent data to storage"""
        try:
            # Ensure data directory exists
            os.makedirs('data', exist_ok=True)
            
            # Save muted users
            muted_data = {
                user_id: timestamp.isoformat()
                for user_id, timestamp in self.muted_users.items()
            }
            with open('data/muted_users.json', 'w') as f:
                json.dump(muted_data, f, indent=2)
            
            # Save abandoned carts
            cart_data = {
                user_id: timestamp.isoformat()
                for user_id, timestamp in self.abandoned_carts.items()
            }
            with open('data/abandoned_carts.json', 'w') as f:
                json.dump(cart_data, f, indent=2)
            
            # Save fire sales
            fire_sale_data = {
                sale_id: timestamp.isoformat()
                for sale_id, timestamp in self.fire_sales.items()
            }
            with open('data/fire_sales.json', 'w') as f:
                json.dump(fire_sale_data, f, indent=2)
            
            # Save pending re-ups
            with open('data/pending_reups.json', 'w') as f:
                json.dump(self.pending_reups, f, indent=2)
            
            logger.info("Saved scheduler persistent data successfully")
            
        except Exception as e:
            logger.error(f"Error saving scheduler persistent data: {e}")
    
    async def auto_save_data(self):
        """Auto-save data every configured interval"""
        logger.info("Running auto-save...")
        self._save_persistent_data()
    
    async def auto_unmute_expired_timers(self):
        """Check and unmute users with expired mute timers"""
        logger.info("Checking for expired mute timers...")
        
        current_time = get_eastern_time()
        expired_users = []
        
        for user_id, mute_end_time in self.muted_users.items():
            if current_time >= mute_end_time:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            try:
                # Remove from muted users
                del self.muted_users[user_id]
                logger.info(f"Unmuted user {user_id} - timer expired")
                
            except Exception as e:
                logger.error(f"Error unmuting user {user_id}: {e}")
        
        if expired_users:
            logger.info(f"Unmuted {len(expired_users)} users with expired timers")
    
    async def cleanup_abandoned_carts(self):
        """Clean up abandoned shopping carts (older than 24 hours)"""
        logger.info("Cleaning up abandoned carts...")
        
        current_time = get_eastern_time()
        cutoff_time = current_time - timedelta(hours=24)
        
        abandoned_users = []
        for user_id, cart_time in self.abandoned_carts.items():
            if cart_time <= cutoff_time:
                abandoned_users.append(user_id)
        
        for user_id in abandoned_users:
            try:
                # Remove abandoned cart
                del self.abandoned_carts[user_id]
                logger.info(f"Cleaned up abandoned cart for user {user_id}")
                
            except Exception as e:
                logger.error(f"Error cleaning up cart for user {user_id}: {e}")
        
        if abandoned_users:
            logger.info(f"Cleaned up {len(abandoned_users)} abandoned carts")
    
    async def schedule_reup_pings(self):
        """Schedule and send re-up reminder pings"""
        logger.info("Processing re-up reminders...")
        
        current_time = get_eastern_time()
        processed_reups = []
        
        for reup in self.pending_reups:
            try:
                reminder_time = datetime.fromisoformat(reup['reminder_time'])
                
                if current_time >= reminder_time:
                    user_id = reup['user_id']
                    product = reup['product']
                    
                    logger.info(f"Re-up reminder due for user {user_id} for {product}")
                    processed_reups.append(reup)
                    
            except Exception as e:
                logger.error(f"Error processing re-up reminder: {e}")
        
        # Remove processed re-ups
        for reup in processed_reups:
            self.pending_reups.remove(reup)
        
        if processed_reups:
            logger.info(f"Processed {len(processed_reups)} re-up reminders")
    
    async def auto_end_fire_sales(self):
        """Auto-end fire sales at 2 AM EST"""
        logger.info("Checking for fire sales to end...")
        
        current_time = get_eastern_time()
        
        # Check if it's 2 AM
        if current_time.hour == 2 and current_time.minute < 10:  # 10-minute window
            ended_sales = []
            
            for sale_id, start_time in self.fire_sales.items():
                try:
                    logger.info(f"Auto-ending fire sale {sale_id}")
                    ended_sales.append(sale_id)
                    
                except Exception as e:
                    logger.error(f"Error ending fire sale {sale_id}: {e}")
            
            # Remove ended sales
            for sale_id in ended_sales:
                del self.fire_sales[sale_id]
            
            if ended_sales:
                logger.info(f"Auto-ended {len(ended_sales)} fire sales")
    
    async def system_health_check(self):
        """Perform system health checks"""
        logger.info("Performing system health check...")
        
        try:
            total_muted = len(self.muted_users)
            total_carts = len(self.abandoned_carts)
            total_reups = len(self.pending_reups)
            total_sales = len(self.fire_sales)
            
            logger.info(f"Scheduler status: {total_muted} muted users, {total_carts} carts, "
                       f"{total_reups} pending re-ups, {total_sales} active fire sales")
            
        except Exception as e:
            logger.error(f"Error in system health check: {e}")
    
    def add_mute_timer(self, user_id: str, duration_minutes: int):
        """Add a user to mute timer"""
        mute_end_time = get_eastern_time() + timedelta(minutes=duration_minutes)
        self.muted_users[user_id] = mute_end_time
        logger.info(f"Added mute timer for user {user_id} until {mute_end_time}")
    
    def add_abandoned_cart(self, user_id: str):
        """Mark a cart as abandoned"""
        self.abandoned_carts[user_id] = get_eastern_time()
        logger.info(f"Marked cart as abandoned for user {user_id}")
    
    def add_reup_reminder(self, user_id: str, product: str, days_ahead: int = 7):
        """Schedule a re-up reminder"""
        reminder_time = get_eastern_time() + timedelta(days=days_ahead)
        
        reup_data = {
            'user_id': user_id,
            'product': product,
            'reminder_time': reminder_time.isoformat(),
            'created_at': get_eastern_time().isoformat()
        }
        
        self.pending_reups.append(reup_data)
        logger.info(f"Scheduled re-up reminder for user {user_id} - {product} in {days_ahead} days")
    
    def start_fire_sale(self, sale_id: str):
        """Start a fire sale"""
        self.fire_sales[sale_id] = get_eastern_time()
        logger.info(f"Started fire sale {sale_id}")
    
    def setup_scheduled_jobs(self):
        """Set up all scheduled jobs"""
        try:
            # Auto-save every configured interval
            self.scheduler.add_job(
                self.auto_save_data,
                trigger=IntervalTrigger(minutes=self.config.scheduler.auto_save_interval_minutes),
                id='auto_save',
                name='Auto-save data',
                replace_existing=True
            )
            
            # Check mute timers every minute
            self.scheduler.add_job(
                self.auto_unmute_expired_timers,
                trigger=IntervalTrigger(minutes=1),
                id='unmute_check',
                name='Check for expired mute timers',
                replace_existing=True
            )
            
            # Clean up abandoned carts every hour
            self.scheduler.add_job(
                self.cleanup_abandoned_carts,
                trigger=IntervalTrigger(hours=1),
                id='cart_cleanup',
                name='Clean up abandoned carts',
                replace_existing=True
            )
            
            # Check re-up reminders every 30 minutes
            self.scheduler.add_job(
                self.schedule_reup_pings,
                trigger=IntervalTrigger(minutes=30),
                id='reup_reminders',
                name='Process re-up reminders',
                replace_existing=True
            )
            
            # Auto-end fire sales at 2 AM EST daily
            self.scheduler.add_job(
                self.auto_end_fire_sales,
                trigger=CronTrigger(hour=2, minute=0, timezone=self.timezone),
                id='end_fire_sales',
                name='Auto-end fire sales at 2 AM EST',
                replace_existing=True
            )
            
            # System health check every configured interval
            self.scheduler.add_job(
                self.system_health_check,
                trigger=IntervalTrigger(minutes=self.config.scheduler.health_check_interval_minutes),
                id='health_check',
                name='System health check',
                replace_existing=True
            )
            
            logger.info("Scheduled jobs configured successfully")
            
        except Exception as e:
            logger.error(f"Error setting up scheduled jobs: {e}")
    
    async def start_services(self):
        """Start all services and schedulers"""
        try:
            logger.info("Starting TTK Bot 2.0 scheduler services...")
            
            # Set up scheduled jobs
            self.setup_scheduled_jobs()
            
            # Start scheduler
            self.scheduler.start()
            logger.info("Scheduler started successfully")
            
            # Mark services as running
            self.services_running = True
            
            logger.info("🚀 TTK Bot 2.0 scheduler services started successfully!")
            
        except Exception as e:
            logger.error(f"Error starting scheduler services: {e}")
            raise
    
    async def stop_services(self):
        """Stop all services gracefully"""
        try:
            logger.info("Stopping TTK Bot 2.0 scheduler services...")
            
            # Save data before shutdown
            self._save_persistent_data()
            
            # Stop scheduler
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                logger.info("Scheduler stopped")
            
            # Mark services as stopped
            self.services_running = False
            
            logger.info("TTK Bot 2.0 scheduler services stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping scheduler services: {e}")
