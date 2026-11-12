"""Synthetic-only grading smoke against the selected development environment."""
import argparse
import base64
import hashlib
import io
import json
import os
import secrets
import time
import uuid
import zipfile

import httpx
from fastapi.testclient import TestClient

from apps.api.db import ROOT
from apps.api.managed import ManagedStore,create_managed_app
from apps.api.subjective import load_pack,grade_submission
from apps.api.agent import create_provider
from scripts.provision_managed import load_env
from scripts.publish_cloud_content import execute,literal

CASE_ANSWER='第一个是性能，要求大促时百分之九十五的请求在五百毫秒内响应。第二个是可用性，主节点故障后三十秒内恢复。同步跨机房复制可以减少故障时数据丢失，提高可靠性，但网络往返增加写入延迟，影响性能，这是权衡点。没有大促压测，峰值容量和延迟能否达标仍有风险。应该模拟峰值请求做压力测试，并故障注入演练切换，对照五百毫秒响应和三十秒恢复目标验收。'
PAPER='''论匿名订单平台的架构演进（合成验收文稿，不是真实项目经历）
摘要：本文以一个虚构商城的订单平台为例，讨论从模块化单体向按业务能力划分服务的演进。系统需要在订单高峰时保持可用，并保证支付与库存之间的最终一致性。作者在这个合成场景中承担架构设计、接口定义和发布方案评审的职责。方案保留交易主路径的清晰边界，采用事务发件箱传递业务事件，用补偿操作处理失败，并以压力测试和故障注入验证目标。以下数字均为合成测试数据，仅用于接口验收。
一、背景与目标
这个虚构平台包含商品、订单、支付、库存四项业务能力，用户在下单后需要尽快看到明确状态。初期系统将所有模块放在同一进程中发布，核心交易和报表查询共同访问一个数据库。业务高峰期间，长时间的报表查询占用连接，影响订单写入；支付渠道发生延迟时，同步调用线程被持续占用。整个系统需要同时发布，即使只修改支付接口也要回归全部订单流程。这些问题构成了演进动机。
演进目标是在合成压测环境中保持订单接口百分之九十五响应时间低于五百毫秒，在支付渠道不可用时仍能接受订单并给出可解释状态。团队同时要求库存扣减与支付处理可以补偿，不允许用无限重试掩盖失败。项目约束是团队规模有限，无法同时维护大量服务，因此首期只分离支付与库存，订单核心仍保留模块化设计。
二、理论与边界
按业务能力划分边界是本方案的主要依据。订单负责订单生命周期与订单状态，库存负责可售数量和预占记录，支付负责渠道适配及支付结果。各服务对自己的数据负责，通过明确接口和业务事件交换信息，而不是跨库直接修改彼此的表。这样的边界有助于独立发布，但也引入网络故障和一致性处理成本。团队没有把控制器、业务层和数据库层各自拆成服务，以避免一次业务操作需要大量细粒度网络调用。
一致性方面，单个服务内部使用数据库事务，跨服务流程采用最终一致性与补偿。由于消息投递可能重复，消费者必须幂等；由于节点可能在数据库提交后、发送事件前崩溃，不能简单依靠事务结束后的普通发送调用。这些理论要求直接决定了发件箱和消费去重记录的设计。对于用户立即查询支付状态的场景，系统读取负责该状态的主节点，避免异步副本延迟造成误解。
三、方案与落地
订单服务在同一数据库事务中写入订单状态与发件箱事件。独立投递进程读取发件箱，向消息通道发送事件并更新投递状态。发送结果不明确时允许重试，因此同一业务事件可能投递多次。库存服务在本地事务中写入消费去重键并执行库存预占，只有首次处理才修改数量。支付成功事件由订单服务驱动状态转换，支付失败或超时则触发释放库存等补偿。状态转换受状态机约束，迟到的事件不能把已经取消的订单错误改成处理中。
团队评估过同步分布式事务。该方案可以提供更强的一致性，但需要协调多个服务和外部支付渠道，故障情况下可能增加资源持有时间。考虑到外部渠道不受本系统控制，最终选择可靠事件加补偿，并明确订单处理中状态对用户可见。这个权衡以业务可解释性换取了跨服务事务的复杂控制，同时仍保留了补偿监控和人工处理入口。
支付适配层设置了调用超时和并发上限，持续失败时触发熔断。订单服务不等待渠道无限返回，而是记录待确认状态，由后台任务按规则核对。各类下游调用使用独立资源池，防止支付延迟占满全部请求处理资源。对重试次数和重试间隔设置上限，超过上限进入告警与人工核对流程，而不是悄悄丢弃订单。
实施分为接口梳理、事件契约定义、库存服务影子验证、支付适配迁移和按流量比例切换几个阶段。每个阶段都有回退路径。迁移期间发现消息字段的枚举变化会使旧消费者拒绝处理，团队改为先发布兼容旧字段的消费者，再升级生产者，并通过事件版本和契约测试约束变更顺序。另一个问题是重复支付通知导致重复发货，团队将支付流水号与订单状态联合校验，并补充幂等处理测试。
四、验证与效果
观测体系使用统一请求标识贯穿网关、订单和支付适配服务，日志、调用链及错误率指标都关联该标识。出现异常时可以定位是渠道超时、库存处理慢还是消息积压。团队持续观察发件箱最老事件年龄、补偿失败数量、重复消息数量等指标，而不是只看接口平均响应时间。这样可以发现系统虽然返回成功、后台一致性流程却已经堆积的问题。
合成验收在相同数据规模与相同峰值负载下比较改造前后的结果。测试中百分之九十五响应时间由八百毫秒下降到四百二十毫秒，支付渠道被故障注入后订单入口仍能返回明确的待确认状态；库存消费者重复收到同一消息五次，实际只扣减一次。故障恢复后，发件箱中的未投递事件能被重新发送，补偿任务能够释放未支付订单的预占库存。这些是测试环境的观测结果，不直接代表生产系统的长期服务承诺。
团队还验证了数据库恢复流程，核对备份时间范围、恢复后订单状态与消息投递记录是否一致，并记录完成恢复的耗时。仅确认备份文件存在不能证明可恢复。测试结果发现一次恢复后发件箱投递位点落后，团队据此增加了恢复后按业务状态核对待投递事件的步骤，避免恢复数据后遗漏后续处理。
五、总结与不足
这次虚构演进说明，拆分服务本身不会自动解决性能和可靠性问题。真正关键的是边界清晰、失败状态可解释、事件投递可重试且消费幂等，以及持续验证补偿链路。当前方案的不足是跨服务排障和事件版本治理提高了维护成本，最终一致性也会给用户带来短暂的处理中状态。后续应继续完善自动核对和契约回归测试，在团队能力允许时逐步完善监控，而不是一开始拆出更多服务。'''
PAPER+='''
六、数据迁移与发布核对
在这个合成项目中，数据库结构调整采用先扩展后收缩的策略。首轮发布只增加可选字段并保留旧字段的读取能力，确认新版本服务稳定工作后，再迁移历史数据和清理兼容分支。团队将迁移脚本在独立测试库中重复执行，核对重复执行是否幂等，以及失败后是否能从明确的位置继续。对于业务唯一键，迁移前后都要核对唯一性和缺失情况，不能只比较记录总数就认定业务含义完全一致。
发布时先将一小部分合成请求导向新服务，对比新旧路径下的状态变化和错误日志。如果新路径出现持续的状态差异，就暂停扩大流量并使用预先设计的回退步骤。回退并不简单等于把程序版本切回去，还需要确认新版本写入的数据仍能被旧版本解释。因此事件字段和数据字段的兼容检查，必须与代码回退演练一起进行。这个过程使团队能够识别程序正常启动但业务流程已经不兼容的情况。
除了性能指标，团队也检查业务不变量。一个订单的库存预占只能成功一次，成功支付的金额应当与订单的应付金额一致，取消后的订单不应继续触发发货流程。这些检查通过合成请求、重复通知和乱序事件共同验证。检查发现差异时先保存可重放的测试事件及状态快照，再分析原因，避免在没有证据的情况下直接修改数据。以上流程仍属于虚构测试环境中的设计说明，不构成真实经营系统的合规或可靠性证明。'''


