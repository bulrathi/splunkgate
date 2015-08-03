#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__  = "bw"
__version__ = "0.1.0"

import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from time import gmtime, strftime

import uuid

sys.path.append("sglib")
from sg_config import configuration
from sg_db import db_layer
from sg_alerts import alert_handler
from sg_esb import esb_handler


class _AlertType:
  """
  Типы алертов
  """

  WIN  = 1
  UNIX = 2


def _get_config(fname):
  """
  Получить конфигурацию гейта
  """

  config = configuration(fname)
  opts = dict(
    logger = config.get_logger('logger', __name__),
    log_ticket_status = config.get_option_str('logger_ticket_status', 'logname'),
    esb = dict(
      host = config.get_option_str('esb','host'),
      url = config.get_option_str('esb','url'),
      login = config.get_option_str('esb','login'),
      password = config.get_option_str('esb','password'),
      serviceId = config.get_option_str('esb','serviceId'),
      routeId = config.get_option_str('esb','routeId'),
      systemCode = config.get_option_str('esb','systemCode'),
      priority = config.get_option_str('esb','priority'),
      timeout = config.get_option_int('esb','timeout')
    ),
    splunkgate = dict(
      database = config.get_option_str('splunkgate','database'),
      pid = config.get_option_str('splunkgate','pid')
    ),
    splunk = dict(
      logWin = config.get_option_str('splunk','logWin'),
      logUnix = config.get_option_str('splunk','logUnix'),
      debug = config.get_option_bool('splunk','debug'),
      snapshotPath = config.get_option_str('splunk','snapshotPath'),
      readOnlyFirstElement = config.get_option_bool('splunk','readOnlyFirstElement'),
      createSnapshot = config.get_option_bool('splunk','createSnapshot'),
      servers = config.get_server_list('splunk.servers')
    ),
    jira = dict(
      openStatus = config.get_list('jira', 'open_status'),
      closeStatus = config.get_list('jira', 'close_status'),
    )
  )

  return opts


def _create_ticket(esb, db, ticket):
  """
  Создание тикета в JIRA
  """

  # попробовать создать тикет в JIRA
  resp = esb.create_ticket(ticket)

  if 'message' in resp:
    # вернулось сообщение, которое не удалось распарсить
    logger.error('Get unparsible message: %s', resp)

  else:
    # тикет создан в JIRA
    ticket['jiraId'] = resp['id']
    ticket['jiraKey'] = resp['key']
    ticket['jiraStatusId'] = None
    # обновить тикет в БД гейта
    db.update_ticket(ticket)


def _parse_alert(config, logger, splunk_alerts, esb, db, alert, alert_type):
  """
  Обработка алертов
  """
  try:
    if alert_type == _AlertType.WIN:
      # алерт от Windows-серверов
      ticket = splunk_alerts.parse_win_alert(alert)
    else:
      # алерт от UNIX-серверов
      ticket = splunk_alerts.parse_unix_alert(alert)

    ticket['messageId'] = str(uuid.uuid1())

    # найти тикет в БД гейта
    ticket1 = None
    ticket1 = db.get_ticket(ticket)

    if ticket1:
      # тикет найден в БД гейта

      ticket['jiraId'] = ticket1['jiraId']
      ticket['jiraKey'] = ticket1['jiraKey']

      if ticket['computerName'] in config['splunk']['servers']:
        ticket['systemCode'] = config.get('splunk').get('servers').get(ticket['computerName'])
      else:
        raise Exception('%s not found in servers list' % ticket['computerName'])

      if ticket['jiraId']:
        # в БД гейта у тикета уже есть ID тикета в JIRA
        logger.info('Find ticket: %s, check state in JIRA', ticket)
        # получить статус тикета в JIRA
        resp = esb.get_ticket_status(ticket)
        # получаем ID тикета в JIRA
        ticket['jiraStatusId'] = resp['fields']['status']['id']
        if ticket['jiraStatusId'] in config.get('jira').get('closeStatus'):
          # если тикет закрыт в JIRA, то создаем новые
          _create_ticket(esb, db, ticket)

        # обновисть статус тикета в БД гейта
        db.update_ticket(ticket)

      else:
        # тикет есть в БД гейта, но не имеет ID JIRA, возможно, он не был создан в JIRA
        logger.info('Find ticket: %s, but not create in JIRA, try for create ticket in JIRA', ticket)
        # пробуем создать тикет в JIRA
        _create_ticket(esb, db, ticket)

    else:
      # тикет не найден в БД гейта
      logger.info('No find ticket: %s, create ticket in JIRA', ticket)
      # создать тикет в БД гейта
      db.set_ticket(ticket)
      # попробовать создать тикет в JIRA
      _create_ticket(esb, db, ticket)

  except Exception, e:
    logger.error(e)


if __name__ == "__main__":
  is_clear_pid = True
  pidfile = None
  logger = None

  try:
    opts = _get_config(sys.argv[1])

    logger = opts['logger']
    logger.info('Start SplunkGate')

    log_ticket_status = opts['log_ticket_status']

    # проверка, что не запущен еще один экземпляр гейта
    pid = str(os.getpid())
    pidfile = opts['splunkgate']['pid']

    if os.path.isfile(pidfile):
      # если найден PID-файл, завершить работу
      logger.warning("%s already exists, exiting", pidfile)
      is_clear_pid = False
      sys.exit()
    else:
      # PID-файл не найден, создать и продолжить
      file(pidfile, 'w').write(pid)

    # Инициировать базу данных
    db = db_layer(logger, opts['splunkgate'])

    # Инициировать подключение к ESB
    esb = esb_handler(logger, opts['esb'])

    # Инициировать систему получения сообщений от Splunk
    splunk_alerts = alert_handler(logger, opts['splunk'])

    ticket_status = db.get_ticket_status()
    if len(ticket_status) > 0:
      t = strftime("%Y-%m-%d %H:%M:%S", gmtime())
      f = open(log_ticket_status, 'a')
      for status in ticket_status:
        s = t + ';' + ''.join(['%s;' % (str(value)) for (key, value) in status.items()])
        s = s[:-1]
        f.write(s + '\n')
      f.close()

    # Получить сообщения из Splunk
    alerts = splunk_alerts.get_alert()

    # Начать обработку сообщений из Splunk
    # обработка алерты от Windows-серверов
    for alert in alerts['win']:
      _parse_alert(opts, logger, splunk_alerts, esb, db, alert, _AlertType.WIN)

    # обработка алерты от UNIX-серверов
    for alert in alerts['unix']:
      _parse_alert(opts, logger, splunk_alerts, esb, db, alert, _AlertType.UNIX)

    logger.info('Stop SplunkGate')

  except Exception, e:
    if logger:
      logger.error(sys.exc_info())
    else:
      print sys.exc_info()
      print str(e)

  finally:
    if is_clear_pid:
      if pidfile:
        if os.path.isfile(pidfile):
          os.unlink(pidfile)

