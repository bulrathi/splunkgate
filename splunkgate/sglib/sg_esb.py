# -*- coding: utf-8 -*-

__author__  = "bw"
__version__ = "0.1.0"

import json
import httplib, urllib
from datetime import datetime, date, time

class esb_handler:

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


  def __create_ticket_message(self, parameters):
    return """<Systems>
    <Systemcode>%s</Systemcode>
    <Task>%s</Task>
    <Comment>%s</Comment>
    <Priority>%s</Priority></Systems>""" % (self.config['systemCode'], parameters['alert'], parameters['comment'], self.config['priority'])


  def __create_get_ticket_status_message(self, parameters):
    return """<issueId>%s</issueId>""" % (parameters['jiraId'])


  def __create_soap_message(self, parameters, messageType):
    """
    Создать SOAP-сообщения для отправки в ESB
    """

    if messageType == 1:
      message = self.__create_ticket_message(parameters)
    else:
      message = self.__create_get_ticket_status_message(parameters)

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
      self.config['serviceId'],
      str(datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%s%z")),
      self.config['routeId'],
      self.config['login'],
      self.config['password'],
      message)

    param = param.replace('\n', '')

    return param


  def __send_soap_message(self, message):
    """Отправка SOAP-сообщения в ESB"""

    conn = None
    data = None

    headers = {"Content-type": "text/xml; charset=utf-8", "SOAPAction": ""}
    log = ''.join(['Call ESB: host=http://', self.config['host'], self.config['url'], ';http headers=', str(headers), ';message=', message])
    self.logger.info(log)

    try:
      conn = httplib.HTTPConnection(self.config["host"], timeout=self.config['timeout'])
      conn.request("POST", self.config["url"], message, headers)
      response = conn.getresponse()
      status = response.status
      reason = response.reason
      data = response.read()

      if status == 200:
        log = ''.join(['Success call ESB: status=', str(status), ';reason=', str(reason), ';data=', data])
        self.logger.info(log)
      else:
        log = ''.join(['status=', str(status), ';reason=', str(reason), ';data=', data])
        self.logger.error(log)
        raise Exception(log)


    except httplib.HTTPException, e:
      self.logger.error('Unsuccess call ESB: '+ str(e))
      raise

    except Exception, e:
      self.logger.error('Unsuccess call ESB: '+ str(e))
      raise

    finally:
      if conn:
        conn.close()

    return data


  def create_ticket(self, parameters):
    try:
      message = self.__create_soap_message(parameters, 1)
      response = self.__send_soap_message(message)
      resp = self.__parse_esb_response(response)
      return resp
    except Exception, e:
      raise


  def get_ticket_status(self, parameters):
    try:
      message = self.__create_soap_message(parameters, 2)
      response = self.__send_soap_message(message)
      resp = self.__parse_esb_response(response)
      return resp
    except Exception, e:
      raise


  def __parse_esb_response(self, response):
    bs = "<data xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xsi:type=\"xs:string\">"
    es = "</data>"
    b = response.find(bs)
    e = response.find(es)
    if b != -1 and e != -1:
      r = response[b:e].replace(bs, '').replace(es, '').replace('&quot;','"')
      return json.loads(r)
    else:
      return dict(message=response)
    


