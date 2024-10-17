import discord
import asyncio
import json
import random
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, time

class AliciaPresenceManager:
    def __init__(self, client: discord.Client, verbose: bool = False):
        self.client = client
        self.config_file = 'alicia_presence_config.json'
        self.verbose = verbose
        self.setup_logging()
        self.config = self.load_config()
        self.current_status_index = 0
        self.current_activity_index = 0

    def setup_logging(self) -> None:
        self.logger = logging.getLogger('AliciaPresenceManager')
        self.logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.validate_config(config)
            return config
        except FileNotFoundError:
            self.logger.warning(f"Config file not found. Creating default config.")
            return self.create_default_config()
        except json.JSONDecodeError:
            self.logger.warning(f"Invalid JSON in config file. Creating default config.")
            return self.create_default_config()

    def validate_config(self, config: Dict[str, Any]) -> None:
        for status_type in ['rotating', 'timed', 'fixed']:
            statuses = config['statuses'].get(status_type, [])
            if isinstance(statuses, list):
                for status in statuses:
                    self.validate_status_text(status.get('text', ''))
            elif isinstance(statuses, dict):
                self.validate_status_text(statuses.get('text', ''))

        for activity in config['rich_presence']['activities']:
            self.validate_activity_name(activity.get('name', ''))

        for activity in config['rich_presence'].get('timed_activities', []):
            self.validate_activity_name(activity.get('name', ''))

    def validate_status_text(self, text: str) -> None:
        if len(text) > 128:
            self.logger.warning(f"Status text exceeds 128 characters: '{text[:50]}...'")

    def validate_activity_name(self, name: str) -> None:
        if len(name) > 128:
            self.logger.warning(f"Activity name exceeds 128 characters: '{name[:50]}...'")

    def save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        if config is None:
            config = self.config
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self.logger.info("Config saved successfully.")
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    def create_default_config(self) -> Dict[str, Any]:
        default_config = {
            "features": {
                "rotating_status": True,
                "rich_presence": True,
                "random_status": True,
                "timed_status": True
            },
            "status_rotation_interval": 600,
            "statuses": {
                "rotating": [
                    {"text": "Spreading love and happiness", "emoji": "💖"},
                    {"text": "Crafting digital hugs", "emoji": "🤗"},
                    {"text": "Nurturing dreams", "emoji": "✨"},
                    {"text": "Whispering encouragement", "emoji": "🌟"},
                    {"text": "Baking virtual cookies", "emoji": "🍪"}
                ],
                "timed": [
                    {"text": "Rise and shine, darling!", "emoji": "🌅", "start_time": "06:00", "end_time": "10:00"},
                    {"text": "Time for a midday hug?", "emoji": "🤗", "start_time": "10:00", "end_time": "14:00"},
                    {"text": "Afternoon tea and chats", "emoji": "☕", "start_time": "14:00", "end_time": "18:00"},
                    {"text": "Cozy evening cuddles", "emoji": "🌙", "start_time": "18:00", "end_time": "22:00"},
                    {"text": "Sweet dreams", "emoji": "😴", "start_time": "22:00", "end_time": "06:00"}
                ],
                "fixed": {"text": "Here for you, always", "emoji": "💕"}
            },
            "rich_presence": {
                "activities": [
                    {
                        "type": "playing",
                        "name": "guardian angel",
                        "details": "Watching over you",
                        "state": "You're safe with me"
                    },
                    {
                        "type": "listening",
                        "name": "to your heart",
                        "details": "Every beat tells a story",
                        "state": "What's on your mind?"
                    },
                    {
                        "type": "watching",
                        "name": "your dreams unfold",
                        "details": "Cheering you on",
                        "state": "You can do it!"
                    }
                ],
                "timed_activities": [
                    {
                        "type": "playing",
                        "name": "sunrise yoga",
                        "details": "Stretching our wings",
                        "state": "Good morning, sunshine!",
                        "start_time": "06:00",
                        "end_time": "10:00"
                    },
                    {
                        "type": "playing",
                        "name": "lunchtime stories",
                        "details": "Sharing giggles and tales",
                        "state": "Once upon a time...",
                        "start_time": "10:00",
                        "end_time": "14:00"
                    },
                    {
                        "type": "playing",
                        "name": "evening lullabies",
                        "details": "Singing you to sleep",
                        "state": "Sweet dreams await",
                        "start_time": "18:00",
                        "end_time": "22:00"
                    },
                    {
                        "type": "watching",
                        "name": "over your sleep",
                        "details": "Guarding your dreams",
                        "state": "Rest easy, I'm here",
                        "start_time": "22:00",
                        "end_time": "06:00"
                    }
                ]
            },
            "presence_update_interval": 3600
        }
        self.save_config(default_config)
        return default_config

    def update_config(self, new_config: Dict[str, Any]) -> None:
        self.config.update(new_config)
        self.validate_config(self.config)
        self.save_config()

    def toggle_feature(self, feature: str) -> None:
        if feature in self.config["features"]:
            self.config["features"][feature] = not self.config["features"][feature]
            self.save_config()
            self.logger.info(f"Feature '{feature}' toggled to {self.config['features'][feature]}")

    def manage_status(self, action: str, status_type: str, status: Optional[Dict[str, str]] = None, index: Optional[int] = None) -> None:
        if status_type not in self.config["statuses"]:
            self.logger.warning(f"Invalid status type: {status_type}")
            return

        if action == "add" and status:
            self.validate_status_text(status.get('text', ''))
            if isinstance(self.config["statuses"][status_type], list):
                self.config["statuses"][status_type].append(status)
            else:
                self.config["statuses"][status_type] = status
            self.logger.info(f"Added new status to {status_type}")
        elif action == "remove" and index is not None:
            if isinstance(self.config["statuses"][status_type], list):
                if 0 <= index < len(self.config["statuses"][status_type]):
                    del self.config["statuses"][status_type][index]
                    self.logger.info(f"Removed status at index {index} from {status_type}")
                else:
                    self.logger.warning(f"Invalid index {index} for {status_type}")
            else:
                self.logger.warning(f"Cannot remove index from non-list status type: {status_type}")

        self.save_config()

    def manage_activity(self, action: str, activity: Optional[Dict[str, Any]] = None, index: Optional[int] = None) -> None:
        if action == "add" and activity:
            self.validate_activity_name(activity.get('name', ''))
            self.config["rich_presence"]["activities"].append(activity)
            self.logger.info("Added new activity")
        elif action == "remove" and index is not None:
            if 0 <= index < len(self.config["rich_presence"]["activities"]):
                del self.config["rich_presence"]["activities"][index]
                self.logger.info(f"Removed activity at index {index}")
            else:
                self.logger.warning(f"Invalid activity index: {index}")

        self.save_config()

    def set_interval(self, interval_type: str, interval: int) -> None:
        if interval_type in ["status_rotation_interval", "presence_update_interval"]:
            self.config[interval_type] = interval
            self.save_config()
            self.logger.info(f"Set {interval_type} to {interval}")
        else:
            self.logger.warning(f"Invalid interval type: {interval_type}")

    def is_time_between(self, start: time, end: time) -> bool:
        now = datetime.now().time()
        if start < end:
            return start <= now < end
        else:  # Over midnight
            return now >= start or now < end

    def select_status(self, statuses: List[Dict[str, str]]) -> Dict[str, str]:
        if self.config["features"]["timed_status"]:
            timed_statuses = self.config["statuses"].get("timed", [])
            for status in timed_statuses:
                start = datetime.strptime(status["start_time"], "%H:%M").time()
                end = datetime.strptime(status["end_time"], "%H:%M").time()
                if self.is_time_between(start, end):
                    self.logger.debug(f"Selected timed status: {status['text']}")
                    return status

        if self.config["features"]["random_status"]:
            status = random.choice(statuses)
            self.logger.debug(f"Selected random status: {status['text']}")
            return status
        
        status = statuses[self.current_status_index]
        self.current_status_index = (self.current_status_index + 1) % len(statuses)
        self.logger.debug(f"Selected rotating status: {status['text']}")

        return status

    def select_activity(self, activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        timed_activities = self.config["rich_presence"].get("timed_activities", [])
        for activity in timed_activities:
            start = datetime.strptime(activity["start_time"], "%H:%M").time()
            end = datetime.strptime(activity["end_time"], "%H:%M").time()
            if self.is_time_between(start, end):
                self.logger.debug(f"Selected timed activity: {activity['name']}")
                return activity

        activity = activities[self.current_activity_index]
        self.current_activity_index = (self.current_activity_index + 1) % len(activities)
        self.logger.debug(f"Selected rotating activity: {activity['name']}")

        return activity

    async def update_presence(self) -> None:
        while True:
            try:
                if not self.client.is_ready():
                    self.logger.warning("Discord client is not ready. Waiting before updating presence.")
                    await asyncio.sleep(60)
                    continue

                if self.config["features"]["rotating_status"]:
                    await self.update_status()
                if self.config["features"]["rich_presence"]:
                    await self.update_rich_presence()
                await asyncio.sleep(self.config["presence_update_interval"])
            except Exception as e:
                self.logger.error(f"Error updating presence: {e}")
                await asyncio.sleep(60)

    async def update_status(self) -> None:
        if not self.client.is_ready():
            self.logger.warning("Client not ready. Skipping status update.")
            return

        if self.config["features"]["timed_status"]:
            statuses = self.config["statuses"].get("timed", [])
        else:
            statuses = self.config["statuses"]["rotating"]

        if not statuses:
            self.logger.warning("No statuses available to update")
            return

        status = self.select_status(statuses)
        activity = discord.Game(name=status["text"])
        
        try:
            await self.client.change_presence(
                status=discord.Status.online,
                activity=activity
            )
            self.logger.info(f"Updated status: {status['text']}")
        except Exception as e:
            self.logger.error(f"Failed to update status: {e}")

    async def update_rich_presence(self) -> None:
        if not self.client.is_ready():
            self.logger.warning("Client not ready. Skipping rich presence update.")
            return

        activities = self.config["rich_presence"]["activities"]
        if not activities:
            self.logger.warning("No activities available to update")
            return

        activity_config = self.select_activity(activities)
        activity = self.create_activity(activity_config)
        
        try:
            await self.client.change_presence(activity=activity)
            self.logger.info(f"Updated rich presence: {activity_config['name']}")
        except Exception as e:
            self.logger.error(f"Failed to update rich presence: {e}")

    def create_activity(self, activity_config: Dict[str, Any]) -> discord.Activity:
        activity_type = getattr(discord.ActivityType, activity_config["type"])
        activity = discord.Activity(
            type=activity_type,
            name=activity_config["name"],
            details=activity_config.get("details"),
            state=activity_config.get("state")
        )

        if "large_image" in activity_config:
            activity.large_image = activity_config["large_image"]
            activity.large_text = activity_config.get("large_text", "")

        if "small_image" in activity_config:
            activity.small_image = activity_config["small_image"]
            activity.small_text = activity_config.get("small_text", "")

        buttons = activity_config.get("buttons", [])
        if buttons:
            activity.buttons = [discord.Button(label=btn["label"], url=btn["url"]) for btn in buttons[:2]]

        return activity

    def start(self) -> None:
        self.logger.info("Starting AliciaPresenceManager")
        self.client.loop.create_task(self.update_presence())