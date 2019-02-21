#coding=utf-8
# author luojin 19/1/14 

import random 
import sys
import os
import json
import io
from datetime import datetime 
from flask import Flask,render_template,redirect,url_for
from flask_bootstrap import Bootstrap
from flask import request
from flask_apscheduler import APScheduler
from flask import jsonify
import time
import requests
import string
from queue import Queue
import re
#通过flask服务器 不同机器之前发起post请求，调用接口类传输json
#代码还有个发起结构化存储文档的post请求，待补全
app = Flask(__name__)
bootstrap = Bootstrap(app)


class Config(object):
    JOBS=[
        {
            'id': 'backup',
            'func': '__main__:backup',
            'trigger': 'interval',
            'seconds': 86400
        }
    ]
    SCHEDULER_API_ENABLED = True
#备份的时候按词条同义词个数排序写入
def sortWords(basepath,readpath,filename):
    f=open(basepath+readpath,'r',encoding='utf-8')
    lines=f.readlines()
    counts={}
    cache=[]
    i=0
    for line in lines:
        cache.append(line)
        
        # if len(words)>2:
        #     print(line)
    cache=list(set(cache))
    for line in cache:
        line=line.strip()
        words=line.split('\t')
        counts[i]=len(words)
        i+=1
    keys=counts.keys()
    values=counts.values()
    list_one = [(key, val) for key, val in zip(keys, values)]
    list_sort = sorted(list_one, key=lambda x: x[1], reverse=True)
    f2=open(basepath+filename,'ab+')
    str1=''
    for item in list_sort:
        if(str1!=cache[item[0]]):
            f2.write((cache[item[0]]).encode('UTF-8'))
        str1=cache[item[0]]
    f2.close()
#备份函数
def backup():
    localtime= time.localtime(time.time())
    filename='backup/'+str(localtime[0])+'_'+str(localtime[1])+'_'+str(localtime[2])+'.txt'
    print(filename)
    basepath=r'./'
    readpath=r'synonym.txt'
    sortWords(basepath,readpath,filename)
#在加入新的同义词或者词条的时候的整合函数  
def integration(words):#对于加入新词以后可能
    basepath=r'./'
    txtpath=r'synonym.txt'
    f=open(basepath+txtpath,'r',encoding='utf-8')
    lines=f.readlines()
    f.close()
    writelines=set()
    for line in lines:
        for word in words:
            if word in line:
                newline=line.strip('\n')
                allwords=newline.split('\t')
                for item in allwords:
                    if item==word:
                        writelines.add(line)
                        break

    print(writelines)
    f_w= open(basepath+txtpath,"w",encoding="utf-8") 
    for line in lines:
        if line not in writelines:
            f_w.write(line)
    wordset=set()
    for line in writelines:
        line=line.strip('\n')
        words=line.split('\t')
        for word in words:
            wordset.add(word)
    newline=''
    print(wordset)
    for word in wordset:
        newline+=word+'\t'
    newline=newline.strip('\t')
    newline+='\n'
    f_w.write(newline)
    f_w.close()
    return

#对于新加入的同义词进入DB-pedia迭代
def spider_db(words):
    # headers={}
    # sleeptime=1+random.random()
    # time.sleep(sleeptime)
    entityUrl=r'http://shuyantech.com/api/cndbpedia/ment2ent?q='
    attrUrl=r'http://shuyantech.com/api/cndbpedia/value?q='
    attrlist=[r'&attr=其他名',r'&attr=别名',r'&attr=别称']
    apikey=r'&apikey=7b17e34845551bfda392a4c1ad858ee2'
    retSet=set()
    for word in words:
        url=entityUrl+word+apikey
        res=[]#返回值
        try:
            response= requests.get(url)
            response.encoding = response.apparent_encoding
            jsonstr=json.loads(response.text)
            #print(jsonstr['ret'])
            #print(str(len(jsonstr['ret'])))
            
            if len(jsonstr['ret']) == 0:
                retSet.add(word)
                return retSet

            queryword=jsonstr['ret'][0]#query 列表第一个词 是最准的
            for attr in attrlist:
                url2=attrUrl+queryword+attr+apikey
                response2=requests.get(url2)
                response2.encoding = response2.apparent_encoding
                jsonstr2=json.loads(response2.text)
                if len(jsonstr2['ret'])!=0 :
                    for simiword in jsonstr2['ret']:
                        #print(simiword,end='\t')
                        res.append(simiword)
                    #print('\n',end='')
                    #print('no return value')
            # for item in res:
            #     print(item)
            for item in res:
                retSet.add(item)
            retSet.add(word)
        except Exception as e:
                print(e)
                return retSet
    return retSet
