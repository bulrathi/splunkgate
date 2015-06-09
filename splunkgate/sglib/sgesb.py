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


  def createTicketMessage(self, parameters):
    return """<Systems>
    <Systemcode>%s</Systemcode>
    <Task>%s</Task>
    <Comment>&quot;%s&quot;</Comment>
    <Priority>%s</Priority></Systems>""" % ('SMAC', parameters['alert'], parameters['comment'], 'P002')


  def createGetTicketStatusMessage(self, parameters):
    return """<issueId>%s</issueId>""" %  (parameters['issueId'])


  def createSOAPMessage(self, parameters, messageType):
    """
    Создать SOAP-сообщения для отправки в ESB
    """

    if messageType == 1:
      message = self.createTicketMessage(parameters)
    else:
      message = self.createGetTicketStatusMessage(parameters)


    param = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:typ="http://ish.curs.kz/SyncChannel/v10/Types">
      <soapenv:Header/>
      <soapenv:Body>
        <typ:SendMessage>
          <request>
            <requestInfo>
              <messageId>%s</messageId>
              <serviceId>%s</serviceId>
              <messageDate>%s</messageDate>
              <routeId>%s</routeId>
              <sender>
                <senderId>%s</senderId>
                <password>%s</password>
              </sender>
              <properties>
                <key/>
                <value/>
              </properties>
              <sessionId/>
            </requestInfo>
            <requestData>
              <data>%s</data>
            </requestData>
          </request>
        </typ:SendMessage>
      </soapenv:Body>
    </soapenv:Envelope>""" % (parameters['messageId'],
      parameters['serviceId'],
      str(datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%s%z")),
      parameters['routeId'],
      parameters['login'],
      parameters['password'],
      message)

    return param


  def sendSOAPMessage(self, message):
    """Отправка SOAP-сообщения в ESB"""

    data = None

    headers = {"Content-type": "text/xml; charset=utf-8", "SOAPAction": ""}
    print message
    log = ''.join(['Call ESB: host=http://', self.config['host'], self.config['url'], ';http headers=', str(headers), ';message=', message])
    self.logger.info(log)

    try:
      conn = httplib.HTTPConnection(self.config["host"])
      conn.request("POST", self.config["url"], message, headers)
      response = conn.getresponse()
      status = response.status
      reason = response.reason
      print response.read()
      #print reason
      #log = ''.join(['Success call ESB: status=', str(status), ';reason=', str(reason), ';data=', str(response.read())])
      #self.logger.info(log)

      data = response.read()

    except Exception, e:
      self.logger.error('Unsuccess call ESB: '+ str(e))

    finally:
      conn.close()

    return data


  def createTicket(self, parameters):
    message = self.createSOAPMessage(parameters, 1)
    self.sendSOAPMessage(message)


  def getTicketStatus(self, parameters):
    message = self.createSOAPMessage(parameters, 2)
    self.sendSOAPMessage(message)


