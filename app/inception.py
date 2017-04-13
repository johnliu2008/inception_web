#coding=utf-8

import MySQLdb
from db_config import *
import re

def audit(opt_username, db_select, sql_content, is_execute):
    if db_select != '' and sql_content != '':
        p_drop_table = re.compile(r'drop\s+table')
        p_drop_db = re.compile(r'drop\s+database')
        p_drop_partition = re.compile(r'drop\s+partition')
        p_truncate = re.compile(r'truncate\s+table')
        m_drop_table = p_drop_table.search(sql_content.lower())
        m_drop_partition = p_drop_partition.search(sql_content.lower())
        m_drop_db = p_drop_db.search(sql_content.lower())
        m_truncate = p_truncate.search(sql_content.lower())
        if m_drop_table is not None:
            return unicode('审核不通过！ 不能包含【DROP TABLE】语句！！', "utf-8").split("\n")
        elif m_drop_db is not None:
            return unicode('审核不通过！ 不能包含【DROP DATABASE】语句！！', "utf-8").split("\n")
        elif m_drop_partition is not None:
            return unicode('审核不通过！ 不能包含【DROP PARTITION】语句！！', "utf-8").split("\n")
        elif m_truncate is not None:
            return unicode('审核不通过！ 不能包含【TRUNCATE TABLE】语句！！', "utf-8").split("\n")
        else:
            conn = db_conn[db_select]
            sql1='/*--user=%s;--password=%s;--host=%s;%s;--port=%s;*/\
                    inception_magic_start;\
                    ' % (conn['user'], conn['password'], conn['host'], is_execute, conn['port'], )
            sql2='inception_magic_commit;'
            sql = sql1 + sql_content + sql2
            try:
                conn=MySQLdb.connect(host=inception_server['host'],user=inception_server['user'],passwd=inception_server['password'],db='',port=inception_server['port'],use_unicode=True, charset="utf8")
                cur=conn.cursor()
                ret=cur.execute(sql)
                result=cur.fetchall()
                num_fields = len(cur.description)
                field_names = [i[0] for i in cur.description]
                print field_names
                for row in result:
                    print row[0], "|",row[1],"|",row[2],"|",row[3],"|",row[4],"|",row[5],"|",row[6],"|",row[7],"|",row[8],"|",row[9],"|",row[10]
                cur.close()
                conn.close()
            except MySQLdb.Error,e:
                print "Mysql Error %d: %s" % (e.args[0], e.args[1])

            final_result = result[len(result)-1][4]
            if final_result == 'None':
                #记录操作日志
                backup_dbname = result[len(result)-1][8]
                opid = result[len(result)-1][7].strip("'")
                sql_statement = result[len(result)-1][5]
                logdb_conn = MySQLdb.connect(host=incep_bakdb['host'], port=incep_bakdb['port'], user=incep_bakdb['user'], passwd=incep_bakdb['password'], db='inception')
                logdb_conn.autocommit(True)
                cur_log = logdb_conn.cursor()
                # log_sql = '''INSERT INTO t_sys_log
                #             (opt_username, opt_time, bakdb, opid, sql_statement)
                #             VALUES ('%s', now(), '%s', %s, '%s')''' % (opt_username, backup_dbname, opid, sql_statement[:20])
                log_sql = '''INSERT INTO t_sys_log
                            (opt_username, opt_time, bakdb, opid, sql_statement)
                            VALUES (%s, now(), %s, %s, %s)'''
                # print log_sql
                cur_log.execute(log_sql, (opt_username, backup_dbname, opid, sql_statement[:20]))
                cur_log.close()
                logdb_conn.close()
                final_result = unicode('操作成功！')
            return final_result.split("\n")
    else:
        return unicode('请选择DB，并输入要审核的SQL！').split("\n")


def dash_board():
    conn = MySQLdb.connect(host=incep_bakdb['host'], port=incep_bakdb['port'], user=incep_bakdb['user'], passwd=incep_bakdb['password'])
    conn.autocommit(True)
    try:
        get_dbs_sql = "show databases like '%\_%\_%\_%'"  # 192_168_88_11_3306_test, '192_168_88_11_3306_game'
        cur_dbs = conn.cursor()
        cur_dbs.execute(get_dbs_sql)
        dbs_list = cur_dbs.fetchall()   # [['192_168_88_11_3306_test',],['192_168_88_11_3306_game',]]
        if dbs_list != ():
            all_records = []
            for i in range(len(dbs_list)):
                backup_dbname = dbs_list[i][0]  # '192_168_88_11_3306_test'
                opt_record_sql = "select @rownum:=@rownum+1 rn, %s, opid_time, time, type, tablename from " + backup_dbname +".$_$inception_backup_information$_$ order by time desc limit 8"
                cur_dbs.execute('set @rownum=0;')
                cur_dbs.execute(opt_record_sql, (backup_dbname,))
                opt_record = cur_dbs.fetchall()
                if opt_record != ():
                    all_records.append(opt_record)
                # else:
                #     all_records.append()  # 在当前查询的备份库未找到任何操作记录。正常不会出现这样的情况，如果出现，很有可能是人为删除了操作记录。

            # print all_records
            return all_records
        else:
            return '未找到任何备份库，请确认是否配置了正确的备份库连接信息'
    except Exception, e:
        print (str(e))
        return None
    finally:
        cur_dbs.close()
        conn.close()

