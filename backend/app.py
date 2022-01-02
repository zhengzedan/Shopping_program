from itertools import product
from logging import debug
from flask import Flask
from flask import request
from flask import jsonify
from flask import session
from flask import redirect
from flask import url_for
from flask_cors import CORS

import controller.control as Control
import os
import sys
import json
import random

import Log.logutil2 as log
import logging

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config['JSON_SORT_KEYS'] = False

# session
# 随机生成SECRET_KEY
app.config['SECRET_KEY'] = os.urandom(24)

# 启动日志服务
logger = log.logs()

@app.route('/login', methods=['GET'])
def Login():
    """
    登录，验证传入的用户名和密码是否在数据库中匹配
    API: http://localhost/login

    Args: 
    u_id -- 用户id
    u_pass -- 登录密码 

    Returns：
        返回是否登录成功   
    """

    # 获取用户名和登录密码
    user_id = str(request.args.get('u_id'))
    user_pass = str(request.args.get('u_pass'))

    control = Control.Control()
    return_dic = control.isExist(user_id, user_pass)
    
    # 找不到用户
    if return_dic['returnCode'] == 'f0':
        return jsonify({
            "error_code": 501,
            "error_info": return_dic['returnMessage'],
        })
    elif return_dic['returnCode'] == 'f1':
        return jsonify({
            "error_code": 502,
            "error_info": return_dic['returnMessage']
        })
    elif return_dic['returnCode'] == 's':
        return jsonify({
            "success_code": 200,
            "success_info": return_dic['returnMessage'],
        })
    else :
        return jsonify({
            "error_code": 503,
            "error_info": "Other errors",
        })

@app.route('/', methods=['GET'])
def GetProductList():
    """
    首页，获取所有商品信息列表
    由于这只是一个模拟，存储的数据元组比较少，所以直接返回所有商品信息
    如果数据库数据规模比较大的话，可以只返回一部分
    """
    control = Control.Control()
    product_list = control.getProductList()
    return jsonify({
        "success_code": 200,
        "success_info": "Get product sucess",
        "product_list": product_list,
    })

@app.route('/home', methods=['GET'])
def GetProductListHome():
    """
    首页，获取所有商品信息列表
    由于这只是一个模拟，存储的数据元组比较少，所以直接返回所有商品信息
    如果数据库数据规模比较大的话，可以只返回一部分
    """
    control = Control.Control()
    product_list = control.getProductList()
    return jsonify({
        "success_code": 200,
        "success_info": "Get product sucess",
        "product_list": product_list,
    })

@app.route('/getDetail', methods=['GET'])
def GetProductDetail():
    product_id = str(request.args.get('p_id'))
    u_id = str(request.args.get('u_id'))
    control = Control.Control()
    detail_info = control.getProductDetail(u_id, product_id)
    return jsonify({
        "success_code": 200,
        "detail": detail_info,
    })

@app.route('/addShoppingCart', methods=['POST'])
def AddShoppingCart():
    user_id = str(request.json.get('u_id'))
    product_id = str(request.json.get('p_id'))
    number = int(request.json.get('number'))
    control = Control.Control()
    control.addShoppingCart(user_id, product_id, number)
    return jsonify({
        "success_code": 200, 
        "success_info": "Add success",
    })

@app.route('/division', methods=['GET'])
def Division():
    tag = int(request.args.get('tag'))
    control = Control.Control()
    tag_product_list = control.getTagProduct(tag)
    return jsonify({
        "success_code": 200,
        "success_info": "Get tag product success",
        "tag_product_list": tag_product_list,
    })

@app.route('/shoppingCart', methods=['GET'])
def ShoppingCart():
    user_id = str(request.args.get('u_id'))
    control = Control.Control()
    shopping_cart_list = control.getShoppingCart(user_id)
    return jsonify({
        "success_code": 200,
        "shopping_cart_list": shopping_cart_list,
    })

@app.route('/addProductNum', methods=['PUT'])
def AddProductNum():
    user_id = str(request.json.get('u_id'))
    product_id = str(request.json.get('p_id'))
    control = Control.Control()
    if_success = control.addProductNum(user_id, product_id)
    if if_success:
        return jsonify({
            "success_code": 200,
            "success_info": "Add success",
        })
    else:
        return jsonify({
            "error_code": 504,
            "error_info": "Can't find record in shopping cart"
        })

@app.route('/subProductNum', methods=['PUT'])
def SubProductNum():
    user_id = str(request.json.get('u_id'))
    product_id = str(request.json.get('p_id'))
    control = Control.Control()
    if_success = control.subProductNum(user_id, product_id)
    if if_success:
        return jsonify({
            "success_code": 200,
            "success_info": "Sub success",
        })
    else:
        return jsonify({
            "error_code": 504,
            "error_info": "Can't find record in shopping cart"
        })

