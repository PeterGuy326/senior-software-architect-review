import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi import HTTPException

from apps.api.agent import BigModel, SiliconFlow, create_provider
from scripts.import_model_config import ROOT, read_config


class ProviderTest(unittest.TestCase):
    def test_free_only_mode_refuses_paid_aliases_before_network(self):
        for model in ('deepseek-ai/DeepSeek-V3.2','Pro/Qwen/Qwen3-8B'):
            with patch.dict(os.environ,{'MODEL_BASE_URL':'https://api.siliconflow.cn/v1',
                                       'MODEL_NAME':model,'MODEL_API_KEY':'synthetic-not-a-real-key','MODEL_FREE_ONLY':'true'}):
                with patch('apps.api.agent.httpx.post') as post:
                    with self.assertRaises(HTTPException):
                        SiliconFlow().complete([{'role':'user','content':'测试'}])
                    post.assert_not_called()

    def response(self,request=None):
        return httpx.Response(200,json={'choices':[{'message':{'content':'回复'}}]},
                              request=request or httpx.Request('POST','https://example.invalid'))

    def test_glm_uses_official_free_model_and_thinking_protocol(self):
        with patch.dict(os.environ,{'MODEL_PROVIDER':'bigmodel','MODEL_BASE_URL':'https://open.bigmodel.cn/api/paas/v4',
                                   'MODEL_NAME':'glm-4.7-flash','MODEL_API_KEY':'synthetic-not-a-real-key'}):
            with patch('apps.api.agent.httpx.post',return_value=self.response()) as post:
                provider=create_provider()
                self.assertIsInstance(provider,BigModel)
                self.assertEqual(provider.complete([{'role':'user','content':'测试'}])['content'],'回复')
                body=post.call_args.kwargs['json']
                self.assertEqual(body['thinking'],{'type':'disabled'})
                self.assertNotIn('enable_thinking',body)
                self.assertEqual(post.call_args.args[0],'https://open.bigmodel.cn/api/paas/v4/chat/completions')
                self.assertIn('tools',body)

    def test_glm_rejects_paid_variant_and_wrong_endpoint_before_network(self):
        for base,model in [('https://other.invalid','glm-4.7-flash'),
                           ('https://open.bigmodel.cn/api/paas/v4','glm-4.7-flashx')]:
            with patch.dict(os.environ,{'MODEL_BASE_URL':base,'MODEL_NAME':model,'MODEL_API_KEY':'synthetic-not-a-real-key'}):
                with patch('apps.api.agent.httpx.post') as post:
                    with self.assertRaises(HTTPException):
                        BigModel().complete([{'role':'user','content':'测试'}])
                    post.assert_not_called()

    def test_siliconflow_protocol_remains_compatible(self):
        with patch.dict(os.environ,{'MODEL_PROVIDER':'siliconflow','MODEL_BASE_URL':'https://api.siliconflow.cn/v1',
                                   'MODEL_NAME':'deepseek-ai/DeepSeek-V3.2','MODEL_API_KEY':'synthetic-not-a-real-key'}):
            with patch('apps.api.agent.httpx.post',return_value=self.response()) as post:
                self.assertIsInstance(create_provider(),SiliconFlow)
                create_provider().complete([{'role':'user','content':'测试'}],tools=False)
                body=post.call_args.kwargs['json']
                self.assertIs(body['enable_thinking'],False)
                self.assertNotIn('thinking',body)
                self.assertNotIn('tools',body)

    def test_upstream_errors_never_echo_credentials(self):
        with patch.dict(os.environ,{'MODEL_BASE_URL':'https://open.bigmodel.cn/api/paas/v4',
                                   'MODEL_NAME':'glm-4.7-flash','MODEL_API_KEY':'synthetic-private-key'}):
            with patch('apps.api.agent.httpx.post',side_effect=httpx.ConnectError('synthetic-private-key')):
                with self.assertRaises(HTTPException) as error:
                    BigModel().complete([{'role':'user','content':'测试'}])
                self.assertNotIn('synthetic-private-key',str(error.exception))

    def test_candidate_configuration_requires_matching_endpoint_and_free_model(self):
        directory=ROOT/'.study/platform'
        directory.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=directory) as temporary:
            candidate=Path(temporary)/'input.env'
            template='MODEL_PROVIDER=bigmodel\nMODEL_BASE_URL={}\nMODEL_NAME={}\nMODEL_API_KEY=synthetic-not-a-real-key\n'
            candidate.write_text(template.format('https://open.bigmodel.cn/api/paas/v4','glm-4.7-flash'))
            self.assertEqual(read_config(candidate)['MODEL_NAME'],'glm-4.7-flash')
            candidate.write_text(template.format('https://other.invalid','glm-4.7-flash'))
            with self.assertRaises(ValueError):
                read_config(candidate)
            candidate.write_text(template.format('https://open.bigmodel.cn/api/paas/v4','glm-4.7-flashx'))
            with self.assertRaises(ValueError):
                read_config(candidate)

    def test_free_provider_backs_off_only_for_transient_capacity_errors(self):
        with patch.dict(os.environ,{'MODEL_BASE_URL':'https://open.bigmodel.cn/api/paas/v4',
                                   'MODEL_NAME':'glm-4.7-flash','MODEL_API_KEY':'synthetic-not-a-real-key'}):
            busy=httpx.Response(429,json={'error':{'code':'1305'}},request=httpx.Request('POST','https://example.invalid'))
            with patch('apps.api.agent.httpx.post',side_effect=[busy,self.response()]) as post, patch('apps.api.agent.time.sleep') as sleep:
                provider=BigModel()
                self.assertEqual(provider.complete([{'role':'user','content':'测试'}])['content'],'回复')
                self.assertEqual(provider.request_count,2)
                self.assertEqual(provider.retry_count,1)
                sleep.assert_called_once_with(1)
            quota=httpx.Response(429,json={'error':{'code':'1308'}},request=httpx.Request('POST','https://example.invalid'))
            with patch('apps.api.agent.httpx.post',return_value=quota) as post, patch('apps.api.agent.time.sleep') as sleep:
                with self.assertRaises(HTTPException) as error:
                    BigModel().complete([{'role':'user','content':'测试'}])
                post.assert_called_once()
                sleep.assert_not_called()
                self.assertEqual(error.exception.provider_code,'1308')
