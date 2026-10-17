#!/usr/bin/env python3
"""Build the public recalled-case practice and answer booklets, without learner state."""

from pathlib import Path
import argparse
import re, html
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'past-papers/case-selected/assets'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--with-answers', action='store_true', help='Include reference answers after each case')
parser.add_argument('--output-dir', type=Path, default=ROOT / 'past-papers/case-selected/pdf', help='Destination directory')
args = parser.parse_args()
WITH_ANSWERS = args.with_answers
filename = '系统架构设计师_案例真题精选_必选加四选二' + ('_题目与答案' if WITH_ANSWERS else '') + '.pdf'
OUT = args.output_dir / filename
OUT.parent.mkdir(parents=True, exist_ok=True)
FONT = 'STSong-Light'
pdfmetrics.registerFont(UnicodeCIDFont(FONT))
INK = colors.HexColor('#172f45')
BLUE = colors.HexColor('#244d70')
GREY = colors.HexColor('#637180')
W = 174*mm
styles = {
 'body': ParagraphStyle('body',fontName=FONT,fontSize=10.5,leading=16,wordWrap='CJK',spaceAfter=5),
 'cell': ParagraphStyle('cell',fontName=FONT,fontSize=9.5,leading=14,wordWrap='CJK'),
 'small': ParagraphStyle('small',fontName=FONT,fontSize=8.5,leading=12,wordWrap='CJK',textColor=GREY,spaceAfter=6),
 'head': ParagraphStyle('head',fontName=FONT,fontSize=15,leading=23,textColor=BLUE,spaceAfter=9),
 'q': ParagraphStyle('q',fontName=FONT,fontSize=11,leading=18,textColor=INK,spaceBefore=9,spaceAfter=6,keepWithNext=True),
 'title': ParagraphStyle('title',fontName=FONT,fontSize=22,leading=31,textColor=INK,spaceAfter=11),
 'center': ParagraphStyle('center',fontName=FONT,fontSize=10.5,leading=16,alignment=1),
}
story=[]
def p(txt,kind='body'):
    txt=txt.replace('✅','').replace('→','->').replace('—','-').replace('～','~').replace('·','｜')
    txt=re.sub(r'\*\*|`','',txt)
    story.append(Paragraph(html.escape(txt),styles[kind]))
def table(rows,widths=None):
    cells=[[Paragraph(html.escape(str(x)), styles['cell']) for x in row] for row in rows]
    t=Table(cells,colWidths=widths or [W/len(rows[0])]*len(rows[0]),repeatRows=1)
    t.setStyle(TableStyle([
      ('GRID',(0,0),(-1,-1),.45,colors.HexColor('#aebcc9')),
      ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#edf3f8')),
      ('VALIGN',(0,0),(-1,-1),'TOP'),
      ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
      ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
    ])); story.append(t);story.append(Spacer(1,3*mm))
def image(path,width,maxheight=200*mm):
    from PIL import Image as PILImage
    im=PILImage.open(path); iw,ih=im.size
    height=width*ih/iw
    if height>maxheight: width*=maxheight/height; height=maxheight
    story.append(Image(path,width=width,height=height,mask='auto'))
    story.append(Spacer(1,3*mm))
def raw_block(file,start,end=None):
    raw=(ROOT/file).read_text();raw=raw[raw.index(start)+len(start):]
    if end:raw=raw[:raw.index(end)]
    return raw
def begin(num,title,source):
    story.append(PageBreak())
    p(f'试题{num}  '+('必选题' if num=='一' else '选做题（四选二）'),'small')
    p(title,'head');p(source,'small')
def question(n,score,text):
    p(f'【问题{n}】（{score}分）','q');p(text)
def answer_page(num,qs):
    if WITH_ANSWERS:
        from selected_case_answers import ANSWERS
        story.append(PageBreak());p(f'试题{num}｜参考答案与采分关键词','head')
        p('参考作答由回忆版答案结合技术文档校正，不是官方标准答案或官方评分细则。','small')
        for item in ANSWERS[num]:
            if item[0]=='table':table(item[1],item[2] if len(item)>2 else None)
            else:p(item[1],item[0])
        return
    story.append(PageBreak());p(f'试题{num} · 作答页','head')
    p('姓名：________________    本题用时：________分钟','small')
    for n,score,rows in qs:
        p(f'【问题{n}】（{score}分）','q')
        t=Table([[''] for _ in range(rows)],colWidths=[W],rowHeights=[8*mm]*rows)
        t.setStyle(TableStyle([('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#c3cdd6'))]))
        story.append(t);story.append(Spacer(1,3*mm))

