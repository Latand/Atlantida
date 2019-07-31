#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8
import logging

import pymysql

from config import sql_config


class Mysql(object):
    def __init__(self, params, debug=False):
        self.params = params
        self.connection = None  # self.connect()
        self.debug = debug
        self.if_cursor_dict = False

    def connect(self):
        self.connection = pymysql.connect(**self.params)
        return self.connection

    def insert(self, table, returning=False, if_not_exists=False, **kwargs):
        what = []
        if "what" in kwargs.keys():
            if isinstance(kwargs["what"], str):
                what = [kwargs["what"]]
            else:
                what = kwargs["what"]
            iterate = ", ".join(["%s" for _ in range(len(what))])
            if isinstance(kwargs["where"], list):
                where = ", ".join([
                    f"`{item}`" for item in kwargs["where"]
                ])
            else:
                where = kwargs["where"]
        else:
            where = ""
            iterate = ""
            for key, value in kwargs.items():
                if key not in ["returning", "table"]:
                    where += "{}, ".format(key)
                    iterate += "%s, "
                    what.append(value)
            iterate = iterate[:-2]
            where = where[:-2]

        exists = "IF NOT EXISTS" if if_not_exists else ""
        command = f"INSERT {exists} INTO `{table}`({where}) VALUES ({iterate})"
        return self.execute(command, what, returning=returning)

    def select(self, where, what="*", one_element=True, multiple=False, limit=None, condition=None, or_condition=None,
               order=None, cursor_dict=False, join: dict = None, groupby=None, left_join=None):
        """

        :param where:
        :param what:
        :param one_element:
        :param multiple:
        :param limit:
        :param condition:
        :param or_condition:
        :param order:
        :param cursor_dict:
        :param join: kwargs: table, column, rel_column
        :param groupby:
        :return:
        """
        args = list()
        if not any([x in what for x in ["SUM", "COUNT", "DISTINCT", "MAX", "AVG"]]):
            if isinstance(what, str):
                what = what,
            # what = ", ".join([f"`{column_name}`" for column_name in what])
            what = ", ".join(what)
        command = "SELECT {0} FROM {1} ".format(
            what, where
        )
        if join:
            command += "JOIN {table} ON {column}={rel_column}".format(**join)
        if left_join:
            command += "LEFT JOIN {table} ON {column}={rel_column}".format(**left_join)

        if condition:
            command += " WHERE "
            for item, value in condition.items():

                if not any([x.lower() in str(value).lower() for x in ["<", ">", "!", "IS", "=", "("]]):
                    command += " {} = %s AND".format(item)
                    args.append(value)
                else:
                    command += " {} {} AND".format(item, value)
            command = command[:-3] if command.endswith("AND") else command
        if or_condition:

            for item, value in or_condition.items():
                command += " OR "
                if not any([x in str(value) for x in ["<", ">", "!", "IS"]]):
                    command += " {} = %s".format(item)
                    args.append(value)
                else:
                    command += " {} {}".format(item, value)
        if groupby:
            command += " GROUP BY {}".format(groupby)

        if order:
            command += " ORDER BY {}".format(order)

        if limit:
            command += " LIMIT {}".format(limit)
        return self.execute(command, args, select=True, one_element=one_element, multiple=multiple,
                            cursor_dict=cursor_dict)

    def delete(self, table, what=None, where=None, condition: dict = None):
        if not condition:
            if where:
                if not what:
                    raise NotImplementedError
                if isinstance(where, str):
                    where = [where]
                where = "AND ".join(["`{}` = %s ".format(wher) for wher in where])
            else:
                where = 1
                what = []
            return self.execute(command="DELETE FROM {} WHERE {}".format(table, where),
                                args=what)
        else:
            args = []
            command = f"DELETE FROM {table} WHERE "
            for item, value in condition.items():

                if not any([x.lower() in str(value).lower() for x in ["<", ">", "!", "IS", "=", "("]]):
                    command += " {} = %s AND".format(item)
                    args.append(value)
                else:
                    command += " {} {} AND".format(item, value)
            command = command[:-3] if command.endswith("AND") else command
            logging.info(command + str(args))
            return self.execute(command=command, args=args)

    def update(self, table, **kwargs):
        args = []
        command = "UPDATE `{0}` SET ".format(table)
        for items, value in kwargs.items():
            if items != "condition":
                if items == "raw":
                    continue
                if "CURRENT_TIMESTAMP" not in str(value):
                    command += " `{}` = %s,".format(items) if "raw" not in kwargs else " `{}` = {},".format(items,
                                                                                                            value)
                    args.append(value)

                else:
                    command += f" `{items}` = {value},"
        command = command[:-1] if command.endswith(",") else command
        command += " WHERE "
        if "condition" in kwargs:
            for item, value in kwargs["condition"].items():
                command += " `{}` = %s AND".format(item) if "raw" not in kwargs else " `{}` = {} AND".format(item,
                                                                                                             value)
                args.append(value)
        command = command[:-3] if command.endswith("AND") else command
        if "raw" in kwargs:
            args.clear()
        self.execute(command, args, kwargs=kwargs)

    def execute(self, command, args=(), select=False, returning=False, kwargs={}, one_element=True, multiple=False,
                cursor_dict=False):
        logging.info(f"Command: {command}\n\nArgs={args}")
        self.connection = self.connect()
        c = None
        if self.if_cursor_dict or cursor_dict:
            c = pymysql.cursors.DictCursor
        if self.debug:
            with self.connection.cursor(c) as cursor:
                logging.debug(f"{command}, {args}, {kwargs}")
                cursor.execute(command, (*args,))
                if returning:
                    ids = cursor.lastrowid
                self.connection.commit()
            if select:
                values = cursor.fetchall()
                self.connection.close()
                if not multiple:
                    if one_element:

                        if len(values) == 1:
                            if isinstance(values[0], tuple) and len(values[0]) == 1:
                                values = values[0][0]

                logging.debug(str(values).encode())
                return values
            elif returning:
                return ids
        else:
            cursor = self.connection.cursor(c)
            try:
                cursor.execute(command, (*args,))
                if returning:
                    ids = cursor.lastrowid
            except pymysql.err.OperationalError as err:
                logging.exception("Operational error. restart {}\n{}\n{}".format(command, kwargs, err))
                return
                # self.connection.close()
                # self.connect()
                # cursor = self.connection.cursor()
                # cursor.execute(command, (*args,))
            except pymysql.err.InterfaceError as err:
                print("InterfaceError (bad command), "
                      "reconnecting, executing", err)
                logging.exception("InterfaceError (bad command), "
                                  "reconnecting, executing {}".format(err))
                return
                # self.connection.close()
                # self.connect()
                # cursor = self.connection.cursor()
                # cursor.execute(command, (*args,))
            except pymysql.err.ProgrammingError as err:
                print("Programming error (bad command), {} \n{} ".format(err, [command, kwargs, args]))
                logging.exception("Programming error (bad command), {} \n{} ".format(err, [command, kwargs, args]))
                return
            except pymysql.err.IntegrityError as err:
                logging.exception("IntegrityError, dublicate primary key? {}".format(err))
                print("IntegrityError, dublicate primary key? ", err)
                return
            except Exception as err:
                print("Other error. {}\n {}, \n{}".format(command, (kwargs, args), err))
                logging.exception("Other error. {}\n {}, \n{}".format(command, (kwargs, args), err))
                return
            if select:

                values = cursor.fetchall()
                self.connection.close()
                if not multiple:
                    if one_element:
                        if len(values) == 1:
                            if isinstance(values[0], tuple) and len(values[0]) == 1:
                                values = values[0][0]

                return values
            else:
                self.connection.commit()
                self.connection.close()
                if returning:
                    return ids

    def exec_raw(self, command, select=False, multiple=False, cursor_dict=False):
        self.connection = self.connect()
        try:
            if cursor_dict:
                cursor = self.connection.cursor(pymysql.cursors.DictCursor)
            else:
                cursor = self.connection.cursor()
            cursor.execute(command)
            self.connection.commit()
            if select:
                values = cursor.fetchall()

                if not multiple:
                    if len(values) == 1:
                        if isinstance(values[0], tuple) and len(values[0]) == 1:
                            values = values[0][0]
                return values
            self.connection.close()
        except pymysql.err.OperationalError as err:
            print("Operational error. restart {}\n{}".format(command, err))
        except pymysql.err.InterfaceError as err:
            print("InterfaceError (bad command), "
                  "reconnecting, executing", err)
            logging.exception("InterfaceError (bad command), "
                              "reconnecting, executing {}".format(err))

        except pymysql.err.ProgrammingError as err:
            print("Programming error (bad command), {} \n{} ".format(err, [command]))
            logging.exception("Programming error (bad command), {} \n{} ".format(err, [command]))
        except pymysql.err.IntegrityError as err:
            logging.exception("IntegrityError, dublicate primary key? {}".format(err))
            print("IntegrityError, dublicate primary key? ", err)
        except Exception as err:
            print("Other error. {}\n, \n{}".format(command, err))
            logging.exception("Other error. {}\n, \n{}".format(command, err))


sql = Mysql(sql_config, debug=True)
