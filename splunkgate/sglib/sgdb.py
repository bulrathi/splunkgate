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
    self.conn = sqlite3.connect(self.config['database'])
    self.conn.text_factory = str

    with self.conn:
      cur = self.conn.cursor()
      cur.execute("""CREATE TABLE IF NOT EXISTS tickets
        (event_code integer,
          event_type integer,
          computer_name varchar(1000),
          message varchar(2048),
          message_id varchar(1024),
          create_date timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
          send_to_esb_date timestamp,
          jira_key varchar(1024),
          jira_id integer,
          primary key(event_code, event_type, computer_name)
        )""")

      cur.close()
      self.conn.commit()


  def setTicket(self, ticket):
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
      cur.execute('INSERT INTO tickets (event_code, event_type, computer_name, message, message_id) VALUES (:eventCode, :eventType, :computerName, :message, :messageId)', (ticket))
      self.conn.commit()
      cur.close()


  def getTicket(self, ticketParam):
    """
    Получить тикет из базы данных
    eventCode - код события
    eventType - тип события
    computerName - имя сервера, где произошло событие
    """

    ticket = {}
    with self.conn:
      cur = self.conn.cursor()

      cur.execute('SELECT event_code, event_type, computer_name, message, message_id, jira_id, jira_key FROM tickets WHERE event_code = :eventCode AND event_type = :eventType AND computer_name = :computerName', (ticketParam))

      row = cur.fetchone()
      if row:
        ticket['eventCode'] = row[0]
        ticket['eventType'] = row[1]
        ticket['computerName'] = row[2]
        ticket['message'] = row[3]
        ticket['messageId'] = row[4]
        ticket['jira_id'] = row[5]
        ticket['jira_key'] = row[6]

      cur.close()
      return ticket


  def updateTicket(self, ticket):
    """
    Обновить запись с тикетом
    status - статус заказа в Jira
    eventCode - код события
    eventType - тип события
    computerName - имя сервера, где произошло событие
    """

    with self.conn:
      cur = self.conn.cursor()
      cur.execute('UPDATE tickets SET send_to_esb_date = CURRENT_TIMESTAMP, jira_key = :jiraKey, jira_id = :jiraId WHERE event_code = :eventCode AND event_type =:eventType AND computer_name = :computerName', (ticket))
      self.conn.commit()
