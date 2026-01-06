import asyncio
import math
import discord
import schedule

from discord import Message, User, NotFound, Client

from config.base import Config
from debug import debug_msg

class Notis():
    def __init__(self, bot: Client, cfg: Config):
        self.cfg: Config = cfg
        self.bot: Client = bot

        self.msgs: list[Message] = []

        self.is_checking = False
        self.currently_in_check = False

        self.first_run = True

        self.recheck_job = None
        self.snooze_job = None

        self.snoozes = 0

        self.fetch_cfg()

    def fetch_cfg(self):
        cfg = self.cfg

        self.verbose = cfg.Debug.verbose

        self.channel_id = cfg.Bot.channel_id
        self.user_id = cfg.Bot.user_id

        self.timezone = cfg.Alert.timezone
        self.snooze_time = cfg.Alert.snooze_time
        self.times = cfg.Alert.times
        self.max_snoozes = cfg.Alert.max_snoozes

    async def init_notis(self):
        timezone = self.timezone

        #schedule.every(5).seconds.do(lambda: asyncio.create_task(self.alert_user()))

        for t in self.times:
            print(f"Scheduling notification at {t} ({timezone})...")

            schedule.every().day.at(t, timezone).do(lambda: asyncio.create_task(self.alert_user()))

    async def check_notis(self):
        while True:
            schedule.run_pending()

            await asyncio.sleep(1)

    async def alert_user(self, snooze = False):
        bot = self.bot
        cfg = self.cfg

        if cfg.Alert.wait_for_prev_ack and self.is_checking and not snooze:
            debug_msg(cfg, 2, "Previous alert not yet acknowledged. Skipping new alert...")

            return

        await bot.wait_until_ready()

        channel_id = int(self.channel_id)
        user_id = self.user_id

        channel = bot.get_channel(channel_id)
        user = await bot.fetch_user(user_id)

        if channel is None:
            debug_msg(self.cfg, 0, f"Channel with ID {channel_id} not found.")

            return

        if user is None:
            debug_msg(self.cfg, 0, f"User with ID {user_id} not found.")

            return
        
        debug_msg(self.cfg, 1, f"Notifying user '{user.name}' (ID: {user.id})...")

        msgF = cfg.Alert.alert_msg.format(m=user.mention, n = user.name)

        if snooze:
            msgF = cfg.Alert.alert_msg_snooze.format(m=user.mention, n = user.name, min = math.ceil(self.snooze_time / 60), sec = self.snooze_time)

        msg = await channel.send(msgF)

        # Add message ID to list.
        self.msgs.append(msg)

        if self.is_checking and not self.first_run:
                debug_msg(self.cfg, 1, "WARNING: Notification sent, but check already in progress...")

        if self.first_run:
            self.first_run = False

        if not snooze and not self.is_checking:
            if self.recheck_job is not None:
                schedule.cancel_job(self.recheck_job)

            if self.snooze_job is not None:
                schedule.cancel_job(self.snooze_job)

            self.is_checking = True

            self.recheck_job = schedule.every(1).seconds.do(lambda: asyncio.create_task(self.wait_for_reaction_or_snooze(user)))

            self.snooze_job = schedule.every(self.snooze_time).seconds.do(lambda: asyncio.create_task(self.snooze(user)))

    async def wait_for_reaction_or_snooze(self, user: User):
        cfg = self.cfg

        max_snoozes = self.max_snoozes

        if self.currently_in_check:
                return
            
        self.currently_in_check = True

        if len(self.msgs) == 0:
            debug_msg(cfg, 2, "No more messages to check. Stopping recheck job...")

            self.cancel_recheck_job()

            return

        debug_msg(cfg, 2, f"Rechecking messages(Snooze count: {self.snoozes}/{max_snoozes})...")

        # Look through all tracked messages.
        for i, msg in enumerate(self.msgs):
            try:
                if msg in self.msgs:
                    msg = await msg.channel.fetch_message(msg.id)
                    self.msgs[i] = msg
            except NotFound:
                self.msgs.remove(msg)

                continue
            except Exception as e:
                if msg in self.msgs:
                    self.msgs.remove(msg)

                debug_msg(cfg, 3, f"Error fetching message ID {msg.id}: {e}")

                continue

            reactionCnt = len(msg.reactions)

            debug_msg(cfg, 3, f"Checking reactions for message ID {msg.id} ({reactionCnt})...\n")

            if reactionCnt > 0:
                for reaction in msg.reactions:
                    debug_msg(cfg, 3, f"Checking users for reaction {reaction.emoji}...\n")

                    async for rUsr in reaction.users():
                        # Exclude bot.
                        if rUsr == self.bot.user:
                            continue

                        found = False

                        if rUsr == user:
                            debug_msg(cfg, 1, f"{user.name} has acknowledged the alert!")

                            await msg.channel.send(cfg.Alert.alert_msg_ack.format(m=user.mention, n = user.name))

                            self.cancel_recheck_job()

                            found = True

                            break
                    if found:
                        break
        
        # Check for max snoozes.
        if max_snoozes > 0 and self.snoozes >= max_snoozes:
            debug_msg(cfg, 1, "Max snoozes reached. Stopping notifications...")

            snoozeMsg = cfg.Alert.alert_msg_max_snoozes.format(m=user.mention, n = user.name, max_snoozes = max_snoozes)

            await msg.channel.send(snoozeMsg)

            self.cancel_recheck_job()

        self.currently_in_check = False
    
    async def snooze(self, user: User):
        if not self.is_checking:
            return
        
        max_snoozes = self.max_snoozes
        
        self.snoozes += 1

        # Shouldn't get here.
        if max_snoozes > 0 and self.snoozes >= max_snoozes:
            debug_msg(self.cfg, 1, "Max snoozes reached in snooze job. Stopping notifications...")

            self.cancel_recheck_job()

            return
        
        debug_msg(self.cfg, 2, f"Snooze time reached. Sending another notification to {user.name}...")
        
        await self.alert_user(snooze=True)
        
    def cancel_recheck_job(self):
        self.is_checking = False

        # Clear current messages and snoozes count.
        self.msgs = []        

        self.snoozes = 0

        try:
            if self.recheck_job is not None:
                schedule.cancel_job(self.recheck_job)
                self.recheck_job = None
        except Exception as e:
            debug_msg(self.cfg, 0, f"Error cancelling recheck job: {e}")

        try:
            if self.snooze_job is not None:
                schedule.cancel_job(self.snooze_job)
                self.snooze_job = None
        except Exception as e:
            debug_msg(self.cfg, 0, f"Error cancelling snooze job: {e}")
            
        