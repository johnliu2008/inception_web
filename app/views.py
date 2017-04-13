# -*- coding:utf-8 -*-
#coding=utf-8
__author__ = 'lihui'

from app import app
from flask import render_template, flash, redirect,session,url_for,request
from forms import InceptionAudit
import inception

#登录页面
@app.route('/')
@app.route('/login', methods=['POST','GET'])
def login():
    #https://www.douban.com/note/511577488/
    # http://laoxu.blog.51cto.com/4120547/1568677
    session['username'] = False
    session['password'] = False
    if request.method == 'POST':
        username = request.form['username']
        passwd = request.form['password']
        if username != '' and passwd != '':
            # if request.form['username'] != 'admin' or request.form['password'] != 'admin123':
            login_result = inception.login(username, passwd)
            if login_result == 'wrong passwd':
                error = "用户名或密码错误，请重新登录"
                return render_template('login.html', error=error)
            elif login_result == 'user not exist':
                error = "该用户不存在"
                return render_template('login.html', error=error)
            elif login_result == 'disabled':
                error = "用户已禁用"
                return render_template('login.html', error=error)
            else:
                session['username'] = request.form['username']
                session['password'] = request.form['password']
                return redirect(url_for('index'))
        else:
                error = "请输入用户名和密码"
                return render_template('login.html', error=error)
    return render_template('login.html')

#退出登录功能
@app.route("/logout")
def logout():
    session.pop('username',None)
    session.pop('password',None)
    return redirect(url_for('login'))

#创建系统用户
@app.route('/create_sys_user', methods=['POST', 'GET'])
def create_sys_user():
    if session.get('username') == 'admin':
        if request.method == 'POST':
            username = request.form['username']
            passwd = request.form['password']
            if username != '' and passwd != '':
                check = inception.complexity_check(username, passwd)
                if check == True:
                    create = inception.create_sys_user(username, passwd)
                    if create:
                        result = "用户创建成功"
                        return render_template('dba_tool/create_sys_user.html', result=result, username=session.get('username'))
                    else:
                        result = "该用户已存在！"
                        return render_template('dba_tool/create_sys_user.html', result=result, username=session.get('username'))
                else:
                    result = "用户名和密码长度须大于等于6位，且不能包含特殊字符，必须以字母开头；用户名不能是纯数字，密码必须是字母、数字的组合；用户名和密码不同相同"
                    return render_template('dba_tool/create_sys_user.html', result=result, username=session.get('username'))
            else:
                result = "用户名或密码不能为空！"
                return render_template('dba_tool/create_sys_user.html', result=result, username=session.get('username'))
    else:
        return redirect(url_for('login'))
    return render_template('dba_tool/create_sys_user.html', username=session.get('username'))

#管理系统用户
@app.route('/manage_sys_user', methods=['POST', 'GET'])
def manage_sys_user():
    if session.get('username') == 'admin':
        if request.method == 'POST':
            username = request.form['username']
            passwd = request.form['password']
            enabled = request.values.get('enabled')
            if username != '':
                manage = inception.manage_sys_user(username, passwd, enabled)
                if manage == True:
                    result = "用户信息修改成功"
                    return render_template('dba_tool/manage_sys_user.html', result=result, username=session.get('username'))
                elif manage == 'complexity_check fail':
                    result = "用户名和密码长度须大于等于6位，且不能包含特殊字符，必须以字母开头；用户名不能是纯数字，密码必须是字母、数字的组合；用户名和密码不同相同"
                    return render_template('dba_tool/manage_sys_user.html', result=result, username=session.get('username'))
                else:
                    result = "该用户不存在！"
                    return render_template('dba_tool/manage_sys_user.html', result=result, username=session.get('username'))
            else:
                result = "用户名不能为空！"
                return render_template('dba_tool/manage_sys_user.html', result=result, username=session.get('username'))
    else:
        return redirect(url_for('login'))
    return render_template('dba_tool/manage_sys_user.html', username=session.get('username'))

#查看操作日志
@app.route('/check_opt_log')
def check_opt_log():
    if session.get('username') == 'admin':
        html_table_content = inception.check_opt_log()
        return render_template('dba_tool/check_opt_log.html',html_table_content = html_table_content, username=session.get('username'))
    else:
        return redirect(url_for('login'))
    return render_template('dba_tool/check_opt_log.html',html_table_content = html_table_content, username=session.get('username'))

#查看统计信息
@app.route('/statistics')
def statistics():
    if session.get('username'):
        html_table_content = inception.statistics()
        return render_template('dba_tool/statistics.html',html_table_content = html_table_content, username=session.get('username'))
    else:
        return redirect(url_for('login'))
    return render_template('dba_tool/check_opt_log.html',html_table_content = html_table_content, username=session.get('username'))

#首页
# @app.route('/')
@app.route('/index')
def index():
    if session.get('username'):
        html_table_content = inception.dash_board()
        # print html_table_content
        return render_template('index.html',html_table_content = html_table_content, username=session.get('username'))
    else:
        return redirect(url_for('login'))

#Inception_表结构评审
@app.route('/sql_audit',methods=['GET','POST'])
def inception_audit():
    form = InceptionAudit()
    sql_review = {}
    if session.get('username'):
        if request.method == "POST":
            db_select = request.values.get('db_select')
            sql_content = request.form.get('sql_content')
            is_execute = request.values.get('is_execute')
            sql_review = inception.audit(session.get('username'), db_select, sql_content, is_execute)
            return render_template('dba_tool/sql_audit.html',sql_review = sql_review, username=session.get('username'),abc = sql_content)
        return render_template('dba_tool/sql_audit.html',sql_review = sql_review, username=session.get('username'))
    else:
        return redirect(url_for('login'))

#列出某个DB的全部操作记录
@app.route('/more_operation')
def more_operation():
    if session.get('username'):
        bakdb = request.args.get('bakdb')
        html_table_content = inception.get_more_operation(bakdb)
        if html_table_content != None:
            return render_template('dba_tool/more_operation.html',html_table_content = html_table_content, username=session.get('username'))
        else:
            return render_template('dba_tool/more_operation.html',html_table_content = (((None,),),), username=session.get('username'))
    else:
        return redirect(url_for('login'))

#列出某个操作的详细信息
@app.route('/operation_detail')
def operation_detail():
    if session.get('username'):
        bakdb = request.args.get('bakdb')
        opid = request.args.get('opid')
        html_table_content = inception.get_operation_detail(bakdb, opid)
        if html_table_content != None:
            return render_template('dba_tool/operation_detail.html',html_table_content = html_table_content, username=session.get('username'))
        else:
            return render_template('dba_tool/operation_detail.html',html_table_content = (((None,),),), username=session.get('username'))
    else:
        return redirect(url_for('login'))