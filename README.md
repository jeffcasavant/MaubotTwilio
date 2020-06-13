# MaubotTwilio

Maubot plugin to bridge in SMS with Twilio.

## Dependencies

Your Maubot instance needs to have access to the following Pip packages:

* twilio

## Usage

* Create a Twilio account and a phone number.  Create a project so you track
  costs.
* Load the plugin into your Maubot instance
* Create an instance - remember its name
* Set the values in the config file
* In Twilio -> Super Network -> Phone Numbers -> the source number you intend
  to use, under Messaging, set the `A MESSAGE COMES IN` webhook URL to
  `https://<maubot instance hostname>/<plugin base from maubot config, default
  _matrix/maubot/plugin>/<plugin instance name>/sms`
* `!addsms alias +12223334444` will begin sending room messages via SMS to
  +1-222-333-4444 and routing messages from it to the room in which you ran
  this command.  Use a number format that Twilio supports directly - the plugin
  does no format conversion.
* `!removesms alias` or `!removesms +12223334444` will stop bridging to that
  number.
* `!listsms` prints a table of the currently bridged numbers and aliases.

## Motivation

The plugin's design & limitations come from its primary use case: I am in a
room with one member who was going to be without her smartphone for a few
months.  I built this as a quick & dirty solution to keep her involved in our
group chat.

## Features

* Admin list - only allow certain users to add / remove bridging (to control
  costs).

## Limitations

* Numbers can only send messages to one room.  This could be corrected in the
  future by supporting multiple Twilio numbers, and looking up `(Twilio number,
  message source number)` to `room_id` instead of just `message source number`.
* MMS is not currently supported though Twilio does have that feature.
* Voice (via text-to-speech and speech-to-text) is not supported either.  Might
  be useful for an alarms room, or for any style of message you'll want to
  reach you during e.g. a work meeting.
* Other telephony providers are not supported (for example Nexmo should be a
  tiny bit cheaper).

## Drawbacks

* Cost: at Twilio rates as of 2020-06-13, you'll pay $.0075 for each ingoing
  and outgoing SMS, and $1/mo to retain the number you're using.
* Logging: Twilio has copies of all messages in its SMS log (handy for
  troubleshooting delivery).  Don't treat SMS as a secure messaging service.

## Esoterica

* The package name for this plugin diverges from my other plugin
  (`casavant.jeff...` vs `org.casavant.jeff...`).  This new format is correct.
  Not sure if it will break current installations of my old plugin if I update
  it.

## Issues

Hit me up in #maubot-casavant-plugins:casavant.org if you have any trouble.
