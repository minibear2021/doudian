# -*- coding: utf-8 -*-
import json
import logging
import os
from random import sample
from string import digits, ascii_letters
from time import time

from flask import Flask, jsonify, request

from doudian import DouDian, AppType

# App类型，SELF=自用型应用, TOOL=工具型应用
APP_TYPE = AppType.SELF

# 应用key，长度19位数字字符串
APP_KEY = '3409409348479354011'

# 应用密钥 字符串
APP_SECRET = '2ad2355c-01d0-11f8-91dc-05a8cd1054b1'

# 店铺ID，仅自用型应用需要
SHOP_ID = '323423'

# token缓存文件
TOKEN_FILE = './token'

# 日志记录器，记录API请求和推送消息细节
logging.basicConfig(filename=os.path.join(os.getcwd(), 'demo.log'), level=logging.DEBUG, filemode='a', format='%(asctime)s - %(process)s - %(levelname)s: %(message)s')
LOGGER = logging.getLogger("demo")

# 代理设置，None或者{"https": "http://10.10.1.10:1080"}，详细格式参见https://docs.python-requests.org/zh_CN/latest/user/advanced.html
PROXY = None

# 初始化
doudian = DouDian(
    app_key=APP_KEY,
    app_secret=APP_SECRET,
    app_type=APP_TYPE,
    shop_id=SHOP_ID,
    token_file=TOKEN_FILE,
    logger=LOGGER,
    proxy=PROXY
)

app = Flask(__name__)


@app.route('/orderList')
def order_list():
    # 以会员订单列表查询为例，参照官方文档，将path、method、params三个参数拼凑好传入request接口，调用成功后即可获取会员订单数据。
    # https://op.jinritemai.com/docs/api-docs/13/366
    path = '/member/searchList'
    method = 'member.searchList'
    params = {}
    params.update({'start_time': '2021/10/12 00:00:00'})
    params.update({'end_time': '2021/10/12 00:00:00'})
    result = doudian.request(path=path, method=method, params=params)
    if result and result.get('err_no') == 0:
        return jsonify({'data': result.get('data')})
    else:
        return jsonify({'data': ''})


@app.route('/notify', methods=['POST'])
def notify():
    # 解析处理消息推送服务
    # https://op.jinritemai.com/docs/guide-docs/153/99
    result = doudian.callback(request.headers, request.data)
    if result:
        tag = result.get('tag')
        if tag == '0':  # 抖店推送服务验证消息，需立即返回success
            return jsonify({'code': 0, 'msg': 'success'})
        if tag == '100':  # 订单创建消息，更多消息类型查阅官方文档。
            # TODO: 根据推送的消息参数进行必要的业务处理，5秒内返回success
            return jsonify({'code': 0, 'msg': 'success'})
        return jsonify({'code': 0, 'msg': 'success'})
    else:
        return jsonify({'code': 40041, 'message': '解析推送数据失败'})


@app.route('/authUrl')
def authUrl():
    # 工具型应用生成授权url供商户进行授权操作
    # https://op.jinritemai.com/docs/guide-docs/9/22
    service_id = 'demo service id'
    state = 'demo state'
    result = doudian.build_auth_url(service_id=service_id, state=state)
    if result:
        return jsonify({'code': 0, 'msg': result})
    else:
        return jsonify({'data': -1, 'msg': '生成授权url失败'})


if __name__ == '__main__':
    app.run()
