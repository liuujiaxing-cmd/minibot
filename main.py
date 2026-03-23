import asyncio
import sys
import os

from apscheduler.triggers.cron import CronTrigger

# Ensure the minibot package is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minibot.agent import agent
from minibot.config import config
from minibot.connectors.console import ConsoleConnector
from minibot.connectors.telegram import TelegramConnector
from minibot.modules.scheduler import scheduler
from minibot.modules.daily_journal import daily_journal

async def main():
    """Main entry point for Minibot."""
    print(f"Initializing Minibot ({config.bot_name})...")
    
    # Start the scheduler
    scheduler.start()

    if daily_journal:
        asyncio.create_task(daily_journal.finalize_overdue())
        scheduler.scheduler.add_job(
            daily_journal.finalize_previous_day,
            CronTrigger(hour=0, minute=5),
            id="daily_finalize",
            name="daily_finalize",
            replace_existing=True,
        )
    
    tasks = []
    
    # Always run console connector
    console = ConsoleConnector(agent)
    tasks.append(asyncio.create_task(console.start()))
    
    # Run Telegram connector if configured
    if config.telegram_token:
        telegram = TelegramConnector(agent, config.telegram_token)
        tasks.append(asyncio.create_task(telegram.start()))
    
    # You can add more connectors here (Discord, Slack, etc.)
        
    print("Minibot is running. Press Ctrl+C to stop.")
    
    try:
        # Wait for all connectors to complete (usually they run forever)
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMinibot stopped.")
