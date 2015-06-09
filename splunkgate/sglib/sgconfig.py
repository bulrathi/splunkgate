# -*- coding: utf-8 -*-

__author__  = "bw"
__version__ = "0.1"

import sys
import logging
import ConfigParser
from optparse import OptionParser
from optparse import OptionGroup

class Configuration(object):
  def __init__(self, fname):
    self.fname = fname
    self.config = ConfigParser.RawConfigParser()
    self.config.read(fname)

  def get_sections(self):
    return self.config.sections()

  def get_config(self, section):
    return self.config.items(section)

  def get_errors_list(self, section):
    errors = self.config.items(section)
    err_list = {}
    for error in errors:
      _e = error[1].split(',')
      _e_d = dict(code = int(_e[0]), dscr = _e[1].strip(), severity = _e[2].strip())
      err_list[error[0]] = _e_d
    return err_list

  def get_server_list(self, section):
    servers = self.config.items(section)
    print servers
    server_list = {}
    for server in servers:
      server_list[server[0]] = server[1]
    return server_list

  def get_options(self, section):
    options = self.config.items(section)
    opt_list = {}
    for opt in options:
      opt_list[opt[0]] = opt[1]
    return opt_list

  def get_list(self, section, option):
    return [chunk.strip().strip('\n') for chunk in self.config.get(section, option).split(',')]

  def get_option_str(self, section, option):
    return self.config.get(section, option)

  def get_option_int(self, section, option):
    return self.config.getint(section, option)

  def get_option_bool(self, section, option):
    return self.config.getboolean(section, option)

  def get_option_float(self, section, option):
    return self.config.getfloat(section, option)

  def get_modules(self):
    modules = self.get_list('modules', 'modules')
    modules_part = {}
    for module in modules:
      module_list = self.get_options('modules.' + module)
      errors = self.get_errors_list('modules.' + module + '.errors')
      modules_part[module] = dict(methods = module_list, errors = errors)
    return modules_part

  def get_logger(self, section, loggername):
    lvl_dscr = self.config.get(section, 'level')
    level = None
    if lvl_dscr in 'debug': level = logging.DEBUG
    elif lvl_dscr in 'info': level = logging.INFO
    elif lvl_dscr in 'warning': level = logging.WARNING
    elif lvl_dscr in 'critical': level = logging.CRITICAL
    elif lvl_dscr in 'exception': level = logging.EXCEPTION
    else: level = logging.DEBUG

    logging.basicConfig(format = self.config.get(section, 'format'),
      level = level,
      filename = self.config.get(section,'logname'))
    return logging.getLogger(loggername)

