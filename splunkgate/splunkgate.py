#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import uuid
import shutil

sys.path.append("sglib")
from sgconfig import Configuration
from sglogger import SplunkLogger
from sgdb import DBLayer
from sgalerts import AlertHandler
from sgesb import ESBHandler


if __name__ == "__main__":
  """Инициация SplunkGate"""

  # Инициировать систему конфигурации
  config = Configuration(sys.argv[1])
  opts = dict(
    logger = config.get_logger('logger', __name__),
    esb = dict(
      host = config.get_option_str('esb','host'),
      url = config.get_option_str('esb','url'),
      login = config.get_option_str('esb','login'),
      password = config.get_option_str('esb','password'),
      serviceId = config.get_option_str('esb','serviceId'),
      routeId = config.get_option_str('esb','routeId')
    ),
    splunkgate = dict(
      database = config.get_option_str('splunkgate','database')
    ),
    splunk = dict(
      log = config.get_option_str('splunk','log'),
      debug = config.get_option_bool('splunk','debug'),
      snapshotPath = config.get_option_str('splunk','snapshotPath'),
      readOnlyFirstElement = config.get_option_bool('splunk','readOnlyFirstElement'),
      createSnapshot = config.get_option_bool('splunk','createSnapshot'),
      servers = config.get_server_list('splunk.servers')
    )
  )
  print opts

  logger = opts['logger']
  logger.info('Start SplunkGate')

  # Инициировать базу данных
  db = DBLayer(logger, opts['splunkgate'])

  # Инициировать подключение к ESB
  esb = ESBHandler(logger, opts['esb'])

  # Инициировать систему получения сообщений от Splunk
  splunkAlerts = AlertHandler(logger, opts['splunk'])

  # Получить сообщения из Splunk
  alerts = splunkAlerts.getAlert()

  # Начать обработку сообщений из Splunk
  for alert in alerts:
    try:
      ticket = splunkAlerts.parseAlert(alert)
      ticket['messageId'] = str(uuid.uuid1())

    except Exception, e:
      logger.error(e)

    #print config['splunk.servers'].get(ticket.get('computerName'))
    ticket['serviceId'] = opts['esb']['serviceId']
    ticket['routeId'] = opts['esb']['routeId']
    ticket['login'] = opts['esb']['login']
    ticket['password'] = opts['esb']['password']

    ticket1 = None
    ticket1 = db.getTicket(ticket)
    print ticket1
    if ticket1:
      print 'Find ticket:', ticket

    else:
      print 'Not find ticket:', ticket
      db.setTicket(ticket)
      esb.createTicket(ticket)

      #message = gate.createSOAPMessage(id, 'SMAC', alert[3], comment, 'P002')
      #response = gate.sendSOAPMessage(message)
      #logger.info(''.join(['Get response: ', str(response)]))
    #  db.updateTicket(status, eventCode, eventType, computerName)

  logger.info('Stop SplunkGate')

