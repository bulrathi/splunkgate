#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import uuid
import shutil

sys.path.append("sglib") 
from sgconfig import SplunkConfig
from sglogger import SplunkLogger
from sgdb import DBLayer
from sgalerts import AlertHandler
from sgesb import ESBHandler


if __name__ == "__main__":
  """Инициация SplunkGate"""

  # Инициировать систему конфигурации
  splunkConfig = SplunkConfig(sys.argv[1])
  config = splunkConfig.getConfigParams()

  # Инициировать систему логирования
  splunkLogger = SplunkLogger(config)
  logger = splunkLogger.getLogger()

  logger.info('Start SplunkGate')

  # Инициировать базу данных
  db = DBLayer(logger, config)

  # Инициировать подключение к ESB
  esb = ESBHandler(logger, config)

  # Инициировать систему получения сообщений от Splunk
  splunkAlerts = AlertHandler(logger, config)
  
  # Получить сообщения из Splunk
  alerts = splunkAlerts.getAlert()

  # Начать обработку сообщений из Splunk
  for alert in alerts:
    try: 
      ticket = splunkAlerts.parseAlert(alert)
      ticket['messageId'] = uuid.uuid1()
    
    except Exception, e:
      logger.error(e)

    #print config['splunk.servers'].get(ticket.get('computerName'))

    #ticket1 = None
    #ticket1 = db.getTicket(eventCode, eventType, computerName)
    #if not ticket1:
    #  db.setTicket(ticket)

      #message = gate.createSOAPMessage(id, 'SMAC', alert[3], comment, 'P002')
      #response = gate.sendSOAPMessage(message)
      #logger.info(''.join(['Get response: ', str(response)]))
    #  db.updateTicket(status, eventCode, eventType, computerName)

  logger.info('Stop SplunkGate')