def get_more_operation(bakdb):
    conn = MySQLdb.connect(host=incep_bakdb['host'], port=incep_bakdb['port'], user=incep_bakdb['user'], passwd=incep_bakdb['password'])
    conn.autocommit(True)
    try:
        opt_record_sql = "select @rownum:=@rownum+1 rn, %s, opid_time, time, type, tablename from " + bakdb + ".$_$inception_backup_information$_$ order by time desc"
        # opt_record_sql = "select if(rn=1,'%s',''),opid_time, time, type, tablename from(select @rownum:=@rownum+1 rn, opid_time, time, type, tablename from %s.$_$inception_backup_information$_$ order by time desc) x" % (bakdb, bakdb)
        cur_dbs = conn.cursor()
        cur_dbs.execute('set @rownum=0;')
        cur_dbs.execute(opt_record_sql, (bakdb,))
        opt_record = cur_dbs.fetchall()
        # print opt_record
        return opt_record
    except Exception, e:
        print (str(e))
        return None
    finally:
        cur_dbs.close()
        conn.close()

def get_operation_detail(bakdb, opid):
    conn = MySQLdb.connect(host=incep_bakdb['host'], port=incep_bakdb['port'], user=incep_bakdb['user'], passwd=incep_bakdb['password'])
    conn.autocommit(True)
    try:
        all_records = []
        table_name_sql = "select t.tablename from " + bakdb + ".$_$inception_backup_information$_$ t where t.opid_time=%s"
        cur_dbs = conn.cursor()
        cur_dbs.execute(table_name_sql, (opid,))
        table_result = cur_dbs.fetchall()
        if table_result != ():
            tablename = table_result[0][0]
            opt_detail_sql = """select %s,t.opid_time,t.time,t.tablename,IF(t.start_binlog_file='','N/A',t.start_binlog_file),t.start_binlog_pos,IF(t.end_binlog_file='','N/A',t.end_binlog_file),t.end_binlog_pos,t.sql_statement,b.rollback_statement
                                 from """ + bakdb + ".$_$inception_backup_information$_$ t left join " + bakdb + "." + tablename + " b on t.opid_time=b.opid_time where t.opid_time=%s"
            cur_dbs.execute(opt_detail_sql, (bakdb, opid))
            detail = cur_dbs.fetchall()
            all_records.append(detail)
            # print all_records
            # if all_records != ():
            return all_records
            # else:
            #     return None
        else:
            return None
    except Exception, e:
        print (str(e))
        return None
    finally:
        cur_dbs.close()
        conn.close()

def complexity_check(username, passwd):
    p_user = re.compile(r'(?!^[0-9]+$)(^[a-zA-Z]\w{6,}$)') # 用户名和密码长度须大于等于6位，且不能包含特殊字符，必须以字母开头，不能是纯数字
    p_pass = re.compile(r'(?!^[a-zA-Z]+$)(?!^[0-9]+$)(^[a-zA-Z]\w{6,}$)') #用户名和密码长度须大于等于6位，且不能包含特殊字符，必须以字母开头，密码必须是字母、数字、下划线的组合
    m_user = p_user.match(username)
    m_pass = p_pass.match(passwd)
    if m_user and m_pass and username != passwd:
        return True
    else:
        return False