@app.route('/delProduct', methods=['DELETE'])
def DelProduct():
    user_id = str(request.json.get('u_id'))
    product_id = str(request.json.get('p_id'))
    control = Control.Control()
    is_success = control.delProduct(user_id, product_id)
    if is_success:
        return jsonify({
            "success_code": 200,
            "success_info": "Delete success",
        })
    else:
        return jsonify({
            "error_code": 509,
            "error_info": "Delete failed",
        })

@app.route('/pay', methods=['POST'])
def Pay():
    u_id = str(request.json.get('u_id'))
    p_list = list(request.json.get('product_list'))
    control = Control.Control()
    is_success = control.pay(u_id, p_list)
    if is_success :
        return jsonify({
            "success_code": 200,
            "success_info": "Pay success",
        })
    else:
        return jsonify({
            "error_code": 505,
            "error_info": "Money is not enough",
        })

@app.route('/getInfo', methods=['GET'])
def GetUserInfo():
    u_id = str(request.args.get('u_id'))
    control = Control.Control()

    user_info = control.getUserInfo(u_id)

    if len(user_info) == 0:
        return jsonify({
            "error_code": 506,
            "error_info": "User doesn't exist",
            "user_info": user_info,
        })
    else:
        return jsonify({
            "success_code": 200,
            "success_info": "Get success",
            "user_info": user_info
        })

@app.route('/collect', methods=['GET'])
def GetCollectList():
    u_id = str(request.args.get('u_id'))
    control = Control.Control()
    collect_list = control.getCollectList(u_id)
    return jsonify({
        "success_code": 200,
        "success_info": "Get success",
        "collect_list": collect_list,
    })

@app.route('/addCollect', methods=['POST'])
def AddCollect():
    u_id = str(request.json.get('u_id'))
    p_id = str(request.json.get('p_id'))
    control = Control.Control()
    control.addCollect(u_id, p_id)
    return jsonify({
        "success_code": 200,
        "success_info": "Add success",
    })

@app.route('/subCollect', methods=['DELETE'])
def SubCollect():
    u_id = str(request.json.get('u_id'))
    p_id = str(request.json.get('p_id'))
    control = Control.Control()
    control.subCollect(u_id, p_id)
    return jsonify({
        "success_code": 200,
        "success_info": "Sub success",
    })

@app.route('/register', methods=['POST'])
def Register():
    u_id = str(request.json.get('u_id'))
    u_pass = str(request.json.get('u_pass'))
    u_name = str(request.json.get('u_name'))
    phone = str(request.json.get('phone'))
    address = str(request.json.get('address'))
    money = 1000
    portrait_path = request.json.get('portrait_path')

    control = Control.Control()
    is_success = control.register(u_id, u_pass, u_name, phone, address, money, portrait_path)
    if is_success:
        return jsonify({
            "success_code": 200,
            "success_info": "Register success",
        })
    else:
        return jsonify({
            "error_code": 507,
            "error_info": "User already exists",
        })

@app.route('/addProduct', methods=['POST'])
def AddProduct():
    p_id = str(request.json.get('p_id'))
    p_name = str(request.json.get('p_name'))
    price = float(request.json.get('price'))
    tag = int(request.json.get('tag'))
    sold = int(request.json.get('sold'))
    remain = int(request.json.get('remain'))
    desc = str(request.json.get('desc'))
    picture_path = str(request.json.get('picture_path'))

    control = Control.Control()
    is_success = control.addProduct(p_id, p_name, price, tag, sold, remain, desc, picture_path)
    if is_success:
        return jsonify({
            "success_code": 200,
            "success_info": "Add success",
        })
    else:
        return jsonify({
            "error_code": 508,
            "error_info": "Product already exists",
        })

@app.route('/getOrderList', methods=['POST'])
def GetTryOrder():
    u_id = str(request.json.get('u_id'))
    p_list = list(request.json.get('product_list'))
    from_cart = int(request.json.get('from_cart'))
    
    control = Control.Control()
    if from_cart == 1:
        control.delCartAddOrder(u_id, p_list)
    order_list = control.getOrderList(u_id)
    return jsonify({
        "success_code":200,
        "success_info": "Get try order_list success",
        "order_list": order_list
    })

@app.route('/changeAddress', methods=['POST'])
def ChangeAddress():
    u_id = str(request.json.get('u_id'))
    phone = str(request.json.get('phone'))
    address = str(request.json.get('address'))

    control = Control.Control()
    is_success = control.changeAddress(u_id, phone, address)

    if is_success:
        return jsonify({
            "success_code": 200,
            "success_info": "Change address success",
        })
    else:
        return jsonify({
            "error_code": 510,
            "error_info": "Change address falied",
        })


if __name__=="__main__":
    # init_server()
    app.run(debug=True, host='127.0.0.1', port=8000)