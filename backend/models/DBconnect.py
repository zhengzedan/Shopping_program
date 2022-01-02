from ctypes import resize
from os import P_DETACH
from flask import Flask, render_template, jsonify, json
from flask_sqlalchemy import SQLAlchemy
from flask import request
import pymysql
import hashlib

from pymysql import cursors
import logging

class Config(object):
    SQLALCHEMY_DATABASE_URI = "mysql://root:root@127.0.0.1:3306/Shopping_program"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# 日志文件
logger_sql = logging.getLogger('app.py')

logger_sql.setLevel(logging.INFO)

# 创建一个handler，用于写入日志文件
fh = logging.FileHandler('app.log')
fh.setLevel(logging.INFO)

# 定义handler的输出格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# 给logger添加handler
logger_sql.addHandler(fh)

class Product(db.Model):
    """商品信息表"""
    __tablename__ = "Product"
    p_id = db.Column(db.String(5), primary_key=True)
    name = db.Column(db.String(30))
    price = db.Column(db.Numeric(10,2))
    tag = db.Column(db.Integer)
    sold = db.Column(db.Integer)
    remain = db.Column(db.Integer)
    desc = db.Column(db.String(200))
    picture_path = db.Column(db.String(200))

class User(db.Model):
    """用户信息表"""
    __tablename__ = "User"
    u_id = db.Column(db.String(5), primary_key=True)
    u_pass=db.Column(db.String(500))
    u_name = db.Column(db.String(50))
    phone = db.Column(db.String(11))
    address = db.Column(db.String(500))
    money = db.Column(db.Numeric(10, 2))
    portrait_path = db.Column(db.String(500))