story.append(Spacer(1,7*mm))
p('系统架构设计师','title');p('案例分析 · 真题精选练习','title')
p('必选题 + 四选二','head')
p('数据库 / MySQL方向 · Redis · Cache-Aside · Web','body')
p('跨年份公开回忆版组卷 01 | recalled_real | '+('题目与答案' if WITH_ANSWERS else '题目册'),'small')
story.append(Spacer(1,8*mm))
table([
 ['姓名：________________','练习日期：________________'],
 ['开始时间：____________','结束时间：________________'],
 ['选做题号：____________','实际用时：________分钟'],
], [W/2,W/2])
p('作答规则','head')
for s in [
 '试题一必做；试题二至试题五任选两道。每道25分，共75分。练习建议限时90分钟，合格线45分。',
 '本卷面向数据库、缓存和Web方向跨年份编排，四道选做题均为软件方向；并非某一年的完整原卷。原考试未必同时提供四道这类题。',
 '保留年份、原题号、题干、小问、分值及填空形式。来源为公开回忆或整理版本，不称为官方原卷。部分文字作排版和明显错字修正。',
 ('每道大题后直接附参考答案，按小问给出可书写的答案和采分关键词。答案不是官方评分细则，技术争议处单独说明。' if WITH_ANSWERS else '题目页不附答案或解析。表格直接填空；简答和流程说明可使用对应作答页。Web架构图单独一页，便于看清八个空。'),
 '试题一的必选身份沿用2024下来源；试题二至五在本练习中均为选做题。不要把必选题范围固定理解为只考ATAM。',
]:p(s)
p('本卷题目','head')
table([
 ['练习题号','年份 / 原题号','方向'],
 ['一（必选）','2024下 / 试题一','质量属性与故障检测'],
 ['二（选做）','2026上 / 试题三','数据库并发控制与Redis'],
 ['三（选做）','2025下 / 批次一试题四','Redis类型、持久化、淘汰'],
 ['四（选做）','2024下 / 试题二','Cache-Aside与缓存一致性'],
 ['五（选做）','2024下 / 试题四','Web架构、分词器、RESTful'],
],[35*mm,62*mm,77*mm])

begin('一','质量属性与故障检测','2024年下半年 · 原试题一 · 25分 · 公开回忆整理版')
block=raw_block('past-papers/case-by-year/2024下.md','### 2.1. 试题一：质量属性','**答案：**')
intro=block.split('**【问题')[0].strip()
intro=intro[intro.index('【说明】')+4:]
prefix,reqs=intro.split('（a）',1)
p('【说明】','q');p(prefix.strip())
for m in re.finditer(r'（([a-j])）(.*?)(?=（[a-j]）|$)','（a）'+reqs,re.S): p('（'+m[1]+'）'+m[2].strip())
story.append(PageBreak());p('试题一｜问题与填空表（续）','head')
question(1,14,'为了辅助架构师张工完成系统架构设计，首先需对上述需求进行分析。请分析需求（a）~（j），补充完善下表中（1）~（7）的空白处。')
table([
 ['需求','功能性需求 / 具体质量属性需求名称'],
 ['（a）','功能性'],['（b）','（1）________________'],['（c）','可靠性'],
 ['（d）','（2）________________'],['（e）','（3）________________'],
 ['（f）','（4）________________'],['（g）','（5）________________'],
 ['（h）','可用性'],['（i）','（6）________________'],['（j）','（7）________________'],
],[30*mm,144*mm])
p('表格按希赛网公开回忆版图表转录；来源见末页。','small')
question(2,11,'针对可用性需求（h），张工提出可采用ping/echo策略完成故障检测，但李工认为从系统资源利用率的角度出发，采用心跳策略完成故障检测更优。')
p('（1）请分别说明如何采用ping/echo策略和心跳策略来完成可用性的故障检测。')
p('（2）请解释李工认为心跳策略更优的原因。')
answer_page('一',[(1,14,3),(2,11,17)])

