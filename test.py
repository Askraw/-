# -*- coding:utf-8 -*-
import sys
from urllib import request
from bs4 import BeautifulSoup
import random 
import os
import json
import io
import glob
import requests
import string
from queue import Queue
import re
import time
from queue import Queue
basepath=r'E:\code'
readpath=r'\final.txt'
writepath=r'\result.txt'

def func():
    f=open(basepath+readpath,'r',encoding='utf-8')
    lines=f.readlines()
    for line in lines:
        wordSet=set()
        q=Queue()
        #把初始读入文件的第一行入set
        line=(re.sub(r'\r\n|\n|\r', '', line)).strip()
        linewords=line.split('\t')
        for word in linewords:
            wordSet.add(word)
            q.put(word)

        while not q.empty():
            searchword=q.get()
            #searchList_bable=spider_bable(searchword)
            searchList_db=spider_db(searchword)
            #spider返回的2个同义词列表，如果有新词加入set和用于循环的queue来寻找新的枝叶
            #而已经出现在set的词 必定加入了queue 所以对其他词不处理
            # for word in searchList_bable:
            #     if word not in wordSet:
            #         wordSet.add(word)
            #         q.put(word)
            for word in searchList_db:
                if word not in wordSet:
                    wordSet.add(word)
                    q.put(word)
        #while结束的时候把set写入这个词表就行了
        #这里可以在while开始的时候设一个标准词 然后再输出其他同义词:)
        f2=open(basepath+writepath,'ab+')
        num=0
        for word in wordSet:
            if num==0:
                f2.write((word).encode('UTF-8'))
                print(word)
                num+=1
            else:
                print('tongyici: '+word)
                f2.write(('\t'+word).encode('UTF-8'))
        f2.write(('\n').encode('UTF-8'))
        f2.close()
    print('Mission Completed!')
def spider_db(word):
    # headers={}
    # sleeptime=1+random.random()
    # time.sleep(sleeptime)
    entityUrl=r'http://shuyantech.com/api/cndbpedia/ment2ent?q='
    attrUrl=r'http://shuyantech.com/api/cndbpedia/value?q='
    attrlist=[r'&attr=其他名',r'&attr=别名',r'&attr=别称']
    apikey=r'&apikey=7b17e34845551bfda392a4c1ad858ee2'
    url=entityUrl+word+apikey
    res=[]#返回值
    try:
        response= requests.get(url)
        response.encoding = response.apparent_encoding
        jsonstr=json.loads(response.text)
        #print(jsonstr['ret'])
        #print(str(len(jsonstr['ret'])))
        
        if len(jsonstr['ret']) == 0:
            return res

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
        return res
    except Exception as e:
            print(e)
            return res
if  __name__=='__main__':
    res=[]
    res=spider_db('癫痫')
    print(res)