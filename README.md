# digestbot
[![Build Status](https://travis-ci.com/maybe-hello-world/digestbot.svg?branch=develop)](https://travis-ci.com/maybe-hello-world/digestbot)

Bot for Slack, who send you top messages whenever you want!

![Message Example](https://i.imgur.com/tWsw83p.png)

### What bot can do:
* find and send you top messages from a given channel, pre-defined sets of channels or all channels
* select messages for last N hours / days / weeks
* sort messages by 3 different sorting types
* create timers for you to receive digest on schedule
* create your own presets to combine channels in one group


### Can I use this bot for my own space?
Sure! To deploy your bot you have to:
* Create a slack app in your workspace and get USER_SLACK_TOKEN and BOT_SLACK_TOKEN
* Prepare needed environment variables in .env file (see env.template)
* Deploy this bot using the docker-compose.yml file with bot and database or pull bot from dockerhub:
_maybehelloworld/digestbot:latest_
    * Do not forget to pass environment variables to bot from .env file or in any other way
* Done!


### How can I help?

If you have any good ideas or noticed a bug - create a new issue and we will talk about it!
Before submitting the issue, please check ROADMAP.md - possibly we are already working on that. :)

Doesn't know what to do? Check issues and implement a solution for one.

Anyway, Pull Requests are welcome!