begin('二','数据库并发控制与Redis优化','2026年上半年 · 原试题三 · 25分 · 公开回忆版')
block=raw_block('past-papers/case-by-year/2026上.md','# 试题3','## 参考答案')
intro=block.split('【问题1】')[0].replace('【说明】','').strip()
intro=intro.replace('如果秒杀系统中并发控制机制，','如果秒杀系统缺少并发控制机制，')
p('【说明】','q');p(intro)
for n,score in [(1,8),(2,11),(3,6)]:
    part=block.split(f'【问题{n}】')[1]
    part=part.split(f'【问题{n+1}】')[0]
    part=re.sub(r'^\s*（\d+分）','',part).strip()
    question(n,score,part)
answer_page('二',[(1,8,5),(2,11,10),(3,6,7)])

begin('三','Redis数据类型、持久化与内存淘汰','2025年下半年 · 批次一原试题四 · 25分 · 公开整理版')
block=raw_block('past-papers/case-by-year/2025下.md','## 试题四：Redis数据类型与缓存策略','## 试题五：')
intro=block.split('### 问题1')[0].replace('### 题目描述','').strip()
p('【说明】','q')
for line in intro.splitlines():
    if line.strip():p(line)
for n,score in [(1,10),(2,7),(3,8)]:
    part=block.split(f'### 问题{n}')[1].split('**参考答案**')[0]
    part=re.sub(r'^\s*（\d+分）','',part).strip()
    question(n,score,part)
    if n==1:
      table([['数据类型','存储的值','可实现的业务功能'],
        ['STRING','字符串、整数或浮点数','（1）____________'],
        ['LIST','列表','（2）____________'],
        ['SET','无序集合','（3）____________'],
        ['HASH','包括键值对的无序散列表','（4）____________'],
        ['ZSET','有序集合','（5）____________']], [32*mm,76*mm,66*mm])
      p('表格按软考在线公开题库样张第34页转录；按题干功能字母填写，可填多个。','small')
answer_page('三',[(1,10,3),(2,7,9),(3,8,9)])

begin('四','Cache-Aside缓存一致性','2024年下半年 · 原试题二 · 25分 · 公开回忆整理版')
block=raw_block('past-papers/case-by-year/2024下.md','### 2.2. 试题二：数据库cache-aside架构','**答案：**')
intro=block.split('**【问题1】**')[0]
intro=intro[intro.index('【说明】')+4:].strip()
intro=intro.replace('最新材料','最新数据')
p('【说明】','q');p(intro)
for n,score in [(1,10),(2,6),(3,9)]:
    part=block.split(f'**【问题{n}】**')[1].split(f'**【问题{n+1}】**')[0]
    part=re.sub(r'^\s*（\d+分）','',part).strip()
    part=part.replace('素材不一致','数据不一致')
    question(n,score,part)
    if n==1:
        image(ASSETS / 'cache-aside-read.png',W,maxheight=60*mm)
        p('图1 数据读取流程（公开回忆版图）','small')
    if n==2:
        image(ASSETS / 'cache-aside-write.png',W,maxheight=32*mm)
        p('图2 数据更新流程（公开回忆版图）','small')
answer_page('四',[(1,10,6),(2,6,4),(3,9,12)])

begin('五','Web架构、Elasticsearch分词器与RESTful','2024年下半年 · 原试题四 · 25分 · 公开回忆版')
p('【说明】','q');p('基于Elasticsearch分词的商品推荐系统，使用微信小程序接入。')
question(1,6,'说明Standard、Simple、Whitespace、Keyword分词器各自的分词原理和特点差异。')
question(2,12,'根据商品推荐系统架构图，从下列名称中选择合适内容，填写图中（1）~（8）的空白处。架构图见下一页。')
p('分层候选：接入层、显示层、网络层、应用层、业务逻辑层、控制层、数据层。')
p('技术候选：MyBatis、Nginx、Flink、JavaScript、Node.js、RESTful、Elasticsearch、Kafka。')
question(3,7,'RESTful架构有什么特点？它如何实现前后端分离？')
p('本题背景及问法取自仓库回忆版，填空图取自公开回忆复原图；采用其已有空号，不附已填答案图。','small')
story.append(PageBreak());p('试题五 · 问题2架构图','head')
image(ASSETS / 'web-architecture-blanks.png',161*mm,maxheight=175*mm)
p('图3 商品推荐系统架构（公开回忆复原图，非官方原图）','small')
table([['空号','填写内容','空号','填写内容'],
 ['（1）','____________','（5）','____________'],['（2）','____________','（6）','____________'],
 ['（3）','____________','（7）','____________'],['（4）','____________','（8）','____________']], [20*mm,67*mm,20*mm,67*mm])
