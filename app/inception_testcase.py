#!/usr/bin/env python
# encoding:utf-8
__author__ = 'Liuj'

from db_config import *
import MySQLdb
import time

def test_inception():
    inception_conn = MySQLdb.connect(host=inception_server['host'],user=inception_server['user'],passwd=inception_server['password'],db='',port=inception_server['port'],use_unicode=True, charset="utf8")
    testcase_conn = MySQLdb.connect(host='192.168.88.221',user='root',passwd='abc123',db='test',port=6606,use_unicode=True, charset="utf8")
    testcase_conn.autocommit(True)
    incep_bakdb_conn = MySQLdb.connect(host='192.168.88.221',user='root',passwd='abc123',db='192_168_88_11_3306_test',port=6606,use_unicode=True, charset="utf8")
    db=db_conn['RC_main']
    sql1='/*--user=%s;--password=%s;--host=%s;--execute=1;--port=%s;*/\
                inception_magic_start; \
         use test;\
                ' % (db['user'], db['password'], db['host'], db['port'], )
    sql2='inception_magic_commit;'
    try:
        cur_testcase=testcase_conn.cursor()
        ret1=cur_testcase.execute('select id,test_sql from t_inception_testcase_v0 where id>0') #从测试用例表取出测试SQL
        testcase_result=cur_testcase.fetchall()



        for i in range(len(testcase_result)):
            cur_inception=inception_conn.cursor()
            cur_incep_bakdb=incep_bakdb_conn.cursor()
            testcase_id= testcase_result[i][0]
            test_sql = testcase_result[i][1]
            test_sql = sql1 + test_sql + sql2

            ret2=cur_inception.execute(test_sql) #将SQL发送到inception执行
            inception_result=cur_inception.fetchall()
            print inception_result
            final_result = inception_result[len(inception_result)-1][4]
            opid_time = inception_result[len(inception_result)-1][7]
            if final_result != 'None':
                output_sql = "update t_inception_testcase_v0 set output='%s' where id=%s;" % (final_result.replace("'", "\\'"), testcase_id)
                cur_testcase.execute(output_sql) #如果inception审核失败，则将inception返回的结果更新到testcase表
            else:
                sql = "select t11.rollback_statement from t11 inner join $_$inception_backup_information$_$ i on t11.opid_time=i.opid_time where i.opid_time=%s" % (opid_time)
                cur_incep_bakdb.execute(sql)
                incep_bakdb_result = cur_incep_bakdb.fetchall() #如果inception审核通过，则去检查备份库中是否有相应的rollback SQL
                if incep_bakdb_result != ():
                    rollback_sql = incep_bakdb_result[0][0].replace("'", "\\'")
                else:
                    rollback_sql = 'rollback_sql not found!' + sql.replace("'", "\\'")
                output_sql = "update t_inception_testcase_v0 set output='%s' where id=%s;" % (rollback_sql, testcase_id)
                cur_testcase.execute(output_sql)

            # time.sleep(1)
            cur_incep_bakdb.close()
            cur_inception.close()
        cur_testcase.close()

        incep_bakdb_conn.close()
        inception_conn.close()
        testcase_conn.close()

    except MySQLdb.Error,e:
        testdb_conn = MySQLdb.connect(host=db['host'],user=db['user'],passwd=db['password'],db='test',port=3306,use_unicode=True, charset="utf8")
        testdb_conn.autocommit(True)
        cur = testdb_conn.cursor()
        rename_sql = 'alter table t11 rename to t11_%s' % time.strftime('%Y-%m-%d %H:%M:%S').replace('-','').replace(':','').replace(' ','') #比如20170217165014
        cur.execute(rename_sql)
        cur.close()
        testdb_conn.close()

        incep_bakdb_conn.close()
        inception_conn.close()
        testcase_conn.close()
        print "Mysql Error  %s" % (e)




test_inception()