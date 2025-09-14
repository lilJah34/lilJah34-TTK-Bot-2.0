#!/usr/bin/env python3
"""
TTK Bot 2.0 - Integrated Main Application
Coordinates Telegram bot with infrastructure services
"""

import asyncio
import logging
import signal
import sys
import threading
import time
import os
import atexit
from datetime import datetime
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Import handlers
from handlers.command_handlers import start, menu, cart, admin, notifications, addproduct, help_command
from handlers.callback_handlers import handle_callback_query
from handlers.message_handlers import handle_message

# Import infrastructure components
from config import get_config, get_telegram_config
from data_manager import DataManager
from location_service import run_location_service, location_service
from utils import safe_execute_async, get_eastern_time
import utils

# Configure logging
config = get_config()
logging.basicConfig(
    level=getattr(logging, config.logging.level),
    format=config.logging.format_string,
    handlers=[
        logging.FileHandler(config.logging.file_path) if config.logging.file_path else logging.NullHandler(),
        logging.StreamHandler(sys.stdout) if config.logging.enable_console else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

class SingletonGuard:
    """Prevent multiple bot instances from running simultaneously"""
    
    def __init__(self, lock_file="ttk_bot.pid"):
        self.lock_file = lock_file
        self.pid = str(os.getpid())
    
    def __enter__(self):
        # Check if lock file exists and process is still running
        if os.path.exists(self.lock_file):
            try:
                with open(self.lock_file, 'r') as f:
                    old_pid = f.read().strip()
                
                # Check if process is still running (Windows)
                try:
                    import subprocess
                    result = subprocess.run(['tasklist', '/FI', f'PID eq {old_pid}'], 
                                         capture_output=True, text=True)
                    if old_pid in result.stdout:
                        logger.error(f"Another TTK Bot instance is already running (PID: {old_pid})")
                        logger.error("Please stop the existing instance before starting a new one.")
                        sys.exit(1)
                    else:
                        logger.info(f"Stale PID file found (PID {old_pid} not running), removing...")
                        os.remove(self.lock_file)
                except Exception as e:
                    logger.warning(f"Could not check if process {old_pid} is running: {e}")
                    # Remove stale lock file if we can't verify
                    os.remove(self.lock_file)
                    
            except Exception as e:
                logger.error(f"Error reading lock file: {e}")
                sys.exit(1)
        
        # Create new lock file with current PID
        try:
            with open(self.lock_file, 'w') as f:
                f.write(self.pid)
            logger.info(f"Created lock file with PID: {self.pid}")
            
            # Register cleanup function
            atexit.register(self.cleanup)
            
        except Exception as e:
            logger.error(f"Could not create lock file: {e}")
            sys.exit(1)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def cleanup(self):
        """Clean up the lock file"""
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
                logger.info("Cleaned up lock file")
        except Exception as e:
            logger.error(f"Error cleaning up lock file: {e}")

class TTKBotApplication:
    """Integrated TTK Bot application with infrastructure services"""
    
    def __init__(self):
        self.config = get_config()
        self.telegram_config = get_telegram_config()
        self.data_manager = DataManager()
        
        # Service threads
        self.location_service_thread = None
        self.scheduler_thread = None
        
        # Application state
        self.running = False
        self.telegram_app = None
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load persistent data"""
        try:
            self.data_manager.load_from_file()
            logger.info("Loaded existing data successfully")
        except Exception as e:
            logger.warning(f"Could not load existing data: {e}")
            logger.info("Starting with fresh data")
    
    def _setup_telegram_bot(self):
        """Set up the Telegram bot application"""
        try:
            # Get bot token from config or environment
            bot_token = self.telegram_config.bot_token
            if not bot_token:
                # Fallback to hardcoded token from launch instructions
                bot_token = "8306498479:AAHOIrEZ64jOYcsP70K07_yb2n_Y9w1VMF0"
                logger.warning("Using fallback bot token")
            
    # Create application
            self.telegram_app = Application.builder().token(bot_token).build()
            
            # Add command handlers
            self.telegram_app.add_handler(CommandHandler("start", start))
            self.telegram_app.add_handler(CommandHandler("menu", menu))
            self.telegram_app.add_handler(CommandHandler("cart", cart))
            self.telegram_app.add_handler(CommandHandler("admin", admin))
            self.telegram_app.add_handler(CommandHandler("notifications", notifications))
            self.telegram_app.add_handler(CommandHandler("addproduct", addproduct))
            self.telegram_app.add_handler(CommandHandler("help", help_command))
            
            # Add callback and message handlers
            self.telegram_app.add_handler(CallbackQueryHandler(handle_callback_query))
            self.telegram_app.add_handler(MessageHandler(
                filters.TEXT | filters.PHOTO | filters.VIDEO | filters.ANIMATION, 
        handle_message
    ))
    
            logger.info("Telegram bot configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Telegram bot: {e}")
            return False
    
    def _start_location_service(self):
        """Start the location service in a separate thread"""
        try:
            def location_service_target():
                run_location_service(
                    host=self.config.location.service_host,
                    port=self.config.location.service_port,
                    debug=self.config.debug_mode
                )
            
            self.location_service_thread = threading.Thread(
                target=location_service_target,
                daemon=True,
                name="LocationService"
            )
            self.location_service_thread.start()
            
            # Wait a moment to ensure it starts
            time.sleep(2)
            
            if self.location_service_thread.is_alive():
                logger.info(f"Location service started on port {self.config.location.service_port}")
                return True
            else:
                logger.error("Location service failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Error starting location service: {e}")
            return False
    
    def _start_scheduler_service(self):
        """Start the job scheduler service"""
        try:
            # Import scheduler - skip if not available
            try:
                from scheduler_service import TTKBotScheduler
            except ImportError:
                logger.warning("Scheduler service not available")
                return False
            
            def scheduler_target():
                scheduler = TTKBotScheduler()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(scheduler.start_services())
                    # Keep running
                    while self.running:
                        loop.run_until_complete(asyncio.sleep(1))
                except Exception as e:
                    logger.error(f"Scheduler error: {e}")
                finally:
                    loop.run_until_complete(scheduler.stop_services())
                    loop.close()
            
            self.scheduler_thread = threading.Thread(
                target=scheduler_target,
                daemon=True,
                name="SchedulerService"
            )
            self.scheduler_thread.start()
            
            logger.info("Scheduler service started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting scheduler service: {e}")
            return False
    
    async def _periodic_save(self):
        """Periodic data saving"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Save every 5 minutes
                await safe_execute_async(
                    self.data_manager.save_to_file,
                    default_return=False,
                    log_errors=True
                )
            except Exception as e:
                logger.error(f"Error in periodic save: {e}")
    
    async def start_all_services(self):
        """Start all services"""
        try:
            logger.info("🚀 Starting TTK Bot 2.0 with infrastructure services...")
            
            # Mark as running
            self.running = True
            
            # Start location service
            if not self._start_location_service():
                logger.warning("Location service failed to start, continuing without it")
            
            # Start scheduler service (if available)
            if not self._start_scheduler_service():
                logger.warning("Scheduler service failed to start, continuing without it")
            
            # Set up Telegram bot
            if not self._setup_telegram_bot():
                logger.error("Failed to set up Telegram bot")
                return False
            
            # Start periodic data saving
            asyncio.create_task(self._periodic_save())
            
            logger.info("✅ All services started successfully!")
            logger.info("🤖 TTK Bot 2.0 is now running...")
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting services: {e}")
            return False
    
    async def stop_all_services(self):
        """Stop all services gracefully"""
        try:
            logger.info("Stopping TTK Bot 2.0 services...")
            
            # Mark as not running
            self.running = False
            
            # Save data before shutdown
            await safe_execute_async(
                self.data_manager.save_to_file,
                default_return=False,
                log_errors=True
            )
            
            # Stop Telegram bot with proper cleanup
            if self.telegram_app:
                try:
                    # Stop polling first
                    if hasattr(self.telegram_app, 'updater') and self.telegram_app.updater:
                        await self.telegram_app.updater.stop()
                        logger.info("Telegram updater stopped")
                    
                    # Then stop the application
                    await self.telegram_app.stop()
                    logger.info("Telegram application stopped")
                    
                    # Finally shutdown completely
                    await self.telegram_app.shutdown()
                    logger.info("Telegram bot shutdown complete")
                    
                except Exception as e:
                    logger.error(f"Error stopping Telegram bot: {e}")
            
            logger.info("✅ TTK Bot 2.0 stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping services: {e}")
    
    def run(self):
        """Run the application"""
        async def main_loop():
            def signal_handler(signum, frame):
                logger.info(f"Received signal {signum}, shutting down...")
                asyncio.create_task(self.stop_all_services())
                sys.exit(0)
            
            # Register signal handlers
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            try:
                # Start all services
                if not await self.start_all_services():
                    logger.error("Failed to start services")
                    return
                
                # Run the Telegram bot
                if self.telegram_app:
                    logger.info("Starting Telegram bot polling...")
                    await self.telegram_app.initialize()
                    await self.telegram_app.start()
                    await self.telegram_app.updater.start_polling()
                    
                    # Keep running until interrupted
                    try:
                        while self.running:
                            await asyncio.sleep(1)
                    finally:
                        await self.telegram_app.updater.stop()
                        await self.telegram_app.stop()
                        await self.telegram_app.shutdown()
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
            finally:
                await self.stop_all_services()
        
        # Run the main loop
        asyncio.run(main_loop())

def main():
    """Main entry point with singleton protection"""
    with SingletonGuard():
        try:
            logger.info("🚀 Starting TTK Bot 2.0 with singleton protection...")
            app = TTKBotApplication()
            app.run()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user (Ctrl+C)")
        except Exception as e:
            logger.error(f"Critical error in main: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()