# digestbot
[![Build Status](https://travis-ci.com/artyomche9/digestbot.svg?branch=develop)](https://travis-ci.com/artyomche9/digestbot)

Bot for slack, who send you top messages whenever you want!

### What bot can do:
* find and send you top messages from given channel, pre-defined sets of channels or all channels
* select messages for last N hours / days / weeks
* sort messages by 3 different sorting types
* create timers for you to receive digest on schedule
* create your own presets to combine channels in one group


### Can I use this bot for my own space?
Sure! To deploy your bot you have to:
* Create slack app in your workspace and get USER_SLACK_TOKEN and BOT_SLACK_TOKEN
* Prepare needed environment variables in .env file (see env.template)
* Deploy this bot using prepared docker-compose file with bot and database or pull bot from dockerhub:
_maybehelloworld/digestbot:latest_
    * Do not forget to pass environment variables to bot from .env file or in any other way
* Done!


### How can I help?

If you have any good idea or noticed a bug - create new issue and we will talk about it!
Before submitting issue, please check ROADMAP.md - possibly we are already working on that. :)

Doesn't know what to do? Check issues and implement solution for one.

Anyway, Pull Requests are welcome!