answer_page('五',[(1,6,7),(2,12,3),(3,7,11)])

story.append(PageBreak());p('来源与练习记录','head')
p('来源说明','q')
p('本册使用仓库现有回忆题面，并补回公开来源的填空图表。商业题库网站不等同于考试主管部门；本册不采用其“官方题库”称谓。不同回忆版本的措辞可能有差异。','body')
sources=[
 ('题一题面、题四题面、题五题面','past-papers/case-by-year/2024下.md'),
 ('题二题面','past-papers/case-by-year/2026上.md；source-pdfs/2026上/回忆版PDF'),
 ('题三题面','past-papers/case-by-year/2025下.md（批次一）'),
 ('题一需求表','https://www.educity.cn/rk/5437194.html'),
 ('题三Redis数据类型表','https://www.rkpass.cn/yangzhang/4_80_1.pdf（第34页）'),
 ('题四流程图','https://jishuzhan.net/article/1900600614273495041'),
 ('题五填空图','https://jishuzhan.net/article/2041681427436208129'),
]
for label,value in sources:
    p(label,'q')
    if value.startswith('http'):
       url=value.split('（')[0]; story.append(Paragraph(f'<link href="{url}" color="#244d70">{html.escape(value)}</link>',styles['small']))
    else:p(value,'small')
if WITH_ANSWERS:
    story.append(PageBreak());p('参考答案｜技术校核来源','head')
    p('以下官方技术文档用于校正锁、缓存和分词器等实现细节。题目分值沿用回忆题面，答案不另造逐条官方分数。','small')
    refs=[
      ('悲观锁兼容关系','https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html'),
      ('MySQL一致性非锁定读','https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html'),
      ('Redis WATCH事务','https://redis.io/docs/latest/develop/using-commands/transactions/'),
      ('Redis分布式锁','https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/'),
      ('Redis持久化','https://redis.io/docs/latest/management/persistence/'),
      ('Redis内存淘汰','https://redis.io/docs/latest/develop/reference/eviction/'),
      ('Redis发布订阅','https://redis.io/docs/latest/develop/pubsub/'),
      ('Elasticsearch分词器','https://www.elastic.co/docs/reference/text-analysis/analyzer-reference'),
    ]
    for label,url in refs:
        p(label,'q');story.append(Paragraph(f'<link href="{url}" color="#244d70">{url}</link>',styles['small']))
p('记录区','q')
table([
 ['项目','填写'],['必选题得分','________ / 25'],
 ['选做题____得分','________ / 25'],['选做题____得分','________ / 25'],
 ['合计','________ / 75'],['最需要补的题号 / 小问','________________________'],
],[62*mm,112*mm])
p('生成或阅读本册不构成掌握证据。学习成绩应以实际独立作答及评分为准。','small')

def footer(canvas,doc):
    canvas.saveState();canvas.setFont(FONT,8);canvas.setFillColor(GREY)
    canvas.setStrokeColor(colors.HexColor('#c3cdd6'));canvas.line(18*mm,15*mm,192*mm,15*mm)
    canvas.drawString(18*mm,10*mm,'案例真题精选 | 回忆版 | 必选 + 四选二'+(' | 含参考答案' if WITH_ANSWERS else ''))
    canvas.drawRightString(192*mm,10*mm,f'{doc.page}')
    canvas.restoreState()

doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,
    topMargin=18*mm,bottomMargin=20*mm,title='系统架构设计师案例真题精选练习：必选加四选二'+('（含参考答案）' if WITH_ANSWERS else ''),
    author='学习资料整理',pageCompression=1,invariant=1)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
