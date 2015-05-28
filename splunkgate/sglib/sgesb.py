# -*- coding: utf-8 -*-

import httplib, urllib
from datetime import datetime, date, time

class ESBHandler:
  """Интеграция с ESB"""
  logger = None
  config = {}

  def __init__(self, logger, config):
    """
    Инициализация класса
    В configFile передается dict, содежащий конфигурацию SplunkGate 
    В logger передает объект-логгер
    """
    self.logger = logger
    self.config = config


  def createSOAPMessage(self, id, systemCode, task, comment, priority):
    """
    Создать SOAP-сообщения для отправки в ESB
    id - идентификатор сообщения
    systemCode - код системы - инициатора сообщения
    task - описание задачи, создаваемой в Jira
    comment - комментарий к задаче в Jira
    priority - приоритет
    """

    param = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:typ="http://ish.curs.kz/SyncChannel/v10/Types">
      <soapenv:Header/>
      <soapenv:Body>
        <typ:SendMessage>
          <request>
            <requestInfo>
              <messageId>""" + str(id) + """</messageId>
              <serviceId>""" + self.config["esb.serviceId"] + """</serviceId>
              <messageDate>""" + str(datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%s%z")) + """</messageDate>
              <routeId>""" + self.config["esb.routeId"] + """</routeId>
              <sender>
                <senderId>""" + self.config["esb.login"] + """</senderId>
                <password>""" + self.config["esb.password"] +"""</password>
              </sender>
              <properties>
                <key/>
                <value/>
              </properties>
              <sessionId/>
            </requestInfo>
            <requestData>
              <data>
                <Systems>
                  <Systemcode>""" + systemCode + """</Systemcode>
                  <Task>""" + task + """</Task>
                  <Comment>""" + comment + """</Comment>
                  <Priority>""" + priority + """</Priority>
                </Systems>
              </data>
            </requestData>
          </request>
        </typ:SendMessage>
      </soapenv:Body>
    </soapenv:Envelope>"""

    return param


  def sendSOAPMessage(self, message):
    """Отправка SOAP-сообщения в ESB"""

    data = None

    headers = {"Content-type": "text/xml; charset=utf-8", "SOAPAction": ""}

    log = ''.join(['Call ESB: host=http://', self.configParams['esb.host'], self.configParams['esb.url'], ';http headers=', str(headers), ';message=', message])
    self.logger.info(log)

    try:
      conn = httplib.HTTPConnection(self.configParams["esb.host"])
      conn.request("POST", self.configParams["esb.url"], message, headers)
      response = conn.getresponse()
      status = response.status
      reason = response.reason

      log = ''.join(['Success call ESB: status=', str(status), ';reason=', str(reason), ';data=', str(response.read())])
      self.logger.info(log)

      data = response.read()

    except Exception, e:
      self.logger.error('Unsuccess call ESB: '+ str(e))

    finally:
      conn.close()

    return data