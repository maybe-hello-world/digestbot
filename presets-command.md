#User based presets

##Main Syntax

* ```presets add <name> channel1 [channel2] ... [channelN]``` - Добавать пресет с заданными каналами
* ```presets rm <name>``` - Удалить пресет
* ```presets ls [global]``` - Список доступных пресетов. С флагом `global` выводятся пресеты заданные разработчикам

##Optional Syntax
* ```presets <name> add channel1 [channel2] ... [channelN]``` -- Добавить каналы в пресет
* ```presets <name> rm channel1 [channel2] ... [channelN]``` -- Удалить каналы из пресета

Обработка не существующего канала