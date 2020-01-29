## @digestbot v2.0.2 - 2020-01-29
Hotfix for channel parsing

### Changes:
- **Channels:** fixed parsing channel ID that caused possibility of adding erroneous IDs to the database from user input
([#46](https://github.com/artyomche9/digestbot/pull/46))


## @digestbot v2.0.1 - 2020-01-16
Internal hotfix for timer functionality

### Changes:
- **Timers:** fixed incorrect sleep timing during timers processing
 ([#45](https://github.com/artyomche9/digestbot/pull/45))

## @digestbot v2.0.0 - 2020-01-12

Timers and user-defined presets added. Now you can create your own presets combining channels together and
schedule timers to send you top messages whenever you want.

### Changes:
- **User-defined presets:** added possibility for users to create their own presets
 ([#40](https://github.com/artyomche9/digestbot/pull/40), thx [@Sergey778](https://github.com/Sergey778))
- **User-defined timers:** added possibility to schedule timers (every 1hour..(+inf)weeks) to receive top messages
 ([#41](https://github.com/artyomche9/digestbot/pull/41))

**How to try:** ask bot for "help timers" and "help presets".

## @digestbot v1.0.0 - 2019-10-31

Initial release of **@digestbot**. Basic functionality added:
- get top messages from all channels, any channel or predefined sets of channels
- filter of top messages by time ("later then ...")
- sort top messages by number of answers, emoji rating or amount of text

**Help** is availabel in repo's [wiki](https://github.com/artyomche9/digestbot/wiki)
 or from bot itself: just print "help" command.

Thanks to awesome bot team:
 - [toshiks](https://github.com/toshiks)
 - [Sergey778](https://github.com/Sergey778)
 - [artyomche9](https://github.com/artyomche9)
 - [varan42](https://github.com/varan42)
