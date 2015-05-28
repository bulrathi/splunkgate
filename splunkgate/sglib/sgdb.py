# -*- coding: utf-8 -*-

import sqlite3

class DBLayer:
  """
  Класс, содержащий методы для работы с базой данных тикетов
  """

  logger = None
  config = {}
  conn = None

  def __init__(self, logger, config):
    """
    Инициализация класса
    В configFile передается dict, содежащий конфигурацию SplunkGate 
    В logger передает объект-логгер
    """

    cur = None
    self.logger = logger
    self.config = config
    self.conn = sqlite3.connect(self.config['splunkgate.db'])
    self.conn.text_factory = str

    with self.conn:
      cur = self.conn.cursor()
      cur.execute('create table if not exists tickets (event_code integer, event_type integer, computer_name varchar(1000), message varchar(2048), message_id varchar(1024), create_date timestamp not null default current_timestamp, send_to_esb_date timestamp, esb_status varchar(1024), primary key(event_code, event_type, computer_name))')
      cur.close()
      self.conn.commit()


  def setTicket(self, eventCode, eventType, computerName, message, messageId):
    """
    Сохранить тикет в БД
    eventCode - код события
    eventType - тип события
    computerName - имя сервера, где произошло событие
    message - описание события
    messageId - идентификатор сообщения, отправленного в ESB
    """
    with self.conn:

      cur = self.conn.cursor()
      cur.execute('insert into tickets (event_code, event_type, computer_name, message, message_id) values (?, ?, ?, ?, ?)', (eventCode, eventType, computerName, message, str(messageId)))
      self.conn.commit()
      cur.close()


  def getTicket(self, eventCode, eventType, computerName):
    """
    Получить тикет из базы данных
    eventCode - код события
    eventType - тип события
    computerName - имя сервера, где произошло событие
    """

    ticket = {}
    with self.conn:
      cur = self.conn.cursor()
      cur.execute('select event_code, event_type, computer_name, message, message_id from tickets where event_code = ? and event_type = ? and computer_name = ?', (eventCode, eventType, computerName))
      row = cur.fetchone()
      if row:
        ticket['eventCode'] = row[0]
        ticket['eventType'] = row[1]
        ticket['computerName'] = row[2]
        ticket['message'] = row[3]
        ticket['messageId'] = row[4]

      cur.close()
      return ticket


  def updateTicket(self, status, eventCode, eventType, computerName):
    """
    Обновить запись с тикетом
    status - статус заказа в Jira
    eventCode - код события
    eventType - тип события
    computerName - имя сервера, где произошло событие
    """

    with self.conn:
      cur = self.conn.cursor()
      cur.execute('update tickets set send_to_esb_date = current_timestamp, esb_status = ? where event_code = ? and event_type = ? and computer_name = ?', (status, eventCode, eventType, computerName))
      self.conn.commit()
