import cmd
import random
import sys
import logging
import requests
import threading
import readline
import traceback

from will import settings
from will.utils import Bunch, UNSURE_REPLIES
from will.abstractions import Message, Person, Channel
from .base import StdInOutIOBackend


class ShellBackend(StdInOutIOBackend):
    friendly_name = "Interactive Shell"
    internal_name = "will.backends.io_adapters.shell"
    partner = Person(
        id="you",
        handle="you",
        source=Bunch(),
        name="Friend",
    )

    def send_direct_message(self, message_body, **kwargs):
        print("Will: %s" % message_body)

    def send_room_message(self, room_id, message_body, html=False, color="green", notify=False, **kwargs):
        print("Will: %s" % message_body)

    def set_room_topic(self, room_id, topic):
        print("Will: Setting the Topic to %s" & topic)

    def normalize_incoming_event(self, event):
        if event["type"] == "message.incoming.stdin":
            m = Message(
                content=event.data.content.strip(),
                type=event.type,
                is_direct=True,
                is_private_chat=True,
                is_group_chat=False,
                backend=self.name,
                sender=self.partner,
                will_is_mentioned=False,
                will_said_it=False,
                backend_supports_acl=False,
                source=event
            )
            return m
        else:
            # An event type the shell has no idea how to handle.
            return None

    def handle_outgoing_event(self, event):
        # Print any replies.
        # print "handle_outgoing_event"
        # print event
        if event.type in ["say", "reply"]:
            self.send_direct_message(event.content)

        elif event.type == "message.no_response":
            # TODO: Seriously fix this. It's gross and confusing.
            # print event.data["source"].data.content
            if event.data and "source" in event.data and len(event.data["source"].data.content) > 0:
                self.send_direct_message(random.choice(UNSURE_REPLIES))

        # Regardless of whether or not we had something to say,
        # give the user a new prompt.
        sys.stdout.write("You:  ")
        sys.stdout.flush()

    def bootstrap(self):
        # Bootstrap must provide a way to to have:
        # a) self.normalize_incoming_event fired, or incoming events put into self.incoming_queue
        # b) any necessary threads running for a)
        # c) self.me (Person) defined, with Will's info
        # d) self.people (dict of People) defined, with everyone in an organization/backend
        # e) self.channels (dict of Channels) defined, with all available channels/rooms.
        #    Note that Channel asks for members, a list of People.
        # f) A way for self.handle, self.me, self.people, and self.channels to be kept accurate,
        #    with a maximum lag of 60 seconds.
        self.people = {}
        self.channels = {}
        self.me = Person(
            id="will",
            handle="will",
            source=Bunch(),
            name="William T. Botterton",
        )

        # Do this to get the first "you" prompt.
        self.pubsub.publish('message.input.stdin', (Message(
                content="",
                type="chat",
                is_direct=True,
                is_private_chat=True,
                is_group_chat=False,
                backend=self.internal_name,
                sender=self.partner,
                will_is_mentioned=False,
                will_said_it=False,
                backend_supports_acl=False,
                source={}
            ))
        )