class Shopping_cart(db.Model):
    """购物车表"""
    __tablename__ = "Shopping_cart"
    u_id = db.Column(db.String(5), db.ForeignKey('User.u_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    p_id = db.Column(db.String(5), db.ForeignKey('Product.p_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    number = db.Column(db.Integer)

class Order_list(db.Model):
    """订单表"""
    __tablename__ = "Order_list"
    u_id = db.Column(db.String(5), db.ForeignKey('User.u_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    p_id = db.Column(db.String(5), db.ForeignKey('Product.p_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    number = db.Column(db.Integer)
    price = db.Column(db.Numeric(10, 2))

class Collect(db.Model):
    """收藏表""" 
    __tablename__ = "Collect"
    u_id = db.Column(db.String(5), db.ForeignKey('User.u_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    p_id = db.Column(db.String(5), db.ForeignKey('Product.p_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

class Comment(db.Model):
    """评论表"""
    __tablename__ = "Comment"
    u_id = db.Column(db.String(5), db.ForeignKey('User.u_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    p_id = db.Column(db.String(5), db.ForeignKey('Product.p_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    comment = db.Column(db.String(300))

class DBConnect:
    """
    数据库连接类
    初始化会连接数据库
    析构会关闭数据库连接
    """

    def __init__(self):
        """
        初始化数据库连接地址，连接数据库
        host='127.0.0.1',port=3306,user='root',password='root'
        """
        try:
            self.conn = pymysql.connect(
                host='127.0.0.1', port=3306, user='root', passwd='root', db='Shopping_program'
            )
            self.cur = self.conn.cursor()
        except :
            print('error')
    
    # 查询是否有某个用户存在
    def dbQuery_user_exist(self, u_id, u_pass):
        exist = 0
        cur = self.cur
        sql = "SELECT u_pass FROM user WHERE u_id=%s"
        cur.execute(sql, (u_id))
        self.conn.commit()
        result = cur.fetchall()

        logger_sql.info("SELECT u_pass FROM user WHERE u_id=%s"%(u_id))

        if len(result) == 0:
            exist = 0
        else:
            password = result[0][0]
            pass_encode = str(hashlib.md5(u_pass.encode('utf-8')).hexdigest())
            
            if pass_encode == password:
                exist = 1
            else:
                exist = -1
        return exist
    
    # 查询整个商品列表
    def dbQuery_product(self):
        cur = self.cur
        sql = "SELECT * FROM PRODUCT"
        cur.execute(sql)
        self.conn.commit()
        logger_sql.info("SELECT * FROM PRODUCT")
        result = cur.fetchall()
        product_list = []
        if len(result) != 0:
            for r in result:
                one_result = {
                    "p_id":r[0],
                    "name":r[1],
                    "price":r[2],
                    "tag":r[3],
                    "sold":r[4],
                    "remain":r[5],
                    "desc":r[6],
                    "picturePath":r[7]
                }
                product_list.append(one_result)
        return product_list

    # 查询某一个商品的详细信息
    def dbQuery_product_detail(self, p_id):
        cur = self.cur
        sql = "SELECT * FROM PRODUCT WHERE p_id = %s"
        cur.execute(sql, (p_id))
        self.conn.commit()
        logger_sql.info("SELECT * FROM PRODUCT WHERE p_id = %s"%(p_id))
        detail_list = cur.fetchall()
        detail = {
            "p_id": detail_list[0][0],
            "p_name": detail_list[0][1],
            "price": detail_list[0][2],
            "tag": detail_list[0][3],
            "sold": detail_list[0][4],
            "remain": detail_list[0][5],
            "desc": detail_list[0][6],
            "picture_path": detail_list[0][7]
        }
        return detail

    # 将商品加入购物车
    def dbAdd_shopping_cart(self, u_id, p_id, number):
        cur = self.cur
        sql = "SELECT * FROM shopping_cart WHERE u_id = %s AND p_id = %s"
        logger_sql.info("SELECT * FROM shopping_cart WHERE u_id = %s AND p_id = %s"%(u_id, p_id))
        cur.execute(sql, (u_id, p_id))
        self.conn.commit()
        result = cur.fetchall()
        if len(result) != 0:
            old_num = result[0][2]
            new_num = old_num + number
            sql = "UPDATE shopping_cart SET number = %s WHERE u_id = %s AND p_id = %s"
            logger_sql.info("UPDATE shopping_cart SET number = %s WHERE u_id = %s AND p_id = %s"%(str(new_num),u_id,p_id))
            cur.execute(sql, (str(new_num), u_id, p_id))
            self.conn.commit()
        else:
            # sql = "INSERT INTO shopping_cart VALUE(" + u_id + ", " + p_id + ", " + str(number) + ")"
            sql = "INSERT INTO shopping_cart VALUES(%s,%s,%s)"
            cur.execute(sql, (u_id, p_id, number))
            self.conn.commit()
            logger_sql.info("INSERT INTO shopping_cart VALUES(%s,%s,%s)"%(u_id, p_id,str(number)))
        return 1
    
    # 获取某一类商品
    def dbQuery_tag_product(self, tag):
        cur = self.cur
        sql = "SELECT * FROM PRODUCT WHERE tag = %s" 
        cur.execute(sql, (tag))
        result = cur.fetchall()
        self.conn.commit()
        logger_sql.info("SELECT * FROM PRODUCT WHERE tag = %s"%tag)
        tag_product_list = []
        if len(result) != 0 :
            for r in result:
                one_product = {
                    "p_id": r[0],
                    "p_name": r[1],
                    "price": r[2],
                    "tag": r[3],
                    "sold": r[4],
                    "remain": r[5],
                    "desc": r[6],
                    "picture": r[7]
                }
                tag_product_list.append(one_product)
        
        return tag_product_list

    # 获取某一用户的购物车
    def dbQuery_shopping_cart(self, u_id):
        cur = self.cur
        sql = "SELECT * FROM shopping_cart WHERE u_id = %s"
        cur.execute(sql, (u_id))
        self.conn.commit()
        logger_sql.info("SELECT * FROM shopping_cart WHERE u_id = %s"%u_id)
        result = cur.fetchall()
        shopping_cart_list = []
        if len(result) != 0:
            for r in result:
                shopping_cart_list.append(r)
        return shopping_cart_list

    # 获取购物车中某一商品的数量信息
    def dbQuery_shopping_cart_product_num(self, u_id, p_id):
        cur = self.cur
        sql = "SELECT number FROM shopping_cart WHERE u_id = %s AND p_id = %s"
        cur.execute(sql, (u_id, p_id))
        self.conn.commit()
        logger_sql.info("SELECT number FROM shopping_cart WHERE u_id = %s AND p_id = %s"%(u_id,p_id))
        result = cur.fetchall()
        if len(result) == 0:
            return 0
        number = result[0][0]

        return number

    
    # 获取某一商品的部分信息
    def dbQuery_product_name_price_pic(self, p_id):
        cur = self.cur
        sql = "SELECT name, price, picture_path FROM product WHERE p_id = %s"
        cur.execute(sql, (p_id))
        self.conn.commit()
        logger_sql.info("SELECT name, price, picture_path FROM product WHERE p_id = %s"%p_id)
        result = cur.fetchall()
        product_someinfo = []
        for r in result:
            product_someinfo.append(r)
        return product_someinfo

    # 购物车中商品数量+1
    def dbAdd_product_num(self, u_id, p_id):
        cur = self.cur
        sql = "SELECT * FROM shopping_cart WHERE u_id = %s AND p_id = %s"
        cur.execute(sql, (u_id, p_id))
        self.conn.commit()
        logger_sql.info("SELECT * FROM shopping_cart WHERE u_id = %s AND p_id = %s"%(u_id,p_id))
        result = cur.fetchall()
        if len(result) == 0:
            return 0
        sql = "UPDATE shopping_cart SET number = number + 1 WHERE u_id = %s AND p_id = %s"
        cur.execute(sql, (u_id, p_id))
        self.conn.commit()
        logger_sql.info("UPDATE shopping_cart SET number = number + 1 WHERE u_id = %s AND p_id = %s"%(u_id,p_id))
        return 1

    def dbSub_product_num(self, u_id, p_id):
        cur = self.cur
        sql = "SELECT number FROM shopping_cart WHERE u_id = %s AND p_id = %s"
        cur.execute(sql, (u_id, p_id))
        self.conn.commit()
        logger_sql.info("SELECT number FROM shopping_cart WHERE u_id = %s AND p_id = %s"%(u_id,p_id))
        result = cur.fetchall()
        if len(result) == 0:
            return 0
        number = result[0]
        if number == 1:
            sql = "DELETE FROM shopping_cart WHERE u_id = %s AND p_id = %s"
            logger_sql.info("DELETE FROM shopping_cart WHERE u_id = %s AND p_id = %s"%(u_id,p_id))
        else:
            sql = "UPDATE shopping_cart SET number = number - 1 WHERE u_id = %s AND p_id = %s"
            logger_sql.info("UPDATE shopping_cart SET number = number - 1 WHERE u_id = %s AND p_id = %s"%(u_id,p_id))
        cur.execute(sql, (u_id, p_id))
        self.conn.commit()
        
        return 1
    
    # 从购物车中删除某一个商品，并把它添加到订单中，再修改相关表
    def dbDelete_shoppingCart_add_order(self, u_id, p_id):
        cur = self.cur
        sql = "SELECT money FROM user WHERE u_id = %s"
        cur.execute(sql, (u_id))
        self.conn.commit()
        logger_sql.info("SELECT money FROM user WHERE u_id = %s"%u_id)
        result = cur.fetchall()
        money = result[0][0]
        sql = "SELECT number FROM shopping_cart WHERE u_id = %s AND p_id = %s"
        cur.execute(sql, (u_id, p_id))
        self.conn.commit()
        logger_sql.info("SELECT number FROM shopping_cart WHERE u_id = %s AND p_id = %s"%(u_id,p_id))
        result = cur.fetchall()
        number = result[0][0]
        sql = "SELECT price FROM product WHERE p_id = %s"
        cur.execute(sql, (p_id))
        self.conn.commit()
        logger_sql.info("SELECT price FROM product WHERE p_id = %s"%p_id)
        result = cur.fetchall()
        price = result[0][0]
        if money < number * price:
            return 0
        sql = "DELETE FROM shopping_cart WHERE u_id = %s AND p_id = %s"
        cur.execute(sql, (u_id, p_id))
        self.conn.commit()
        logger_sql.info("DELETE FROM shopping_cart WHERE u_id = %s AND p_id = %s"%(u_id,p_id))
        sql = "UPDATE user SET money = money - %s where u_id = %s"
        cur.execute(sql, (str(number*price), u_id))
        self.conn.commit()
        logger_sql.info("UPDATE user SET money = money - %s where u_id = %s"%(str(number*price), u_id))
        sql = "UPDATE product SET sold = sold + %s,remain = remain - %s where p_id = %s"
        cur.execute(sql, (str(number), str(number), p_id))
        self.conn.commit()
        logger_sql.info("UPDATE product SET sold = sold + %s,remain = remain - %s where p_id = %s"%(str(number), str(number), p_id))
        sql = "SELECT remain FROM product WHERE p_id=%s"
        logger_sql.info("SELECT remain FROM product WHERE p_id=%s"%(p_id))
        cur.execute(sql, (p_id))
        self.conn.commit()
        result = cur.fetchall()
        if result[0] == 0:
            sql = "DELETE FROM product WHERE p_id=%s"
            logger_sql.info("DELETE FROM product WHERE p_id=%s"%(p_id))
            cur.execute(sql, (p_id))
            self.conn.commit()
        sql = "SELECT * FROM order_list where u_id=%s AND p_id = %s"
        cur.execute(sql, (u_id, p_id))
        self.conn.commit()
        logger_sql.info("SELECT * FROM order_list where u_id=%s AND p_id = %s"%(u_id, p_id))
        result = cur.fetchall()
        if len(result) != 0:
            sql = "UPDATE order_list SET number = number + %s WHERE u_id=%s AND p_id=%s"
            # sql = "INSERT INTO user VALUES(%s,%s,%s,%s,%s,%s,%s)"
            cur.execute(sql, (str(number), u_id, p_id))
            self.conn.commit()
            logger_sql.info("UPDATE order_list SET number = number + %s WHERE u_id=%s AND p_id=%s"%(str(number), u_id, p_id))
        else:
            sql = "INSERT INTO order_list VALUES(%s,%s,%s,%s)"
            # sql = "INSERT INTO user VALUES(%s,%s,%s,%s,%s,%s,%s)"
            cur.execute(sql, (u_id, p_id, str(number), str(price*number)))
            self.conn.commit()
            logger_sql.info("INSERT INTO order_list VALUES(%s,%s,%s,%s)"%(u_id, p_id, str(number), str(price * number)))
        return 1
    
    # 获取某个用户的详细信息
    def dbQuery_user_info(self, u_id):
        cur = self.cur
        sql = "SELECT * FROM user WHERE u_id = %s"
        cur.execute(sql, (u_id))
        self.conn.commit()
        logger_sql.info("SELECT * FROM user WHERE u_id = %s"%u_id)
        result = cur.fetchall()
        user_info = {
            "u_id": result[0][0],
            "u_pass": result[0][1],
            "u_name": result[0][2],
            "phone": result[0][3],
            "address": result[0][4],
            "money": result[0][5],
            "portrait_path": result[0][6]
        }
        return user_info
    
    # 获取某个用户的收藏列表
    def dbQuery_collect_list(self, u_id):
        cur = self.cur
        sql = "SELECT * FROM collect WHERE u_id = %s"
        cur.execute(sql, (u_id))
        self.conn.commit()
        logger_sql.info("SELECT * FROM collect WHERE u_id = %s"%u_id)
        result = cur.fetchall()
        collect_list = []
        if len(result) != 0:
            for r in result:
                one_collect = {
                    "u_id": r[0],
                    "p_id": r[1]
                }
                collect_list.append(one_collect)
        return collect_list

    # 增加某个商品到某个用户的收藏列表中
    def dbAdd_collect(self, u_id, p_id):
        cur = self.cur
        sql = "INSERT INTO collect VALUES(%s, %s)"
        cur.execute(sql, (u_id, p_id))
        self.conn.commit()
        logger_sql.info("INSERT INTO collect VALUES(%s, %s)"%(u_id, p_id))
        return 

    # 删除某个用户的收藏列表中的某个商品
    def dbSub_collect(self, u_id, p_id):
        cur = self.cur
        sql = "DELETE FROM collect WHERE u_id=%s and p_id=%s"
        cur.execute(sql, (u_id, p_id))
        self.conn.commit()
        logger_sql.info("DELETE FROM collect WHERE u_id=%s and p_id=%s"%(u_id, p_id))
        return 

    # 查询某一商品是否在收藏夹 
    def dbQuery_collect_exist(self, u_id, p_id):
        cur = self.cur
        sql = "SELECT * FROM collect WHERE u_id=%s AND p_id=%s"
        logger_sql.info("SELECT * FROM collect WHERE u_id=%s AND p_id=%s"%(u_id,p_id))
        cur.execute(sql, (u_id,p_id))
        self.conn.commit()
        result = cur.fetchall()
        if len(result) != 0:
            is_success = 1
        else:
            is_success = 0
        return is_success

    # 注册用户
    def dbAdd_user(self, u_id, u_pass, u_name, phone, address, money, portrait):
        cur = self.cur
        sql = "SELECT * FROM user WHERE u_id = %s"
        cur.execute(sql, (u_id))
        self.conn.commit()
        logger_sql.info("SELECT * FROM user WHERE u_id = %s"%u_id)
        result = cur.fetchall()
        is_success = 1
        if len(result) != 0:
            is_success = 0
        else:
            pass_encode = hashlib.md5(u_pass.encode('utf-8')).hexdigest()
            test = str(pass_encode)
            # sql = "INSERT INTO user VALUES(" + u_id + ",'" + test + "','" + u_name + "', '" + phone + "', '" + address + "', '" + str(money) + "', '" + portrait + "')"
            sql = "INSERT INTO user VALUES(%s,%s,%s,%s,%s,%s,%s)"
            cur.execute(sql, (u_id, str(pass_encode), u_name, phone, address, money, portrait))
            self.conn.commit()
            logger_sql.info("INSERT INTO user VALUES(%s,%s,%s,%s,%s,%s,%s)"%(u_id, str(pass_encode), u_name, phone, address, money, portrait))
        return is_success

    # 添加商品
    def dbAdd_product(self, p_id, p_name, price, tag, sold, remain, desc, picture):
        cur = self.cur
        sql = "SELECT * FROM product WHERE p_id = %s"
        cur.execute(sql, (p_id))
        self.conn.commit()
        logger_sql.info("SELECT * FROM product WHERE p_id = %s"%p_id)
        result = cur.fetchall()
        is_success = 1
        if len(result) != 0:
            is_success = 0
        else:
            # sql = "INSERT INTO product VALUE(" + p_id + ", " + p_name + ", " + p_name + ", " + price + ", " + str(tag) + ", " + str(sold) + ", " + str(remain) + ", " + desc + picture
            # print("type:", type(p_id), type(p_name), type(price), type(tag), type(sold), type(remain), type(desc), type(picture))
            sql = "INSERT INTO product VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
            cur.execute(sql, (p_id, p_name, price, tag, sold, remain, desc, picture))
            self.conn.commit()
            logger_sql.info("INSERT INTO product VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"%(p_id, p_name, price, tag, sold, remain, desc, picture))
        return is_success

    def dbDel_product(self, u_id, p_id):
        cur = self.cur
        sql = "DELETE FROM shopping_cart WHERE u_id = %s AND p_id = %s"
        cur.execute(sql, (u_id, p_id))
        self.conn.commit()
        result = cur.fetchall()
        logger_sql.info("DELETE FROM shopping_cart WHERE u_id = %s AND p_id = %s"%(u_id,p_id))

        return 1

    def dbQuery_order_list(self, u_id):
        cur = self.cur
        sql = "SELECT * FROM order_list WHERE u_id = %s"
        logger_sql.info("SELECT * FROM order_list WHERE u_id = %s"%(u_id))
        cur.execute(sql, (u_id))
        self.conn.commit()
        result = cur.fetchall()

        return result

    def dbUpdate_user(self, u_id, phone, address):
        cur = self.cur
        sql = "UPDATE user SET phone=%s, address=%s WHERE u_id=%s"
        logger_sql.info("UPDATE user SET phone=%s, address=%s WHERE u_id=%s"%(phone, address, u_id))
        cur.execute(sql, (phone, address, u_id))
        self.conn.commit()
        result = cur.fetchall()

        return 1

    def dbTry_del_cart(self, u_id, p_list):
        cur = self.cur
        for p_id in p_list:
            sql = "SELECT * FROM shopping_cart WHERE u_id=%s AND p_id=%s"
            logger_sql.info("SELECT * FROM shopping_cart WHERE u_id=%s AND p_id=%s"%(u_id, p_id))
            cur.execute(sql, (u_id, p_id))
            self.conn.commit()
            result = cur.fetchall()
            if len(result) != 0:
                sql = "INSERT INTO order_list VALUES()"
                sql = "DELETE FROM shopping_cart WHERE u_id=%s AND p_id=%s"
                logger_sql.info(("DELETE FROM shopping_cart WHERE u_id=%s AND p_id=%s"%(u_id, p_id)))
                cur.execute(sql, (u_id, p_id))
                self.conn.commit()
        return 
    
    def dbDelete_order_list(self, u_id, p_list):
        cur = self.cur
        for p_id in p_list:
            sql = "DELETE FROM order_list WHERE u_id=%s AND p_id=%s"
            logger_sql.info("DELETE FROM order_list WHERE u_id=%s AND p_id=%s"%(u_id, p_id))
            cur.execute(sql, (u_id, p_id))
            self.conn.commit()
        return 
        
if __name__=="__main__":
    db.create_all() 