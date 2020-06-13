#! /usr/bin/env python3

from typing import Type

from aiohttp import web

from maubot import Plugin, MessageEvent
from maubot.handlers import command, event, web as web_handler
from mautrix.types import EventType, TextMessageEventContent, MessageType, Format
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from .db import Database

PREFIX = "<sms>"


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("twilio_account_sid")
        helper.copy("twilio_auth_token")
        helper.copy("twilio_source_number")
        helper.copy("admins")


class WebhookReceiver:
    def __init__(self, db, log, client):
        self.db = db
        self.log = log
        self.client = client

    @web_handler.post("/sms")
    async def handle_sms(self, request: web.Request) -> web.Response:
        params = await request.post()

        number = params["From"]
        body = params["Body"]

        self.log.debug("Received sms from %s: %s", number, body)

        row = self.db.get(number=number)

        if not row:
            self.log.info("No room mapping for %s", number)
        else:
            row = row[0]
            content = TextMessageEventContent(msgtype=MessageType.TEXT, body=f"{PREFIX} {row.name}: {body}")
            await self.client.send_message(row.room, content)

        return web.Response(status=200)


class TwilioPlugin(Plugin):
    db: Database

    async def start(self) -> None:
        await super().start()
        self.config.load_and_update()
        self.db = Database(self.log, self.database)

        self.log.debug("Logging in to twilio")
        self.twilio_client = Client(self.config["twilio_account_sid"], self.config["twilio_auth_token"])

        self.webhook_receiver = WebhookReceiver(self.db, self.log, self.client)
        self.register_handler_class(self.webhook_receiver)

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config

    @event.on(EventType.ROOM_MESSAGE)
    async def handler(self, evt: MessageEvent) -> None:
        content = evt.content
        if not content.msgtype.is_text or content.body.startswith("!") or content.body.startswith(PREFIX):
            return

        self.log.debug("Twilio bot handling message in %s: %s", evt.room_id, content.body)

        numbers = self.db.get(room=evt.room_id)
        self.log.debug("DB resp %s", numbers)

        self.log.info("Forwarding message to %d numbers", len(numbers))
        for number in numbers:
            self.log.debug("Sending message to %s (%s)", number.name, number.number)
            try:
                self.twilio_client.messages.create(
                    to=number.number, from_=self.config["twilio_source_number"], body=f"{evt.sender}: {content.body}"
                )
            except TwilioRestException as exc:
                self.log.exception("Failed to send to %s (%s)", number.name, number.number)

        await evt.mark_read()

    @command.new("removesms", help="Remove an SMS correspondent from this room")
    @command.argument("identifier", required=True)
    async def removesms_handler(self, evt: MessageEvent, identifier: str) -> None:
        if evt.sender not in self.config.get("admins", []):
            content = TextMessageEventContent(
                msgtype=MessageType.TEXT, body="You are not authorized to configure this plugin"
            )
            await self.client.send_message(evt.room_id, content)
            return

        self.log.info("Removing SMS correspondent %s for room %s", identifier, evt.room_id)
        await evt.mark_read()
        self.db.unmap(identifier=identifier)
        content = TextMessageEventContent(msgtype=MessageType.TEXT, body=f"Removed {identifier}")
        await self.client.send_message(evt.room_id, content)

    @command.new("addsms", help="Add an SMS correspondent to this room")
    @command.argument("alias", required=True)
    @command.argument("number", required=True)
    async def addsms_handler(self, evt: MessageEvent, alias: str, number: str) -> None:
        if evt.sender not in self.config.get("admins", []):
            content = TextMessageEventContent(
                msgtype=MessageType.TEXT, body="You are not authorized to configure this plugin"
            )
            await self.client.send_message(evt.room_id, content)
            return

        self.log.info("Registering new SMS correspondent %s (%s) for room %s", alias, number, evt.room_id)
        self.db.map(name=alias, number=number, room=evt.room_id)
        await evt.mark_read()
        content = TextMessageEventContent(msgtype=MessageType.TEXT, body=f"Added {alias} ({number})")
        await self.client.send_message(evt.room_id, content)

    @command.new("listsms", help="List all SMS correspondents in this room")
    async def listsms_handler(self, evt: MessageEvent) -> None:
        self.log.info("Listing SMS correspondents for room %s", evt.room_id)
        await evt.mark_read()

        members = [{"name": row.name, "number": row.number} for row in self.db.list(room=evt.room_id)]

        plain_members = "\n".join([f"{member['name']}: {member['number']}" for member in members])
        html_members = "\n".join(
            [f"<tr><td>{member['name']}</td><td>{member['number']}</td></tr>" for member in members]
        )
        header = "Current SMS participants:"
        formatted_body = f"{header}\n<table>\n{html_members}\n</table>"
        content = TextMessageEventContent(
            msgtype=MessageType.TEXT,
            format=Format.HTML,
            body=f"{header}\n{plain_members}",
            formatted_body=formatted_body,
        )
        await self.client.send_message(evt.room_id, content)
