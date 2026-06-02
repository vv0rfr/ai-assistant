"""
短信验证码服务
支持阿里云SMS和开发模式（控制台输出）
"""
import os
import logging
from flask import current_app

logger = logging.getLogger(__name__)


class SMSService:
    """短信服务基类"""

    def send_code(self, phone, code):
        """发送验证码"""
        raise NotImplementedError


class AliyunSMSService(SMSService):
    """阿里云短信服务"""

    def __init__(self):
        self.access_key_id = current_app.config['SMS_ACCESS_KEY_ID']
        self.access_key_secret = current_app.config['SMS_ACCESS_KEY_SECRET']
        self.sign_name = current_app.config['SMS_SIGN_NAME']
        self.template_code = current_app.config['SMS_TEMPLATE_CODE']

    def send_code(self, phone, code):
        """通过阿里云SMS发送验证码"""
        try:
            # 阿里云SMS SDK调用
            # 需要安装: pip install alibabacloud-dysmsapi20170525
            from alibabacloud_dysmsapi20170525.client import Client
            from alibabacloud_dysmsapi20170525 import models as sms_models
            from alibabacloud_tea_openapi import models as open_api_models

            config = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret
            )
            config.endpoint = 'dysmsapi.aliyuncs.com'
            client = Client(config)

            request = sms_models.SendSmsRequest(
                phone_numbers=phone,
                sign_name=self.sign_name,
                template_code=self.template_code,
                template_param=f'{{"code":"{code}"}}'
            )

            response = client.send_sms(request)
            if response.body.code == 'OK':
                logger.info(f"验证码已发送到 {phone}")
                return True, '验证码已发送'
            else:
                logger.error(f"发送失败: {response.body.message}")
                return False, f'发送失败: {response.body.message}'

        except ImportError:
            logger.error("未安装阿里云SMS SDK，请运行: pip install alibabacloud-dysmsapi20170525")
            return False, '短信服务配置错误'
        except Exception as e:
            logger.error(f"发送短信异常: {str(e)}")
            return False, f'发送失败: {str(e)}'


class DevSMSService(SMSService):
    """开发模式短信服务（控制台输出）"""

    def send_code(self, phone, code):
        """开发模式：在控制台输出验证码"""
        import sys
        logger.info(f"[开发模式] 验证码已生成 - 手机号: {phone}, 验证码: {code}")
        print(f"\n{'='*50}", flush=True)
        print(f"[开发模式] 短信验证码", flush=True)
        print(f"手机号: {phone}", flush=True)
        print(f"验证码: {code}", flush=True)
        print(f"有效期: 5分钟", flush=True)
        print(f"{'='*50}\n", flush=True)
        sys.stdout.flush()
        return True, '验证码已发送（开发模式，请查看控制台）'


def get_sms_service():
    """获取短信服务实例"""
    # 检查是否配置了阿里云SMS
    if (current_app.config.get('SMS_ACCESS_KEY_ID') and
        current_app.config.get('SMS_ACCESS_KEY_SECRET') and
        current_app.config.get('SMS_TEMPLATE_CODE')):
        return AliyunSMSService()
    else:
        return DevSMSService()
