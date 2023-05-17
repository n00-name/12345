# Simple.IDE v0.1
## Simple.IDE - это одна из самых передовых IDE мира, созданная учениками Московской Школы Программистов группы S101_01.

## Подготовка к разработке

1. Запустить файл `./copy-hooks.sh`



### Docker-образ

Используется для ускорения процесса CI

В него вынесена процедура предварительной установки всего необходимого софта для проекта

#### Сборка образа
```bash
docker build -t srx64/shp_ide_ci_environment:0.1 -f ./ci/Dockerfile .  
```
* Версия - может отличаться
* Запускать надо в случае, если изменился набор пакетов, необходимых для разработки

#### Загрузка образа на docker hub
```bash
docker push srx64/shp_ide_ci_environment:0.1 -f ./ci/Dockerfile .  
```

1. Версия - может отличаться
2. Для успешной загрузки требуется доступ к аккаунту srx64 (можно запросить у преподавателя)
3. Если доступа нет - нужно поменять аккаунт в 
   1. команде сборки
   2. команде запуска
   3. а также в `.gitlab-ci.yml`, для которого всё это и затевалось
