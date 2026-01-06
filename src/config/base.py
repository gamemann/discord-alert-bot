import json

from utils.file import safe_write

class DebugSettings():
    def __init__(self):
        self.verbose = 1
        self.log_to_file = False
        self.log_dir = "./logs"
        
    def as_json(self):
        return {
            "verbose": self.verbose,
            "log_to_file": self.log_to_file,
            "log_dir": self.log_dir
        }
    
class General():
    def __init__(self):
        self.save_locally = True

    def as_json(self):
        return {
            "save_locally": self.save_locally
        }
    
class bot_settings():
    def __init__(self):
        self.token: str = None
        self.channel_id: str = None
        self.user_id: str = None

        self.first_emoji = '⏰'
        
    def as_json(self):
        return {
            "token": self.token,
            "channel_id": self.channel_id,
            "user_id": self.user_id,
            "first_emoji": self.first_emoji
        }

class alert_settings():
    def __init__(self):
        self.timezone: str = 'America/Los_Angeles'
        self.snooze_time: int = 1800 
        self.times: list[str] = ["08:00"]
        self.max_snoozes: int = 10

        self.alert_msg = "{m} Timer up {n}!!!"
        self.alert_msg_snooze = "{m} Snoozed {min} minutes, {n}. Will alert again in {sec} seconds."
        self.alert_msg_ack = "{m} Alert acknowledged, {n}!"
        self.alert_msg_max_snoozes = "{m} Max snoozes reached ({max_snoozes}). Alert dismissed for {n}."

        self.wait_for_prev_ack: bool = True
        
    def as_json(self):
        return {
            "timezone": self.timezone,
            "snooze_time": self.snooze_time,
            "times": self.times,
            "max_snoozes": self.max_snoozes,
            "alert_msg": self.alert_msg,
            "alert_msg_snooze": self.alert_msg_snooze,
            "alert_msg_ack": self.alert_msg_ack,
            "alert_msg_max_snoozes": self.alert_msg_max_snoozes,
            "wait_for_prev_ack": self.wait_for_prev_ack
        }
    
class Config():
    def __init__(self, path = "./settings.json"):
        self.path = path

        self.Debug = DebugSettings()
        self.General = General()
        self.Bot = bot_settings()
        self.Alert = alert_settings()

    def as_json(self):
        return {
            "debug": self.Debug.as_json(),
            "general": self.General.as_json(),
            "bot": self.Bot.as_json(),
            "alert": self.Alert.as_json()
        }

    def load_from_fs(self):
        data = {}
        
        with open(self.path) as f:
            data = json.load(f)
            
        if data is None:
            raise Exception("JSON data is None.")
        
        # Debug settings.
        if "debug" in data:
            debug = data["debug"]
            
            self.Debug.verbose = debug.get("verbose", self.Debug.verbose)
            self.Debug.log_to_file = debug.get("log_to_file", self.Debug.log_to_file)
            self.Debug.log_dir = debug.get("log_dir", self.Debug.log_dir)

        # General settings.
        if "general" in data:
            general = data["general"]
            
            self.General.save_locally = general.get("save_locally", self.General.save_locally)

        # Bot settings.
        if "bot" in data:
            bot = data["bot"]
            
            self.Bot.token = bot.get("token", self.Bot.token)
            self.Bot.channel_id = bot.get("channel_id", self.Bot.channel_id)
            self.Bot.user_id = bot.get("user_id", self.Bot.user_id)

            self.Bot.first_emoji = bot.get("first_emoji", self.Bot.first_emoji)

        # Alert settings.
        if "alert" in data:
            alert = data["alert"]
            
            self.Alert.timezone = alert.get("timezone", self.Alert.timezone)
            self.Alert.snooze_time = alert.get("snooze_time", self.Alert.snooze_time)
            self.Alert.times = alert.get("times", self.Alert.times)
            self.Alert.max_snoozes = alert.get("max_snoozes", self.Alert.max_snoozes)

            self.Alert.alert_msg = alert.get("alert_msg", self.Alert.alert_msg)
            self.Alert.alert_msg_snooze = alert.get("alert_msg_snooze", self.Alert.alert_msg_snooze)
            self.Alert.alert_msg_ack = alert.get("alert_msg_ack", self.Alert.alert_msg_ack)
            self.Alert.alert_msg_max_snoozes = alert.get("alert_msg_max_snoozes", self.Alert.alert_msg_max_snoozes)
            self.Alert.wait_for_prev_ack = alert.get("wait_for_prev_ack", self.Alert.wait_for_prev_ack)

    def save_to_fs(self):
        contents = json.dumps(self.as_json(), indent = 4)
        
        # Safely save to file system.
        safe_write(self.path, contents)

    def print(self):
        print("Settings")
        
        print("\tDebug")
        debug = self.Debug
        
        print(f"\t\tVerbose => {debug.verbose}")
        print(f"\t\tLog To File => {debug.log_to_file}")
        print(f"\t\tLog Directory => {debug.log_dir}")
        
        # General settings
        print(f"\tGeneral")
        
        print(f"\t\tSave Config Locally => {self.General.save_locally}")
        
        # Bot settings
        print(f"\tDiscord Bot")
        print(f"\t\tToken => {self.Bot.token}")
        print(f"\t\tChannel ID => {self.Bot.channel_id}")
        print(f"\t\tUser ID => {self.Bot.user_id}")
        print(f"\t\tFirst Emoji => {self.Bot.first_emoji}")

        # Alert settings
        print(f"\tAlerts")
        alert = self.Alert

        print(f"\t\tTimezone => {alert.timezone}")
        print(f"\t\tSnooze Time => {alert.snooze_time}")
        print(f"\t\tTimes => {alert.times}")
        print(f"\t\tMax Snoozes => {alert.max_snoozes}")

        print(f"\t\tAlert Message => {alert.alert_msg}")
        print(f"\t\tAlert Message Snooze => {alert.alert_msg_snooze}")
        print(f"\t\tAlert Message Acknowledged => {alert.alert_msg_ack}")
        print(f"\t\tAlert Message Max Snoozes => {alert.alert_msg_max_snoozes}")
        print(f"\t\tWait For Previous Acknowledgement => {alert.wait_for_prev_ack}")