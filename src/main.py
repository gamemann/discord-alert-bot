import asyncio

import discord

from bot import Bot
from config.base import Config

from debug.utils import debug_msg
from notify import Notis

async def main():
    cfg_path = "./settings.json"
    list = False

    for k, arg in enumerate(asyncio.sys.argv):
        if (arg == '--cfg' or arg == '-c') and k + 1 < len(asyncio.sys.argv):
            cfg_path = asyncio.sys.argv[k + 1]
            
            continue

        if (arg == '--list' or arg == '-l'):
            list = True
            
            continue
    try:
        cfg = Config(cfg_path)

        cfg.load_from_fs()
    except Exception as e:
        raise RuntimeError("Failed to load configuration from file system.") from e
    
    if list:
        cfg.print()
        
        return
    
    bot_settings = cfg.Bot

    if bot_settings.token is None:
        raise ValueError("Token not found in configuration.")
    
    if bot_settings.channel_id is None:
        raise ValueError("Channel ID not found in configuration.")
    
    if bot_settings.user_id is None:
        raise ValueError("User ID not found in configuration.")
    
    if cfg.General.save_locally:
        try:
            debug_msg(cfg, 2, "Saving configuration locally...")

            cfg.save_to_fs()
        except Exception as e:
            debug_msg(cfg, 1, "Failed to save configuration to file system: " + str(e))

    try:
        bot = Bot(token=bot_settings.token, intents=discord.Intents.all())

        asyncio.create_task(bot.connect_and_run())
    except Exception as e:
        raise RuntimeError("Failed to initialize or run the bot.") from e
    
    debug_msg(cfg, 1, "Discord bot connected...")

    alert_settings = cfg.Alert

    # Initialize notifications class.
    notis = Notis(bot=bot, cfg=cfg)

    # Create jobs.
    debug_msg(cfg, 2, "Creating notification jobs...")

    await notis.init_notis()

    # Start checking for notifications to send.
    debug_msg(cfg, 2, "Checking for notifications...")

    try:
        await notis.check_notis()
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass
    except Exception as e:
        raise RuntimeError("Failed during notification checking.") from e

    debug_msg(cfg, 1, "Bot exiting...")

if __name__ == '__main__':
    asyncio.run(main())