@app.route('/',methods=['GET','POST'])
def home():
    return render_template("index.html")#homepage.html在templates文件夹下
@app.route('/searchItem',methods=['POST'])
def req():
    print('请求方式为------->', request.method)
    args = request.args.get("search") or "args没有参数"
    print('args参数是------->', args)
    form = request.form.get('search') or 'form 没有参数'
    print('form参数是------->', form)
    if form=='form 没有参数':
        return redirect(url_for('home'))
    form=form.strip()
    if form=='':
        return redirect(url_for('home'))
    word=form
    basepath=r'./'
    txtpath=r'synonym.txt'
    f=open(basepath+txtpath,'r',encoding='utf-8')
    lines=f.readlines()
    f.close()
    displayWords={}
    for line in lines:
        if word in line:
            line=line.strip('\n')
            words=line.split('\t')#这里进行模糊搜索
            # for item in words:
            #     if item==word:
            #         return render_template("sRes.html",u=words,len=len(words))
            aimword=''
            for item in words:
                if word in item:
                    if aimword=='':
                        aimword=item
                    else:
                        if len(item)<len(aimword):
                            aimword=item
                        else: 
                            continue
            displayWords[aimword]=''
            for single in words:
                    if single==aimword:
                        if len(words)>3:
                            displayWords[aimword]=words[0]+' '+words[1]+' '+words[2]+'...'
                        else:
                            for addword in words:
                                displayWords[aimword]=displayWords[aimword]+addword+' '
                        break
            #这个for循环执行完以后aimwords里是 所有模糊搜索到的词语 list，接下来需要排序
    if displayWords=={}:
        return render_template("sNoRes.html")
    else:
        #aimwords=sorted(aimwords,key=lambda x:len(word)/len(x),reverse=True)
        
        # for item in displayWords.keys():#添加用于展示的词语
        #     for line in lines:
        #         if item in line:
        #             line=line.strip('\n')
        #             words=line.split('\t')
        #             for single in words:
        #                 if single==item:
        #                     if len(words)>3:
        #                         displayWords[item]=words[0]+' '+words[1]+' '+words[2]+'...'
        #                     else:
        #                         for addword in words:
        #                             displayWords[item]=displayWords[item]+addword+' '
        #                     break
        displayList=sorted(displayWords.items(),key=lambda x:len(word)/len(x[0]),reverse=True)
        return render_template("sResList.html",u=displayList,v=form)
    
@app.route('/searchItem/<reqWord>',methods=['GET'])
def req2(reqWord):
    word=reqWord
    basepath=r'./'
    txtpath=r'synonym.txt'
    f=open(basepath+txtpath,'r',encoding='utf-8')
    lines=f.readlines()
    f.close()
    for line in lines:
        if word in line:
            line=line.strip('\n')
            words=line.split('\t')
            for item in words:
                if item==word:
                    return render_template("sRes.html",u=words,len=len(words))
    return render_template("sNoRes.html")
 #另一种传参方式，可以在浏览器进行传参

@app.route('/addWord/<word>',methods=['POST'])
def addWord(word):
    print ('baseword: '+word)#baseword
    form = request.form.get('addwords') or 'form 没有参数'
    if form== 'form 没有参数':
        return redirect(url_for('req2',reqWord=word))
    form=form.strip()
    if form=='':
        return redirect(url_for('req2',reqWord=word))
    #integration(form[0])
    basepath=r'./'
    txtpath=r'synonym.txt'
    with open(basepath+txtpath,"r",encoding="utf-8") as f:
        lines = f.readlines()
    #print(lines)
    f.close()
    with open(basepath+txtpath,"w",encoding="utf-8") as f_w:
        for line in lines:
            if word in line:
                line=line.strip('\n')
                words=line.split('\t')
                mark=0
                for item in words:
                    if item==word:
                        mark=1
                        break
                if form!='form 没有参数' and mark==1:
                    form=form.strip('\n')
                    addwords=form.split()
                    for addword in addwords:
                        line+='\t'+addword
                    line+='\n'
            f_w.write(line)
    f_w.close()
    words=form.split()
    for item in words:
        print(item)
    
    integration(words)
    return redirect(url_for('req2',reqWord=words[0]))
    

@app.route('/addItem',methods=['POST','GET'])
def addItem():
    print('请求方式为------->', request.method)
    args = request.args.get("add") or "args没有参数"
    print('args参数是------->', args)
    form = request.form.get('add') or 'form 没有参数'
    print('form参数是------->', form)
    
    #return jsonify(args=args, form=form)
    return render_template("addItem.html")#homepage.html在templates文件夹下
