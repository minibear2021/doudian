# -*- coding: utf-8 -*-
import json
import time
from datetime import datetime
from logging import Logger

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.hashes import MD5, SHA256, Hash
from cryptography.hazmat.primitives.hmac import HMAC

from .exception import CodeError, ShopIdError, TokenError
from .type import AppType


class DouDian():
    def __init__(self, app_key: str, app_secret: str, app_type: AppType = AppType.SELF, code=None, shop_id: str = None, token_file: str = None, logger: Logger = None, proxy: str = None, test_mode=False):
        """初始化DouDian实例，自用型应用传入shop_id用于初始化access token，工具型应用传入code换取access token（如初始化时未传入，可以在访问抖店API之前调用init_token(code)进行token的初始化。
        """
        self._app_key = app_key
        self._app_secret = app_secret
        self._app_type = app_type
        self._token_file = token_file
        self._logger = logger
        if self._app_type == AppType.SELF and not shop_id:
            if self._logger:
                self._logger.exception('shop_id is not assigned.')
            raise ShopIdError('shop_id is not assigned.')
        self._shop_id = shop_id
        self._proxy = proxy
        self._test_mode = test_mode
        if self._test_mode:
            self._gate_way = 'https://openapi-sandbox.jinritemai.com'
        else:
            self._gate_way = 'https://openapi-fxg.jinritemai.com'
        self._version = 2
        self._token = None
        self._sign_method = 'hmac-sha256'
        if self._token_file:
            try:
                with open(self._token_file) as f:
                    self._token = json.load(f)
            except Exception as e:
                if self._logger:
                    self._logger.exception('{}'.format(e))
        if self._app_type == AppType.SELF:
            self.init_token()
        elif self._app_type == AppType.TOOL and code:
            self.init_token(code)

    def _sign(self, method: str, param_json: str, timestamp: str) -> str:
        param_pattern = 'app_key{}method{}param_json{}timestamp{}v{}'.format(self._app_key, method, param_json, timestamp, self._version)
        sign_pattern = '{}{}{}'.format(self._app_secret, param_pattern, self._app_secret)
        return self._hash_hmac(sign_pattern)

    def _hash_hmac(self, pattern: str) -> str:
        try:
            hmac = HMAC(key=self._app_secret.encode('UTF-8'), algorithm=SHA256(), backend=default_backend())
            hmac.update(pattern.encode('UTF-8'))
            signature = hmac.finalize()
            return signature.hex()
        except Exception as e:
            if self._logger:
                self._logger.exception('{}'.format(e))
            return None

    def _access_token(self) -> str:
        if not self._token:
            if self._logger:
                self._logger.exception('no token info, call init_token() to initialize it.')
            raise TokenError('no token info, call init_token() to initialize it.')
        try:
            if self._token.get('expires_in') - int(time.time()) < 3000:
                self._refresh_token()
            return self._token.get('access_token')
        except Exception as e:
            if self._logger:
                self._logger.exception('{}'.format(e))
            return None

    def init_token(self, code: str = '') -> bool:
        """初始化access token
        :param code: 工具型应用从授权url回调中获取到的code，自用型应用无需传入。
        """
        if self._app_type == AppType.TOOL and not code:
            if self._logger:
                self._logger.exception('code is not assigned.')
            raise CodeError('code is not assigned.')
        path = '/token/create'
        grant_type = 'authorization_self' if self._app_type == AppType.SELF else 'authorization_code'
        params = {}
        params.update({'code': code if code else ''})
        params.update({'grant_type': grant_type})
        if self._app_type == AppType.SELF:
            if self._test_mode:
                params.update({'test_shop': '1'})
            elif self._shop_id:
                params.update({'shop_id': self._shop_id})
            else:
                if self._logger:
                    self._logger.exception('shop_id is not assigned.')
                raise ShopIdError('shop_id is not assigned.')
        result = self._request(path=path, params=params, token_request=True)
        if result and result.get('err_no') == 0 and result.get('data'):
            self._token = result.get('data')
            self._token.update({'expires_in': int(time.time()) + result.get('data').get('expires_in')})
            if self._token_file:
                with open(self._token_file, mode='w') as f:
                    f.write(json.dumps(self._token))
            return True
        return False

    def _get_refresh_token(self) -> str:
        if not self._token:
            return None
        try:
            return self._token.get('refresh_token')
        except Exception as e:
            if self._logger:
                self._logger.exception('{}'.format(e))
            return None

    def _refresh_token(self) -> None:
        path = '/token/refresh'
        refresh_token = self._get_refresh_token()
        grant_type = 'refresh_token'
        params = {}
        params.update({'grant_type': grant_type})
        params.update({'refresh_token': refresh_token})
        result = self._request(path=path, params=params, token_request=True)
        if result and result.get('err_no') == 0 and result.get('data'):
            self._token = result.get('data')
            self._token.update({'expires_in': int(time.time()) + result.get('data').get('expires_in')})
            if self._token_file:
                with open(self._token_file, mode='w') as f:
                    f.write(json.dumps(self._token))

    def _request(self, path: str, params: dict, token_request: bool = False) -> json:
        try:
            headers = {}
            headers.update({'Content-Type': 'application/json'})
            headers.update({'Accept': 'application/json'})
            headers.update({'User-Agent': 'doudian python sdk(https://github.com/minibear2021/doudian)'})
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            param_json = json.dumps(params, sort_keys=True, separators=(',', ':'))
            method = path[1:].replace('/', '.')
            sign = self._sign(method=method, param_json=param_json, timestamp=timestamp)
            if token_request:
                url = self._gate_way + '{}?app_key={}&method={}&param_json={}&timestamp={}&v={}&sign_method={}&sign={}'.format(
                    path, self._app_key, method, param_json, timestamp, self._version, self._sign_method, sign)
            else:
                access_token = self._access_token()
                url = self._gate_way + '{}?app_key={}&method={}&access_token={}&timestamp={}&v={}&sign_method={}&sign={}'.format(
                    path, self._app_key, method, access_token, timestamp, self._version, self._sign_method, sign)
            if self._logger:
                self._logger.debug('Request url: {}'.format(url))
                self._logger.debug('Request headers: {}'.format(headers))
                self._logger.debug('Request params: {}'.format(param_json))
            response = requests.post(url=url, data=param_json, headers=headers, proxies=self._proxy)
            if self._logger:
                self._logger.debug('Response status code: {}'.format(response.status_code))
                self._logger.debug('Response headers: {}'.format(response.headers))
                self._logger.debug('Response content: {}'.format(response.content.decode('UTF-8')))
            if response.status_code != 200:
                return None
            return json.loads(response.content)
        except Exception as e:
            if self._logger:
                self._logger.exception('{}'.format(e))
            return None

    def request(self, path: str, params: dict) -> json:
        """请求抖店API接口
        :param path: 调用的API接口地址，示例：'/material/uploadImageSync'
        :param params: 业务参数字典，示例：{'folder_id':'70031975314169695161250','url':'http://www.demo.com/demo.jpg','material_name':'demo.jpg'}
        """
        return self._request(path=path, params=params)

    def callback(self, headers: dict, body: bytes) -> json:
        """验证处理消息推送服务收到信息
        """
        data: str = body.decode('UTF-8')
        if self._logger:
            self._logger.debug('Callback Header: %s' % headers)
            self._logger.debug('Callback Body: %s' % body)
        if not data:
            return None
        if headers.get('app-id') != self._app_key:
            return None
        event_sign: str = headers.get('event-sign')
        if not event_sign:
            return None
        h = Hash(algorithm=MD5(), backend=default_backend())
        h.update('{}{}{}'.format(self._app_key, data, self._app_secret).encode('UTF-8'))
        if h.finalize().hex() != event_sign:
            return None
        return json.loads(data)

    def build_auth_url(self, service_id: str, state: str) -> str:
        """拼接授权URL，引导商家点击完成授权
        """
        if self._app_type == AppType.TOOL:
            return 'https://fuwu.jinritemai.com/authorize?service_id={}&state={}'.format(service_id, state)
        else:
            return None