def login(username, passwd):
    conn = MySQLdb.connect(host=incep_bakdb['host'], port=incep_bakdb['port'], user=incep_bakdb['user'], passwd=incep_bakdb['password'], db='inception')
    conn.autocommit(True)
    try:
        select_sql = "select enabled from t_sys_user t where t.username=%s"
        cur = conn.cursor()
        cur.execute(select_sql, (username,))
        select_result = cur.fetchall()
        if select_result != (): #如果用户存在
            # is_enabled_sql = "select enabled from t_sys_user t where t.username=%s"
            # cur.execute(is_enabled_sql)
            # is_enabled_result = cur.fetchall()
            if select_result[0][0] == 0: #如果用户被禁用
                return 'disabled'
            else:
                login_sql = "select 1 from t_sys_user t where t.username=%s and t.passwd=md5(%s) and enabled=1 and logon_failed_cnt<5"
                cur.execute(login_sql, (username, passwd))
                login_result = cur.fetchall()
                if login_result != ():
                    #如果用户登录成功，则更新“登录时间”,并把“失败计数”清0
                    update_sql = "update t_sys_user set last_logon_time=now(),logon_failed_cnt=0 where username=%s"
                    # print update_sql
                    cur.execute(update_sql, (username,))
                    return True
                else:  # 否则“登录失败计数”+1
                    update_sql = "update t_sys_user set last_logon_time=now(),logon_failed_cnt=logon_failed_cnt+1,enabled=if(logon_failed_cnt=5,0,1) where enabled=1 and username=%s"
                    # print update_sql
                    cur.execute(update_sql, (username,))
                    return 'wrong passwd'
        else: #用户不存在
            return 'user not exist'
        cur.close()
    except Exception, e:
        print (str(e))
        return False
    finally:
        conn.close()

def create_sys_user(username, passwd):
    conn = MySQLdb.connect(host=incep_bakdb['host'], port=incep_bakdb['port'], user=incep_bakdb['user'], passwd=incep_bakdb['password'], db='inception')
    conn.autocommit(True)
    try:
        select_sql = "select 1 from t_sys_user t where t.username=%s"
        cur = conn.cursor()
        cur.execute(select_sql, (username,))
        is_exists = cur.fetchall()
        if is_exists == ():
            insert_sql = "INSERT INTO t_sys_user (username, passwd, create_time, enabled) VALUES (%s, md5(%s), NOW(), 1)"
            cur.execute(insert_sql, (username, passwd))
            return True
        else:
            #用户已存在
            return False
        cur.close()
    except Exception, e:
        print(str(e))
    finally:
        conn.close()


def manage_sys_user(username, passwd, enabled):
    conn = MySQLdb.connect(host=incep_bakdb['host'], port=incep_bakdb['port'], user=incep_bakdb['user'], passwd=incep_bakdb['password'], db='inception')
    conn.autocommit(True)
    try:
        select_sql = "select 1 from t_sys_user t where t.username=%s"
        cur = conn.cursor()
        cur.execute(select_sql, (username,))
        is_exists = cur.fetchall()
        if is_exists != ():
            if passwd != '':
                check = complexity_check(username, passwd)
                if check:
                    update_sql = "update t_sys_user set enabled=%s, passwd=md5(%s) where username=%s"
                    cur.execute(update_sql, (enabled, passwd, username))
                    return True
                else:
                    return 'complexity_check fail'
            else:
                update_sql = "update t_sys_user set enabled=%s where username=%s"
                cur.execute(update_sql, (enabled, username))
                return True
        else:
            #用户不存在
            return False
        cur.close()
    except Exception, e:
        print(str(e))
    finally:
        conn.close()

def check_opt_log():
    conn = MySQLdb.connect(host=incep_bakdb['host'], port=incep_bakdb['port'], user=incep_bakdb['user'], passwd=incep_bakdb['password'], db='inception')
    conn.autocommit(True)
    try:
        select_sql = "SELECT opt_username, opt_time, bakdb, opid, sql_statement	FROM t_sys_log where bakdb!='None' and opt_time>=date_add(curdate(), interval -3 month) order by opt_time desc,opt_username"
        cur = conn.cursor()
        cur.execute(select_sql)
        result = cur.fetchall()
        return result
    except Exception, e:
        print (str(e))
        return False
    finally:
        conn.close()

def statistics():
    conn = MySQLdb.connect(host=incep_bakdb['host'], port=incep_bakdb['port'], user=incep_bakdb['user'], passwd=incep_bakdb['password'], db='inception')
    conn.autocommit(True)
    try:
        select_sql = """SELECT date_format(optime, '%Y-%m-%d'), sum(selecting), sum(deleting)+sum(inserting)+sum(updating) dml, sum(altertable)+sum(renaming) 'alter', sum(createindex)+sum(dropindex) 'index', sum(addcolumn)+sum(dropcolumn)+sum(changecolumn)+sum(alteroption)+sum(alterconvert) 'column', sum(createtable)+sum(droptable)+sum(truncating) 'c/d/t table', sum(createdb)
	                    FROM statistic group by date_format(optime, '%Y-%m-%d') order by 1"""
        cur = conn.cursor()
        cur.execute(select_sql)
        result = cur.fetchall()
        return result
    except Exception, e:
        print (str(e))
        return False
    finally:
        conn.close()

get_operation_detail('192_168_88_11_3306_test', '1487837975_407577_1')