@app.route('/addItem/detail',methods=['POST'])
def add():
    form = request.form.get('words') or 'form 没有参数'
    print('form参数是------->', form)
    words=[]
    if form == 'form 没有参数':
        return redirect(url_for('add'))
    form=form.strip('\n')
    words=form.split()
    wordset=spider_db(words)
    basepath=r'./'
    txtpath=r'synonym.txt'
    f=open(basepath+txtpath,'ab+')
    output=''
    i=0
    for word in wordset:
        if i==0:
            output+=word
            i+=1
        else:
            output+='\t'+word
            i+=1
    f.write((output).encode('UTF-8'))
    f.write(('\n').encode('UTF-8'))
    f.close()
    #待补全 写入过程 
    integration(wordset)
    return redirect(url_for('req2',reqWord=words[0]))
@app.route('/deleteWord/<word>/<base>',methods=['POST'])
def deleteWord(word,base):
    delword=word.strip('\n')
    baseword=base.strip('\n')
    basepath=r'./'
    txtpath=r'synonym.txt'
    if delword!=baseword:
        with open(basepath+txtpath,"r",encoding="utf-8") as f:
            lines = f.readlines()
        #print(lines)
        f.close()
        with open(basepath+txtpath,"w",encoding="utf-8") as f_w:
            for line in lines:
                if delword in line:
                    line=line.strip('\n')
                    words=line.split('\t')
                    newline=''
                    tag=0
                    for item in words:
                        if item==delword and tag==0:#防止重复词删2次
                            tag=1
                            continue
                        else:
                            newline+=item+'\t'
                    newline=newline.strip('\t')
                    newline+='\n'
                    f_w.write(newline)
                    continue
                f_w.write(line)
    else:#只有一个词的情况
        with open(basepath+txtpath,"r",encoding="utf-8") as f:
            lines = f.readlines()
        #print(lines)
        f.close()
        with open(basepath+txtpath,"w",encoding="utf-8") as f_w:
            for line in lines:
                if delword in line:
                    line=line.strip('\n')
                    words=line.split('\t')
                    newline=''
                    tag=0
                    for item in words:
                        if item==delword:
                            tag=1
                            continue
                        else:
                            newline+=item+'\t'
                    if tag==0:
                        newline=newline.strip('\t')
                        newline+='\n'
                        f_w.write(newline)
                        continue
                    else:
                        tag=0
                        continue
                f_w.write(line)  
    
    f_w.close()      
    return redirect(url_for('req2',reqWord=baseword))
    

@app.route('/deleteItem/<word>',methods=['GET'])
def deleteItem(word):
    print(word)
    basepath=r'./'
    txtpath=r'synonym.txt'
    with open(basepath+txtpath,"r",encoding="utf-8") as f:
        lines = f.readlines()
    #print(lines)
    f.close()
    with open(basepath+txtpath,"w",encoding="utf-8") as f_w:
        for line in lines:
            if word in line:
                continue
            f_w.write(line)
    
    f_w.close()
    return redirect(url_for('home'))

@app.route('/changeWord/<word>',methods=['POST'])
def changeWord(word):
    baseword=word.strip('\n')
    changeWord=request.form.get('changeword') or 'form 没有参数'
    if changeWord=='form 没有参数':
        return redirect(url_for('req2',reqWord=baseword))
    basepath=r'./'
    txtpath=r'synonym.txt'
    with open(basepath+txtpath,"r",encoding="utf-8") as f:
        lines = f.readlines()
    #print(lines)
    f.close()
    with open(basepath+txtpath,"w",encoding="utf-8") as f_w:
        for line in lines:
            if baseword in line:
                line=line.strip('\n')
                words=line.split('\t')
                newline=''
                tag=0
                for item in words:
                    if item==baseword and tag==0:
                        newline+=changeWord+'\t'
                        tag=1
                    else:
                        newline+=item+'\t'
                
                newline=newline.strip('\t')
                newline+='\n'
                f_w.write(newline)
                continue
            f_w.write(line)   
    f_w.close() 
    wordset=set()
    wordset.add(changeWord)
    integration(wordset)
    return    redirect(url_for('req2',reqWord=changeWord))

    
#这里host必须设为0,0,0,0 否则外部浏览器没法通过本机IP访问flask服务器
if __name__ == '__main__':
    #app.jinja_env.filters['zip'] = zip
    app.config.from_object(Config())
    scheduler = APScheduler()
    # it is also possible to enable the API directly
    # scheduler.api_enabled = True
    scheduler.init_app(app)
    scheduler.start()
    app.run(host='0.0.0.0',port = 54321,debug=False)