from flask_cors.core import FLASK_CORS_EVALUATED
import models.DBconnect as DBConnect
import datetime
import os
import sys


class Control:
    """
    控制层，承上启下
    对基本的数据库底层代码进行调用，并进行一系列的逻辑处理，并且把结果返回给API层
    """

    def isExist(self, u_id, u_pass):
        """
        登录时，判断用户是否存在
        若存在登录密码是否正确
        由于数据库中存储的是加密后的密码，所以要先对传入的密码做md5加密
        """
        db = DBConnect.DBConnect()
        is_exist = db.dbQuery_user_exist(u_id, u_pass)

        if is_exist == 0:
            dic = {
                "returnCode": "f0",
                "returnMessage": "User doesn't exist",
            }
        elif is_exist == -1:
            dic = {
                "returnCode": "f1",
                "returnMessage": "Password is wrong",
            }
        elif is_exist == 1:
            dic = {
                "returnCode": "s",
                "returnMessage": "Login success",
            }
        print(dic)
        return dic
    
    def getProductList(self):
        """
        首页获取所有商品信息
        """
        db = DBConnect.DBConnect()
        all_product_list = db.dbQuery_product()
        return all_product_list
    
    def getProductDetail(self, u_id, p_id):
        db = DBConnect.DBConnect()
        detail = db.dbQuery_product_detail(p_id)
        # 补充查询收藏夹
        if u_id != '':
            is_collected = db.dbQuery_collect_exist(u_id, p_id)
        if is_collected:
            detail['is_collected'] = True
        else:
            detail['is_collected'] = False
        return detail

    def addShoppingCart(self, u_id, p_id, number):
        """将商品加入购物车"""
        db = DBConnect.DBConnect()
        db.dbAdd_shopping_cart(u_id, p_id, number)
        return 
    
    def getTagProduct(self, tag):
        """获取某一类别的商品列表"""
        db = DBConnect.DBConnect()
        tag_product_list = db.dbQuery_tag_product(tag)
        return tag_product_list

    def getShoppingCart(self, u_id):
        """获取某一用户的购物车"""
        db = DBConnect.DBConnect()
        shopping_cart_list = db.dbQuery_shopping_cart(u_id)
        shopping_list = []
        for record in shopping_cart_list:
            p_id = record[1]
            number = record[2]
            some_info = db.dbQuery_product_name_price_pic(p_id)[0]
            p_name = some_info[0]
            price = some_info[1]
            picture = some_info[2]
            recood = {
                "p_id": p_id,
                "p_name": p_name,
                "number": number,
                "price": price,
                "picture": picture,
            }
            shopping_list.append(recood)
        
        return shopping_list

    def addProductNum(self, u_id, p_id):
        """用户购物车中的某个商品数量增加1"""
        db = DBConnect.DBConnect()
        if_success = db.dbAdd_product_num(u_id, p_id)
        return if_success

    def subProductNum(self, u_id, p_id):
        """用户购物车中的某个商品数量减1"""
        db = DBConnect.DBConnect()
        if_success = db.dbSub_product_num(u_id, p_id)
        return if_success
    
    # def pay(self, u_id, p_list):
    #     """付款"""
    #     db = DBConnect.DBConnect()
    #     is_success = 1
    #     total_price = 0
    #     # 先查询购物车中的数量，再查询商品列表中的单价，相乘得到每个商品的总价
    #     for p_id in p_list:
    #         number = db.dbQuery_shopping_cart_product_num(u_id, p_id)
    #         detail = db.dbQuery_product_detail(p_id)
    #         one_price = detail["price"]
    #         # 再把所有商品的总价加起来
    #         total_price += number * one_price
        
    #     # 再查询user表中用户的余额
    #     user_info = db.dbQuery_user_info(u_id)
    #     left_money = user_info["money"]

    #     # 如果余额小于商品总价，则付款不成功，返回0，不写入order_list数据库
    #     if left_money < total_price:
    #         is_success = 0
    #         return is_success

    #     for p_id in p_list:
    #         is_success = db.dbDelete_shoppingCart_add_order(u_id, p_id)
    #         if is_success == 0:
    #             return 0
    #     return  1

    def pay(self, u_id, p_list):
        db = DBConnect.DBConnect()
        db.dbDelete_order_list(u_id, p_list)


    def getUserInfo(self, u_id):
        """获取某个用户的详细信息"""
        db = DBConnect.DBConnect()
        user_info = db.dbQuery_user_info(u_id)
        return user_info

    def getCollectList(self, u_id):
        """获取某个用户的收藏列表"""
        db = DBConnect.DBConnect()
        collect = []
        collect_list = db.dbQuery_collect_list(u_id)
        # 根据p_id获取每个商品的详细信息
        for one_collect in collect_list:
            one_pid = one_collect['p_id']
            one_product = db.dbQuery_product_detail(one_pid)
            collect.append(one_product)
        return collect

    def addCollect(self, u_id, p_id):
        """添加某个商品到某个用户的收藏列表"""
        db = DBConnect.DBConnect()
        db.dbAdd_collect(u_id, p_id)
    
    def subCollect(self, u_id, p_id):
        """删除某个用户的收藏列表中的某个商品"""
        db = DBConnect.DBConnect()
        db.dbSub_collect(u_id, p_id)

    def delCartAddOrder(self, u_id, p_list):
        db = DBConnect.DBConnect()
        total_price = 0
        for p_id in p_list:
            db.dbDelete_shoppingCart_add_order(u_id, p_id)
    
    def getOrderList(self, u_id):
        """获取订单列表"""
        db = DBConnect.DBConnect()
        order_list = db.dbQuery_order_list(u_id)
        order_detail_list = []
        for order in order_list:
            p_id = order[1]
            number = order[2]
            one_price = order[3]
            some_info = db.dbQuery_product_name_price_pic(p_id)[0]
            p_name = some_info[0]
            price = some_info[1]
            picture = some_info[2]
            
            one_order = {
                "u_id": u_id,
                "p_id": p_id,
                "p_name":p_name,
                "number": number,
                "price": float(one_price),
                "picture":picture
            }
            order_detail_list.append(one_order)

        return order_detail_list

    def register(self, u_id, u_pass, u_name, phone, address, money, portrait):
        """注册用户"""
        db = DBConnect.DBConnect()
        is_success = db.dbAdd_user(u_id, u_pass, u_name, phone, address, money, portrait)
        return is_success    

    def addProduct(self, p_id, p_name, price, tag, sold, remain, desc, picture):
        """添加商品"""
        db = DBConnect.DBConnect()
        is_success = db.dbAdd_product(p_id, p_name, price, tag, sold, remain, desc, picture)
        return is_success

    def delProduct(self, u_id, p_id):
        """删除商品"""
        db = DBConnect.DBConnect()
        is_success = db.dbDel_product(u_id, p_id)
        return is_success

    def changeAddress(self, u_id, phone, address):
        """修改用户地址"""
        db = DBConnect.DBConnect()
        is_success = db.dbUpdate_user(u_id, phone, address)
        return is_success

    def getTryOrder(self, u_id, p_list):
        db = DBConnect.DBConnect()
        try_order = []
        for p_id in p_list:
            # 先查询购物车表，找出商品的数量
            number = db.dbQuery_shopping_cart_product_num(u_id,p_id)
            # 再查询商品表，找出商品的单价
            detail = db.dbQuery_product_detail(p_id)
            one_price = float(detail["price"])
            one_order = {
                "u_id": u_id,
                "p_id": p_id,
                "number": number,
                "price": one_price
            }
            try_order.append(one_order)
        return try_order