def document():
    output=io.BytesIO()
    from xml.sax.saxutils import escape
    xml='<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
    xml+=''.join('<w:p><w:r><w:t>'+escape(p)+'</w:t></w:r></w:p>' for p in PAPER.splitlines())+'</w:body></w:document>'
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('word/document.xml',xml)
        archive.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="bin" ContentType="application/octet-stream"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        archive.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        # Unreferenced synthetic bytes exercise real multi-chunk upload without
        # adding learner data or changing the paper text sent to the model.
        archive.writestr('word/media/synthetic.bin',secrets.token_bytes(600000),compress_type=zipfile.ZIP_STORED)
    return output.getvalue()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--deployed',action='store_true');parser.add_argument('--provision',action='store_true');args=parser.parse_args()
    load_env();env=os.environ['TCB_ENV_ID']
    if env!='wuji-coach-dev-d4gtwqert85ce3eae':raise SystemExit('Only selected dev environment is supported')
    if args.provision:execute(env,(ROOT/'cloudbase/migrations/20261102020000_subjective.sql').read_text())
    store=ManagedStore();user=uuid.uuid4().hex;token=secrets.token_urlsafe(32)
    store.call('login',{'identity':'disposable-review-'+user,'user_id':user,'token_hash':hashlib.sha256(token.encode()).hexdigest()})
    try:
        client=httpx.Client(base_url=os.environ['API_BASE_URL'],timeout=40) if args.deployed else TestClient(create_managed_app(store))
        with client:
            auth={'Authorization':'Bearer '+token};goal=client.post('/v1/goals',headers=auth,json={}).json()['goal_id'];base=f'/v1/goals/{goal}'
            case=client.post(base+'/case',headers=auth).json()['case']
            records=[]
            for body in [
                {'kind':'case','issue_id':case['issue_id'],'answer':CASE_ANSWER,'duration_seconds':45},
                {'kind':'essay','filename':'synthetic-review.docx','file_base64':base64.b64encode(document()).decode()}]:
                body['request_id']=uuid.uuid4().hex
                wire=body
                if body['kind']=='essay':
                    raw=body['file_base64'];upload=client.post(base+'/uploads',headers=auth,json={
                        'request_id':body['request_id'],'purpose':'essay','filename':body['filename'],
                        'byte_size':len(base64.b64decode(raw))})
                    assert upload.status_code==200,f'Upload HTTP {upload.status_code}'
                    upload=upload.json()
                    for offset in range(0,len(raw),64000):
                        result=client.post(base+'/uploads/'+upload['upload_id']+'/chunks',headers=auth,json={
                            'index':offset//64000,'data':raw[offset:offset+64000]})
                        assert result.status_code==200,f'Chunk HTTP {result.status_code}'
                    wire={k:v for k,v in body.items() if k!='file_base64'}|{'upload_id':upload['upload_id']}
                sent=client.post(base+'/reviews',headers=auth,json=wire);assert sent.status_code==202,f'Review HTTP {sent.status_code}'
                url=base+'/reviews/'+body['request_id'];result={}
                for _ in range(100):
                    result=client.get(url,headers=auth).json()
                    if result.get('status')=='complete':break
                    assert result.get('status')=='pending',f'Review ended: {result.get("status")}'
                    time.sleep(1)
                assert result.get('status')=='complete','Review did not complete'
                report=result['response']['report']
                assert report['final_score']==sum(p['weight'] for p in report['points'] if p['hit'])
                assert client.post(base+'/reviews',headers=auth,json=body).json()==result
                assert client.get(url).status_code==401
                if body['kind']=='case':assert report['final_score']>=15,'Correct case did not reach reference threshold'
                records.append({'kind':body['kind'],'score':report['final_score'],'max_score':report['max_score'],'word_count':report['word_count']})
            history=client.get(base+'/chat',headers=auth).json()['items']
            assert [t['response']['kind'] for t in history]==['case_task','review_report','review_report']
            summary=client.get(base+'/reviews/summary',headers=auth).json()
            assert summary=={'case_count':1,'essay_count':1}
            assert client.get(base+'/status',headers=auth).json()['subjects']['essay']['predicted_score'] is None
            if not args.deployed:
                bad=grade_submission(create_provider(),load_pack()['cases'][0],'case','全部换成微服务就行，不需要压测，也不用管响应时间和数据丢失。')
                assert bad['final_score']<=5,'Clearly incomplete case was over-scored'
            result_path=ROOT/'.study/platform/subjective-smoke.json'
            result_path.write_text(json.dumps({'deployed':args.deployed,'synthetic_only':True,'reviews':records,
                'history_and_replay':True,'original_file_persisted':False},ensure_ascii=False,indent=2));result_path.chmod(0o600)
            (ROOT/'.study/platform/synthetic-review.docx').write_bytes(document())
    finally:
        goals=f'SELECT id FROM coach.learning_goals WHERE user_id={literal(user)}'
        execute(env,f'''BEGIN;DELETE FROM coach.subjective_reviews WHERE goal_id IN ({goals});
          DELETE FROM coach.subjective_issues WHERE goal_id IN ({goals});DELETE FROM coach.chat_turns WHERE goal_id IN ({goals});
          DELETE FROM coach.voice_jobs WHERE goal_id IN ({goals});DELETE FROM coach.learning_goals WHERE user_id={literal(user)};
          DELETE FROM coach.sessions WHERE user_id={literal(user)};DELETE FROM coach.users WHERE id={literal(user)};COMMIT;''')
        store.client.close()
    print(json.dumps({'deployed':args.deployed,'real_model':True,'synthetic_only':True,'reviews':records,'synthetic_data_removed':True}))


if __name__=='__main__':main()
