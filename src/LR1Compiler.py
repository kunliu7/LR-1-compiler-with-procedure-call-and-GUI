# This Python file uses the following encoding: utf-8
from PyQt5 import QtWidgets
import copy
import re
import os
import io
import json
import logging
import time
import sys

from dataStructure import *

#test = Node()

# 最终项目族的DFA
class ItemSetSpecificationFamily():
    def __init__(self, cfg):
        # 首字母大写为贯穿始终的常用不变量
        self.TerminalSymbols = cfg.TerminalSymbols
        self.StartSymbol = cfg.StartSymbol
        self.NonTerminalSymbols = cfg.NonTerminalSymbols
        self.EndSymbol = cfg.EndSymbol
        self.Epsilon = cfg.Epsilon

        self.symbols = self.TerminalSymbols + self.NonTerminalSymbols
        self.itemPool = cfg.items  # itemPool：由产生式加点后的项目池
        self.itemSets = []         # 从pool中用GO函数划分
        self.edges = []            # 项目集之间的转移
        self.firstSet = cfg.firstSet
        return

    # 获取产生式，用于计算闭包
    # 可优化 相同产生式只需要dotPos == 0的
    # input str
    # return [str]
    def getLeftNT(self, NT):
        rst = []
        for item in self.itemPool:
            if item.left == NT and item.dotPos == 0:
                rst.append(item)

        return rst

    # 计算闭包  LR0:S05, P80
    # LR(1)的方式
    # https://pandolia.net/tinyc/ch12_buttom_up_parse_b.html
    # input: I=[item]
    # return [item]
    def getLR1Closure(self, I):
        rst = []
        rst.extend(I)

        # toString 已包含terms信息
        rstStr = [item.toString() for item in rst]  # 作为key值进行比对是否已有了
        while(True):
            isAddItem = 0
            for item in rst:
                right = item.right  # 引用 为了缩短变量长度

                for i in range(len(right)+1): # +1，点在尾
                    # dotPos越界问题
                    if item.dotPos == len(right): # 最后一个
                        # 相当于读到了空串
                        continue # 必须这里判断 不然下面会越界

                    if right[item.dotPos]['class'] == 'T': # 包括eps
                        continue

                    tempRst = self.extendItem(item)
                    #print('extend item rst', len(tempRst))
                    for i in tempRst:
                        tempStr = i.toString()
                        if tempStr not in rstStr:
                            rstStr.append(tempStr)
                            rst.append(i)
                            isAddItem = 1

            if isAddItem == 0:
                break

        return rst

    # 状态转换函数GO P81
    # GO(I，X)＝CLOSURE(J)
    # input I: ItemSet ( == Items)，即状态
    #       X: str, 项目族DFA的状态转移字符
    # return [Item]
    def GO(self,I,X):
        J = []

        # 求GOTO函数的时候不要把ε当终结符/非终结符处理，不要引出ε边
        # http://www.netcan666.com/2016/10/21/%E7%BC%96%E8%AF%91%E5%8E%9F
        # %E7%90%86%E5%AE%9E%E9%AA%8C%E4%B9%8BLR-1
        # -%E5%88%86%E6%9E%90%E5%99%A8%E8%AE%BE%E8%AE%A1/
        if len(I.items) == 0 or X == self.Epsilon:
            return J

        for item in I.items:
            if item.dotPos == len(item.right):
                continue
            # 空产生式
            if len(item.right) == 1 and item.right[0] == self.Epsilon:
                continue

            if item.right[item.dotPos]['type'] == X:
                temp = item.nextItem()
                if temp != None:
                    J.append(temp)  # 这里相当于new了一个新的好像, 但因为全过程没有对item进行任何改动所以只是内存大了一点 whatever

        return self.getLR1Closure(J) #self.getClosure(J)

    # edges to str 为了比较
    def edge2str(self, edge):
        return edge['start']+'->'+edge['symbol']+'->'+edge['end']

    # 获取字符串的first
    # 调用前提：已调用calFirstSet，因为是根据已算好的单个符号的firstset
    # https://blog.csdn.net/jxch____/article/details/78688894
    # input: 句型 ['a','S',...]
    # return: ['a','c',...]
    def getFirstSet(self, symbols):
        rst = []
        hasEpsAllBefore = 0

        for s in symbols:
            #print('geting firstSet', self.firstSet[s])
            tempSet = [i for i in self.firstSet[s]] # ['type']
            if self.Epsilon in tempSet:
                if hasEpsAllBefore == 0: # 第一个符号的First集有eps
                    hasEpsAllBefore = 1
                rst.extend([i for i in tempSet if i != self.Epsilon])
            else:
                hasEpsAllBefore = -1
                rst.extend(tempSet)
                break

        # 运行到这里说明所有符号都读完了，并且之前都是非终结符而且它们都能推出epsilon
        if hasEpsAllBefore == 1:
            rst.append(self.Epsilon)
        #print(rst)
        return rst


    # 延伸形态（extended configuration） ：
    # https://pandolia.net/tinyc/ch12_buttom_up_parse_b.html
    # 若一个形态 C 的黑点后面是非终结符 B ，即：
    # C = [ A -> u.Bv, a ]
    # 且有： B -> w ， b ∈ First(va) 。则形态：
    # C’ = [ B -> .w, b ]是延申状态
    # input, item
    # return, [items]
    def extendItem(self, item):
        rst = []
        # 把自己算上? 不用,extend（）是item的延申状态
        if item.right[item.dotPos]['class'] != 'NT': # 包括eps，A->.eps和A->eps.等价
            return rst

        str2BgetFirstSet = []   # 等待获取first集的字符串
        for rightIdx in range(item.dotPos+1, len(item.right)):  # 忘记加#了！！！！
            str2BgetFirstSet.append(item.right[rightIdx]['type'])

        nextItem = self.getLeftNT(item.right[item.dotPos]['type'])

        # 多个terms，目前terms表中必有一个以上
        str2BgetFirstSet.append(item.terms[0])# 加上terms符号算first
        tempFirsts = self.getFirstSet(str2BgetFirstSet)

        for i in nextItem:
            for j in tempFirsts:    # 必有#号
                rst.append(Item(i.left, i.right, 0, [j]))

        return rst

    # 构造项目集规范族 S05 P33
    """
    BEGIN
        C:={CLOSURE({S·S})}；
        REPEAT
            FOR  C中每个项目集I和G的每个符号X  DO
              IF  GO(I，X)非空且不属于C   THEN
                 把GO(I，X)放入C族中;
        UNTIL C	不再增大
    END
    """
    def buildFamily(self):


        # itemPool[0] = S’->·S, default
        iS = self.itemSets  # 取别名
        startI = []
        startI.append(self.itemPool[0]) # 默认第一个
        iS.append(ItemSet('s0', self.getLR1Closure([startI[0]] + self.extendItem(startI[0]) )   )   )
        #print('I0', iS[0].toString())

        setCnt = 1;
        # 为了方便判别GO(I，X)是否属于C，用它们的名字作为key,string作为value
        setStrings = {}
        setStrings['s0'] = iS[0].toString()
        edgeStrings = []

        while(True):
            isBigger = 0  # 是否有加新边或者状态
            for I in iS:
                #print(I)
                for X in self.symbols: # 有eps
                    rstGO = self.GO(I, X)   # GO内部：X是eps即返回
                    if len(rstGO) == 0: # GO的结果为空
                        continue
                    tempItemSet = ItemSet('s'+str(setCnt), rstGO)

                    # 可能有自己到自己的边，故不能因为不能加入新集合就停止
                    if tempItemSet.toString() in setStrings.values():
                        tempItemSet.name = list(setStrings.keys())[list(setStrings.values()).index(tempItemSet.toString())]
                        #= setStrings.index(tempItemSet.toString()) # 已存在的项目集
                    else:
                        #tempItemSet.name = 's'+str(setCnt)
                        setStrings[tempItemSet.name] = tempItemSet.toString()
                        iS.append(tempItemSet)
                        isBigger = 1
                        setCnt = setCnt + 1

                    tempEdge = {'start':I.name, 'symbol':X, 'end':tempItemSet.name}
                    tempEdgeStr = self.edge2str(tempEdge)

                    # 加边
                    if tempEdgeStr not in edgeStrings:
                        self.edges.append(tempEdge)
                        edgeStrings.append(tempEdgeStr)
                        isBigger = 1

            if isBigger == 0:
                break
        return

    # debug
    def prtFamily(self):
        print(' ----------- Start Print family --------------')
        for itemSet in self.itemSets:
            print(itemSet.name)

            for item in itemSet.items:
                rightList = [r['type'] for r in item.right]
                print(item.left, rightList, item.dotPos, item.terms)
        print('\n')
        for edge in self.edges:
            print(edge['start'], edge['symbol'], edge['end'])
        print(' ----------- End Print family --------------')
        return


# 最终项目族的DFA的状态
# 一个状态可能含有多个项目
class ItemSet():
    def __init__(self, name, items):
        self.name = name  # s0,s1...
        self.items = items # 复数个项目 Production

        # 将所有item用string连起来，方便比较
        self.string = []  #

        for item in self.items:
            itemStr = item.toString()
            if itemStr not in self.string:
                self.string.append(itemStr)

        self.string = sorted(self.string)
        return

    def toString(self):
        return "\n".join(self.string)

# 项目
class Item():
    def __init__(self, left, right, dotPos=0, terms=['#']):  # terms：拓展item,terms的默认是[],不要是None
        self.right = right # Node的集合
        self.left = left
        self.dotPos = dotPos # 用点所在的位置表示同一产生式的不同项目
        self.terms = terms # LR(1)
        return

    def nextItem(self):
        return Item(self.left,\
                self.right, self.dotPos + 1, self.terms) \
                if self.dotPos < len(self.right) + 1 \
                else None

    def toString(self):
        rst = self.left + '->'
        pos = 0
        for right in self.right:
            if pos == self.dotPos:
                rst += '@' # 代替点
            rst += right['type'] + ' '
            pos += 1

        # 也可能点在最末
        if pos == self.dotPos:
            rst += '@'

        # LR(1)，需要附上term信息
        for term in self.terms:
            rst += term + ' '

        return rst

# 穿线表节点



class CFG():

    # , terminalSymbols, nonTerminalSymbols, startSymbol, endSymbol
    def __init__(self):
        self.left = [] # 变元 Non Terminal
        self.prods = []
        self.items = []
        self.startProd = None  # 可能需要转成广义G’，改写原来的起始符号
        self.firstSet = {}
        #保留字
        self.reserved = {
                'if' : 'IF',
                'else' : 'ELSE',
                'while' : 'WHILE',

                'int':'INT',
                'return':'RETURN',
                'void':'VOID'
        }

        self.type=[
                'seperator', 'operator', 'identifier', 'int'
            ]#类别

        #词法分析所使用的正则表达式
        self.regexs=[
                '\{|\}|\[|\]|\(|\)|,|;'#界符
                ,'\+|-|\*|/|==|!=|>=|<=|>|<|='#操作符
                ,'[a-zA-Z][a-zA-Z0-9]*'#标识符
                ,'\d+'#整数
        ]
        self.CURRENT_LINE = 0


        self.TerminalSymbols = []
        self.StartSymbol = None
        self.OriginStartSymbol = None
        self.NonTerminalSymbols = []
        self.EndSymbol = None #终止符
        self.Epsilon = None

        self.pInputStr = 0
        return

    def loadGrammer(self):
        '''
        S'→E
        E→aA|bB
        A→cA|d
        B→cB|d
        '''

        # 已经转为广义G‘了，S不会出现在产生式右边
        # 单个字符串还是dict?
        '''self.TerminalSymbols = ['a','b','c','d']
        self.StartSymbol = 'S'
        self.NonTerminalSymbols = ['S','E','A','B']
        self.EndSymbol = '#'  #终止符
        self.Epsilon = '$'

        left = 'S'
        right = [
            {'class':'NT', 'name':'', 'type':'E' }
        ]
        self.prods.append(Item(left, right))
        # E
        left = 'E'
        right = [
            {'class':'T', 'name':'', 'type':'a' },\
            {'class':'NT', 'name':'', 'type':'A' }
        ]
        self.prods.append(Item(left, right))
        right = [
            {'class':'T', 'name':'', 'type':'b' },\
            {'class':'NT', 'name':'', 'type':'B' }
        ]
        self.prods.append(Item(left, right))

        # A
        left = 'A'
        right = [
            {'class':'T', 'name':'', 'type':'c' },\
            {'class':'NT', 'name':'', 'type':'A' }
        ]
        self.prods.append(Item(left, right))
        right = [
            {'class':'T', 'name':'', 'type':'d' }
        ]
        self.prods.append(Item(left, right))

        # B
        left = 'B'
        right = [
            {'class':'T', 'name':'', 'type':'c' },\
            {'class':'NT', 'name':'', 'type':'B' }
        ]
        self.prods.append(Item(left, right))
        right = [
            {'class':'T', 'name':'', 'type':'d' }
        ]
        self.prods.append(Item(left, right))'''




        '''
        S_ –> S
        S –> XX
        X –> aX
        X –> b
        S–>XX
        X–>aX
        X–>b
        '''
        self.TerminalSymbols = ['a','b','#']
        self.StartSymbol = 'S_'
        self.OriginStartSymbol = 'S'
        self.NonTerminalSymbols = ['S_','S','X']
        self.EndSymbol = '#'  #终止符
        self.Epsilon = '$'

        left = 'S_'
        right = [
            {'class':'NT', 'name':'', 'type':'S' }
        ]
        self.prods.append(Item(left, right))
        # E
        left = 'S'
        right = [
            {'class':'NT', 'name':'', 'type':'X' },\
            {'class':'NT', 'name':'', 'type':'X' }
        ]
        self.prods.append(Item(left, right))

        # A
        left = 'X'
        right = [
            {'class':'T', 'name':'', 'type':'a' },\
            {'class':'NT', 'name':'', 'type':'X' }
        ]
        self.prods.append(Item(left, right))
        right = [
            {'class':'T', 'name':'', 'type':'b' }
        ]
        self.prods.append(Item(left, right))


        # ----------------
        '''
        E->TG
        G->+TG
        G->-TG
        G->@
        T->FS
        S->*FS
        S->/FS
        S->@
        F->(E)
        F->i

        self.TerminalSymbols = ['+','-','*','/','(',')']
        self.StartSymbol = 'S_'
        self.NonTerminalSymbols = ['S_','S','A','B','C','D']
        self.EndSymbol = '#'  #终止符
        self.Epsilon = '$'

        left = 'S_'
        right = [
            {'class':'NT', 'name':'', 'type':'S' }
        ]
        self.prods.append(Item(left, right))
        # E
        left = 'S'
        right = [
            {'class':'NT', 'name':'', 'type':'A' },\
            {'class':'NT', 'name':'', 'type':'B' }
        ]
        self.prods.append(Item(left, right))
        right = [
            {'class':'NT', 'name':'', 'type':'b' },\
            {'class':'NT', 'name':'', 'type':'C' }
        ]
        self.prods.append(Item(left, right))

        # A
        left = 'A'
        right = [
            {'class':'T', 'name':'', 'type':'$' }
        ]
        self.prods.append(Item(left, right))
        right = [
            {'class':'T', 'name':'', 'type':'b' }
        ]
        self.prods.append(Item(left, right))

        left = 'B'
        right = [
            {'class':'T', 'name':'', 'type':'$' }
        ]
        self.prods.append(Item(left, right))
        right = [
            {'class':'T', 'name':'', 'type':'a' },\
            {'class':'NT', 'name':'', 'type':'D' }
        ]
        self.prods.append(Item(left, right))

        left = 'C'
        right = [
            {'class':'T', 'name':'', 'type':'b' }
        ]
        self.prods.append(Item(left, right))
        right = [
            {'class':'NT', 'name':'', 'type':'A' },\
            {'class':'NT', 'name':'', 'type':'D' }
        ]
        self.prods.append(Item(left, right))

        left = 'D'
        right = [
            {'class':'T', 'name':'', 'type':'c' }
        ]
        self.prods.append(Item(left, right))
        right = [
            {'class':'T', 'name':'', 'type':'a' },\
            {'class':'NT', 'name':'', 'type':'S' }
        ]
        self.prods.append(Item(left, right))
        '''

        '''S'->S

            (1)S->aAd

            (2)S->bAc

            (3)S->aec

            (4)S->bed

            (5)A->e'''
        return


    def readGrammerFile(self, path):
        # 必须在这里拓展成广义语法
        # 更改语法的时候注意这里也要改
        self.StartSymbol = 'program_'
        self.OriginStartSymbol = 'program'
        self.prods.append(Item(self.StartSymbol, [{'type':self.OriginStartSymbol, 'class':'NT', 'name':''}]))
        self.NonTerminalSymbols.append(self.StartSymbol)
        
        
        fd=open(path,'r')
        cntProd = 0

        tokens=[]
        while 1:
            line=fd.readline().replace('\n','')
            if not line:
                break
            token1=[]
            token3=[]
            token1.append({'type':line,'class':'NT','name':line})
            while 1:
                token2=[]
                line=fd.readline().replace('\n','')
                if not line:
                    break
                if(line[0]=='\t'):
                    line=line.strip('\t').split(' ')
                    if(line[0]=='#'):

                        tokens.append({'left':token1,'right':token3})
                        break
                    cntProd = cntProd + 1
                    for item in line:
                        match=0
                        for regex in self.regexs[0:2]:
                            result=re.match(regex,item)
                            if result:
                                match=1
                                break
                        if(match==1):
                            #token2.append({'type':type[regexs.index(regex)].upper(),'class':'T','name':item})
                            tempToken2 = {'type':item,'class':'T','name':self.type[self.regexs.index(regex)].upper()}
                        elif(item in self.reserved):
                            tempToken2 = {'type':item,'class':'T','name':item}
                        elif(item == 'id'):
                            tempToken2 = {'type':'IDENTIFIER','class':'T','name':'IDENTIFIER'}
                        elif(item=='$'):
                            tempToken2 = {'type':item,'class':'T','name':item}
                        elif(item=='num'):
                            tempToken2 = {'type':'INT','class':'T','name':'INT'}

                        else:
                            tempToken2 = {'type':item,'class':'NT','name':item}

                        token2.append(tempToken2)
                    token3.append(token2)
        for t in tokens:
            if t['left'][0]['type'] not in self.NonTerminalSymbols:
                self.NonTerminalSymbols.append(t['left'][0]['type'])
            for rightIdx in range(len(t['right'])):

                self.prods.append(Item(t['left'][0]['type'], t['right'][rightIdx]))

                for rightIdx2 in range(len(t['right'][rightIdx])):
                    if t['right'][rightIdx][rightIdx2]['class'] == 'T' and \
                        t['right'][rightIdx][rightIdx2]['type'] not in self.TerminalSymbols:
                        self.TerminalSymbols.append(t['right'][rightIdx][rightIdx2]['type'])


        self.EndSymbol = '#'  #终止符
        self.TerminalSymbols.append(self.EndSymbol)
        self.Epsilon = '$'
        return

    def readGrammerJson(self, path):
        #TERMINAL_SYMBOL_GROUP.append({'class': 'T', 'type': '#'})
        #START_PRODUCTION = Production('S', [{'class': 'NT', 'type': 'start'}], 1, terminals=['#'])
        self.StartSymbol = 'X_'
        #self.NonTerminalSymbols.append(self.StartSymbol)
        self.OriginStartSymbol = 'X'
        self.prods.append(Item(self.StartSymbol, [{'type':self.OriginStartSymbol,'class':'NT','name':''}]))

        #PRODUCTION_GROUP.append(START_PRODUCTION)
        fd=io.open(path,"r", encoding="utf-8")
        data=fd.read()
        grammer=json.loads(data)
        for none_terminal in grammer:
            if none_terminal not in self.NonTerminalSymbols:
                #print(none_terminal)
                self.NonTerminalSymbols.append(none_terminal)
            group=grammer[none_terminal]

            for expressions in group:
                #print(expressions)
                production_temp=Item(none_terminal, expressions)
                self.prods.append(production_temp)

                for item in expressions:
                    if item['class'] != 'NT':
                        if not item['type'] in self.TerminalSymbols:
                            #print(item['type'])
                            self.TerminalSymbols.append(item['type'])
        self.EndSymbol = '#'
        self.TerminalSymbols.append(self.EndSymbol)

        print('NT number:',len(self.NonTerminalSymbols), 'T number:', len(self.TerminalSymbols))
        print('\n')
        print(self.NonTerminalSymbols)
        print('\n')
        print(self.TerminalSymbols)

        #self.StartSymbol = 'start'
        #self.NonTerminalSymbols.append(self.StartSymbol)
        #self.OriginStartSymbol = 'start'

        #self.TerminalSymbols.append('$') # 要加
        return


    def prtGrammer(self):
        print('------------ 语法详情 --------------')
        print("产生式个数", len(self.prods), cntProd)
        # 有些还是要手动设置 有什么好方法吗？
        print('NT number:',len(self.NonTerminalSymbols), 'T number:', len(self.TerminalSymbols))
        print(self.NonTerminalSymbols)
        print(self.TerminalSymbols)

        for item in self.items:
            rightList = [r['type'] for r in item.right]
            print(item.left, rightList, item.dotPos) #
        print('------------ 语法详情 end --------------')
        return

    # 计算所有字符的first集
    def calFirstSet(self):
        # 若 X∈VT，则FIRST(X)={X}。
        for symbol in self.TerminalSymbols: # 这里也包括空串
            self.firstSet[symbol] = [symbol] #[{'class':'T','name':'','type':symbol}]

        # 必须要把字典firstSet的values初始化为空列表
        # 而且必须全部初始化，否则报错
        for symbol in self.NonTerminalSymbols:
            self.firstSet[symbol] = []

        for symbol in self.NonTerminalSymbols:
            self.calNTFirstSetImprove(symbol)

        return

    # 计算所有单个NT符号的First集，迭代生成
    # 单个first集的计算放在cfg这里，因为不需要用项目，用一般的产生式即可
    # https://blog.csdn.net/zheng__jun/article/details/52684612
    # return [str]
    # self.firstSet结果传给family
    # 注意两点：
    # 1. 必须并发计算first集，即按照笔算的方法，能算出几个字符，每个字符算出几个就算几个，
    # 直到不再增加，原因：不能一次性算出一个NT的first集，
    # 遇到递归即使跳过了依然可能永远算不了它，
    # 2. 由于是递归函数，对于左递归A->Aa的first求解陷入死循环，并且对于求解它的first没有意义
    # A -> Aa
    # First(A) = First(A),无意义
    # 考虑：可能存在A->eps，使得First集能进一步扩大
    # old one， 较为完备、暂时无误的是calNTFirstSetImprove
    def calNTFirstSet(self, symbol):
        #self.isSearched = [0 for s in symbol]
        eps = {'class':'T','name':'','type':self.Epsilon}
        # 若 X∈VT，则FIRST(X)={X}。
        hasEpsAllBefore = -1

        rst = []
        rstStr = []

        prods = [prod for prod in self.prods if prod.left == symbol]
        #if prod.right[0]['type'] == symbol:

        if len(prods) == 0:
            return rst

        is_add = 1
        while(is_add):
            is_add = 0

            for prod in prods:
                hasEpsAllBefore = 0
                for right in prod.right:
                    if hasEpsAllBefore >= 0: # 锁死
                        hasEpsAllBefore = hasEpsAllBefore + 1

                    # 2. 若X∈VN，且有产生式X→a…，a∈VT，
                    # 则 a∈FIRST(X)X→ε,则ε∈FIRST(X)
                    #print(right)
                    if right['class'] == 'T' or\
                        (right['type'] == self.Epsilon and len(prod.right) == 1): #不是随便加的那种eps,即A->epsilon
                        if right['type'] not in rstStr:
                            rst.append(right)
                            rstStr.append(right['type'])
                            #print('add eps')

                        hasEpsAllBefore = -2
                        break

                    # 3. 对NT
                    tempRstSet = []
                    # 之前已算出来过
                    # 但有可能是算到一半的？
                    if right['type'] in self.firstSet.keys():
                        tempRstSet = self.firstSet[right['type']]
                    else:
                        # 左递归 避免陷入死循环 可能calFirstSet中需要检验
                        # 语法文件中，写成A->$|Aa  和  A->Aa|$  都没有问题 已经过测试
                        if right['type'] == symbol:
                            break
                        tempRstSet = self.calNTFirstSet(right['type'])

                    # X→Y…是一个产生式且Y ∈VN  则把FIRST(Y)中的所有非空符号串ε元素都加入到FIRST(X)中。
                    if eps in tempRstSet:
                        if hasEpsAllBefore == 1:  # 说明产生式右侧第一个First(NT)就有eps
                            hasEpsAllBefore = -1
                        # 去除eps
                        tempRstSet = [right for right in tempRstSet \
                                      if right['type'] != eps['type']]

                        for tempRst in tempRstSet:
                            if tempRst['type'] not in rstStr:
                                rst.append(tempRst)
                                rstStr.append(tempRst['type'])
                                is_add = 1

                        # 还要继续读下去 不能break
                    else:
                        hasEpsAllBefore = -2 # eps断掉了 就可以退出了

                        for tempRst in tempRstSet:
                            if tempRst['type'] not in rstStr:
                                rst.append(tempRst)
                                rstStr.append(tempRst['type'])
                                is_add = 1
                        break

                # 到这里说明整个产生式已遍历完毕 看是否有始终能推出eps
                # 中途不能退出eps的已经break了
                # 所有right(即Yi) 能够推导出ε,(i=1,2,…n)，则
                if hasEpsAllBefore == -1:
                    is_add = 1
                    rstStr.append(self.Epsilon)
                    rst.append(eps)

        return rst

    def calNTFirstSetImprove(self, symbol):
        eps = {'class':'T','name':'','type':self.Epsilon}
        # 若 X∈VT，则FIRST(X)={X}。
        hasEpsAllBefore = -1
        prods = [prod for prod in self.prods if prod.left == symbol]
        if len(prods) == 0:
            return

        is_add = 1
        while(is_add):      # 必须！
            is_add = 0
            for prod in prods:
                hasEpsAllBefore = 0 # state 0

                for right in prod.right:
                    # 2. 若X∈VN，且有产生式X→a…，a∈VT，
                    # 则 a∈FIRST(X)  X→ε,则ε∈FIRST(X)
                    if right['class'] == 'T' or\
                        (right['type'] == self.Epsilon and len(prod.right) == 1): #不是随便加的那种eps,即A->epsilon
                        #有就加
                        if right['type'] not in self.firstSet[symbol]:
                            self.firstSet[symbol].append(right['type'])
                            is_add = 1

                        break

                    # 3. 对NT
                    # 之前已算出来过
                    # 但有可能是算到一半的
                    if len(self.firstSet[right['type']]) == 0:
                        if right['type'] != symbol: #防止陷入死循环
                            self.calNTFirstSetImprove(right['type'])

                    # X→Y…是一个产生式且Y ∈VN  则把FIRST(Y)中的所有非空符号串ε元素都加入到FIRST(X)中。
                    if self.Epsilon in self.firstSet[right['type']]:
                        # 状态机
                        if hasEpsAllBefore == 1:
                            hasEpsAllBefore = 1
                        elif hasEpsAllBefore == 0:
                            hasEpsAllBefore = 1

                    for f in self.firstSet[right['type']]:
                        if f != self.Epsilon and f not in self.firstSet[symbol]:
                            self.firstSet[symbol].append(f)
                            is_add = 1

                # 到这里说明整个产生式已遍历完毕 看是否有始终能推出eps
                # 中途不能退出eps的已经break了
                # 所有right(即Yi) 能够推导出ε,(i=1,2,…n)，则
                if hasEpsAllBefore == 1:
                    if self.Epsilon not in self.firstSet[symbol]:
                        self.firstSet[symbol].append(self.Epsilon)
                        is_add = 1

        return

    # 给产生式加点，转为项目item
    def getDotItems(self):
        for prod in self.prods:

            # 如果是单独产生空串的 只要最后一个的点
            if len(prod.right)==1 and prod.right[0]['type'] == self.Epsilon:
                self.items.append(Item(prod.left, prod.right, 0, ['#']))
                continue

            for i in range(len(prod.right) + 1):
                self.items.append(Item(prod.left, prod.right, i, ['#']))

    # debug
    def prtFirstSet(self):
        print('---------- FirstSetList --------------')
        for key in self.firstSet.keys():
            prtList = [value for value in self.firstSet[key]]
            print(key, prtList)
        print('---------- FirstSetList end --------------')
        return

    # ------------------------ 词法分析 ----------------------------
    def remove_comments(self, text):#去除注释
        comments = re.findall('//.*?\n', text, flags=re.DOTALL)
        if(len(comments)>0):
            text=text.replace(comments[0], "")
        comments = re.findall('/\*.*?\*/', text, flags=re.DOTALL)
        if(len(comments)>0):
            text=text.replace(comments[0], "")
        return text.strip()

    def scan(self, line):#经行一次扫描，返回得到的token以及剩余的字符串
        max=''
        target_regex=self.regexs[0]
        index_sub=0
        match=False
        for regex in self.regexs:
            result=re.match(regex,line)
            if(result):
                result=result.group(0)
                if(len(result)>len(max)):
                    match=True
                    max=result
                    target_regex=regex
        #出错处理
        if(match==False):
            print(u"非法字符："+line[0])
            return {"data":line[0],"regex":None,"remain":line[1:]}
        else:
            return {"data":max,"regex":target_regex,"remain":line[index_sub+len(max):]}

    def scan_line(self, line):#对一行进行重复扫描，获得一组token
        tokens=[]
        result = line.strip().strip('\t')
        origin=result
        while True:
            if result == "":
                break
            before=result
            result = self.scan(result)
            if result['regex']:
                token = {}
                token['class'] = "T"
                token['row'] = self.CURRENT_LINE
                token['colum'] = origin.find(before)+1
                token['name'] = self.type[self.regexs.index(result['regex'])].upper()
                token['data'] = result['data']
                token['type'] = token['name']

                #保留字，对应文法中->不加引号，认定为终结符
                if result['data'] in self.reserved:
                    token['name'] = self.reserved[result['data']].lower()
                    token['type'] = token['name']

                #操作符或者界符，对应文法中->加引号，认定为终结符
                if token['name']=="operator".upper() or token['name']=="seperator".upper():
                    token['type'] = token['data']


                if token['name'] == "INT":
                    token['data'] = token['data'] # 如果是int(token['data'])，词法分析表就显示不出来，因为要str
                    #print(token['data'])
                    '''
                if token['name'] == "int" and token['type'] != "int":
                    token['data'] = int(token['data'])

                if token['name'] == "INT":
                    token['type'] = 'num'
                    '''

                #swap=token['type']
                #token['type']=token['name']
                #token['name']=swap

                tokens.append(token)
            result = result['remain'].strip().strip('\t')
            if (result == ""):
                return tokens
        return tokens

    def generate_tokens(self, path):
        fd=open(path,'r')
        lines=self.remove_comments(fd.read()).split('\n')
        tokens=[]
        for line in lines:
            tokens_temp=self.scan_line(line)
            tokens+=tokens_temp
            self.CURRENT_LINE+=1
        return tokens

    def genTokensFromInputBox(self, inputStr):
        lines=self.remove_comments(inputStr).split('\n')
        tokens=[]
        for line in lines:
            tokens_temp=self.scan_line(line)
            tokens+=tokens_temp
            self.CURRENT_LINE+=1

        return tokens

    def getTokensOfOneLine(self, inputStr):
        #print(inputStr)
        if self.pInputStr >= len(inputStr):
            return []
        while True:
            idx = inputStr.find('\n', self.pInputStr)
            if idx == -1:
                idx = len(inputStr)-1
            line = inputStr[self.pInputStr:idx+1].strip()
            self.pInputStr = idx + 1
            if line == '':
                continue
            else:
                break
                
        tokens = self.scan_line(line)
        #print(tokens)
        sys.stdout.flush()
        #self.pInputStr = idx + 1
        return tokens

# 语法分析器
class SyntacticAnalyzer():

    # 两张表 S05 P87
    # ACTION[s, a]：当状态s面临输入符号a时，应采取什么动作.
    # GOTO[s, X]：状态s面对文法符号X时，下一状态是什么

    def __init__(self, cfg, family):
        self.cfg = cfg
        self.family = family
        self.EndSymbol = cfg.EndSymbol
        self.OriginStartSymbol = cfg.OriginStartSymbol
        self.StartSymbol = cfg.StartSymbol
        self.TerminalSymbols = cfg.TerminalSymbols
        self.NonTerminalSymbols = cfg.NonTerminalSymbols

        self.itemSets = family.itemSets  # 集合就是状态
        self.edges = family.edges
        self.numSet = len(self.itemSets)

        ACTIONTitle = self.TerminalSymbols
        ACTIONTitle.append(self.EndSymbol)

        # 必须把空格作为默认值，不然在里面没东西时会造成self.ACTION[stateStack[-1]][inputStr[0]][0]
        # Python error: “IndexError: string index out of range”的错，但这恰恰说明规约失败了
        self.ACTION={y.name: {x:' ' for x in ACTIONTitle} for y in self.itemSets}
        self.GOTO={y.name: {x:' ' for x in self.NonTerminalSymbols} for y in self.itemSets}

        self.prods = cfg.prods
        self.prodStrs = [i.toString() for i in self.prods]

        self.MTitle = self.TerminalSymbols + self.NonTerminalSymbols
        self.M={y.name: {x:' ' for x in self.MTitle} for y in self.itemSets}

        # --------------- 以上是语法分析，以下是中间代码生成 -------------------
        # 由于是自底向上的LR1，所以可以在语法分析的同时进行语义分析
        self.sStack = [] # semantic stack, abbr.
        self.symbolTable = [] # [item{name, function}]
        self.curFunc = 0 # 当前函数指针, 0表示全局
        self.curTempId = 0
        self.curOffset = 0
        self.curFuncSymbol = None
        self.funcTable = []
        self.curLabel = 0

        # 把全局当作一个函数
        f = FunctionSymbol()
        f.name = 'global' 
        f.label = 'global'
        self.updateFuncTable(f)
        self.curFuncSymbol = f

        self.middleCode = []
        self.mipsCode = []

        # --------------- GUI 给出错误位置 ------------------
        #self.Rst = True
        self.syntacticRst = True
        self.syntacticErrMsg = "语法分析成功！"
        self.semanticRst = True
        self.semanticErrMsg = "语义分析成功！"

        return

    # 给出一个产生式，返回这个产生式是原文法的第几个产生式
    # 通过字符串比较找索引
    def item2prodIdx(self, item):
        tempStr = item.left + '->@'
        for right in item.right:
            tempStr += (right['type'] + ' ' )
        tempStr += '# '  # 初始态terms只有#

        return self.prodStrs.index(tempStr)

    # 绘制ACTION 和 GOTO S05 P90
    # 有问题 废弃
    def getTables(self):
        for e in self.edges:
            # step 1
            #if e['symbol'] in self.TerminalSymbols:
                # 这里不会有eps    
            #    self.ACTION[e['start']][e['symbol']] = e['end']

            # step 4
            if e['symbol'] in self.NonTerminalSymbols:
                self.GOTO[e['start']][e['symbol']] = e['end']

        for I in self.itemSets:
            for item in I.items:

                # 到底是Origin还是？
                if item.left == self.StartSymbol and \
                    item.terms[0] == '#':
                    #print('acc?', item.left, item.terms[0])


                    if self.ACTION[I.name][item.terms[0]] != ' ':
                        print('rewrite error!!!', I.name, item.terms[0], 'acc')

                    self.ACTION[I.name][item.terms[0]] = 'acc'
                    continue    # y要有 不然后面会覆盖前面
                
                
                if item.dotPos < len(item.right):
                    if item.right[item.dotPos]['class'] == 'T':
                        if item.right[item.dotPos]['type'] != '$':
                            
                            # 到这里的是A→α·aβ，a为终结符
                            for e in self.edges:
                                if e['symbol'] == item.right[item.dotPos]['type']:
                                    # 这里不会有eps    
                                    if self.ACTION[I.name][e['symbol']] != ' ':
                                        print('rewrite error!!!', I.name, item.terms[0], 'e',\
                                            self.ACTION[I.name][e['symbol']], e['end'])
                                    self.ACTION[I.name][e['symbol']] = e['end']

                        else:
                            for t in item.terms:
                                # 这里有一个想给 ACTION[s0][#]=acc 重写r2的冲突
                                # 但是因为原始产生式没有出现在右边 所以两个都算成功 ?
                                # 暂缓 2019/10/17
                                # rewrite error!!! s0 # r1 acc r2
                                if self.ACTION[I.name][item.terms[0]] != ' ':
                                    print('rewrite error!!!', I.name, item.terms[0], \
                                        'r1', self.ACTION[I.name][item.terms[0]], 'r'+str(self.item2prodIdx(item)))
                                self.ACTION[I.name][t] = 'r' + str(self.item2prodIdx(item))
                
                elif item.dotPos == len(item.right):
                    
                    for t in item.terms: # 其实就一个
                        if self.ACTION[I.name][item.terms[0]] != ' ':
                            print('rewrite error!!!', I.name, item.terms[0], 'r2',\
                                self.ACTION[I.name][item.terms[0]], str(self.item2prodIdx(item)))
                        self.ACTION[I.name][t] = 'r' + str(self.item2prodIdx(item))
                    continue
        return

    def prtStep(self, stateStack, shiftStr, inputStr):

        shiftList = []
        inputList = []

        for s in shiftStr:
            shiftList.append(s['type'])

        for s in inputStr:
            inputList.append(s['type'])

        print(stateStack, shiftList, inputList, '\n')
        return

    # 输入字符串分析 S05 P92

    def isRecognizable(self, tokens):
        # 用list当作栈 可方便了
        self.rst=[]
        inputStr = []
        for token in tokens:
            inputStr.append(token['type'])
        #print(inputStr)
        #inputStr = list(tokens)
        stateStack = [] # 栈内状态序列
        shiftStr = [] # 移进规约串
        step = [] # 记录步骤 相当于一个快照

        # start
        inputStr.append('#')
        shiftStr.append('#')
        stateStack.append('s0')  # 要做更好的处理
        #self.prtStep(stateStack, shiftStr, inputStr)

        while(True):
            #if len(inputStr) <= 1:
            #    tmpTokens = self.cfg.scan_line(self.cfg.remove_comments(tokens))
            #    inputStr += [t['type'] for t in tmpTokens]
            self.prtStep(stateStack, shiftStr, inputStr)
            self.rst.append({"stateStack":stateStack, "shiftStr":shiftStr, "inputStr":inputStr})
            # 移进
            #print('debug', stateStack[-1], inputStr[0])

            if self.ACTION[stateStack[-1]][inputStr[0]][0] == 's':
                stateStack.append(self.ACTION[stateStack[-1]][inputStr[0]]) # GOTO? PPT有错？
                shiftStr.append(inputStr[0])
                inputStr.pop(0)

            # 归约
            elif self.ACTION[stateStack[-1]][inputStr[0]][0] == 'r':
                prodIdx = int(self.ACTION[stateStack[-1]][inputStr[0]][1:])
                prod = self.prods[prodIdx]
                #print(prodIdx)

                rightLen = len(prod.right)
                stateLen = len(stateStack)

                if rightLen == 1 and prod.right[0]['type'] == '$':
                    # 是空串 无需出栈
                    #print('\nwe are in\n')
                    #stateStack = stateStack[0:stateLen]
                    stateStack.append(self.GOTO[stateStack[stateLen - 1]][prod.left])
                    shiftStr = shiftStr
                else: # 不是空串
                    
                    # 肯定符合要求 不要判断了 还出事
                    #if shiftStr[stateLen - rightLen:] != [right['type'] for right in prod.right]:
                    #    print('??')
                    #    continue

                    stateStack = stateStack[0:stateLen - rightLen]  # stupid, any better idea ?
                    stateStack.append(self.GOTO[stateStack[stateLen - rightLen - 1]][prod.left])

                    shiftStr = shiftStr[0:stateLen - rightLen]
                    shiftStr.append(prod.left)

            # 结束
            elif self.ACTION[stateStack[-1]][inputStr[0]] == 'acc':
                self.prtStep(stateStack, shiftStr, inputStr)
                return True

            # 出错
            else:
                # 加空串
                #if self.ACTION[stateStack[-1]]['$'] == 'r':

                print('---------------- wrong step!-----------------------')
                self.prtStep(stateStack, shiftStr, inputStr)
                return False
    def getParseRst(self):

        return self.parseRst

    def getTables2(self):
        self.rst = []
        for e in self.edges:
            # step 1
            if e['symbol'] in self.TerminalSymbols:
                self.M[e['start']][e['symbol']] = 'shift '+ e['end']

            # step 4
            if e['symbol'] in self.NonTerminalSymbols:
                self.M[e['start']][e['symbol']] = 'goto '+ e['end']
                #print(self.M[e['start']][e['symbol']])

        for I in self.itemSets:
            for item in I.items:
                if item.dotPos == len(item.right):
                    # 不是item.left == OriginStartSymbol
                    #print(self.OriginStartSymbol)
                    if item.left == self.OriginStartSymbol and\
                        item.terms[0] == '#':
                        if self.M[I.name][item.terms[0]] != ' ':
                            print('rewrite error!!!')

                        self.M[I.name][item.terms[0]] = 'acc'
                    else:
                        if self.M[I.name][item.terms[0]] != ' ':
                            print('rewrite error!!!')

                        self.M[I.name][item.terms[0]] = \
                             'reduce ' + str(self.item2prodIdx(item))
                        #if self.item2prodIdx(item) == 0:
                            #print('fuck3')
                            #print(item.left, item.right[0]['type'], item.terms[0])
                    continue

                if len(item.right) == 1 and item.right[0]['type'] == '$':
                    #print('fuck2')
                    if item.left == self.OriginStartSymbol and\
                        item.terms[0] == '#':
                        if self.M[I.name][item.terms[0]] != ' ':
                            print('rewrite error!!!')

                        self.M[I.name][item.terms[0]] = 'acc'
                    else:
                        if self.M[I.name][item.terms[0]] != ' ':
                            print('rewrite error!!!')

                        self.M[I.name][item.terms[0]] = \
                             'reduce ' + str(self.item2prodIdx(item))
                    continue

        return

    def isRecognizable2(self, originCode):
        # 用list当作栈 可方便了
        inputStr = []
        #for token in tokens:
            #inputStr.append(token['type'])
        #inputStr = copy.deepcopy(tokens)
        inputStr += self.cfg.getTokensOfOneLine(originCode)
        #print(inputStr)
        sys.stdout.flush()
        #print(inputStr)
        #print(inputStr)
        #inputStr = list(tokens)

        #inputStr = list(inputStr)
        stateStack = [] # 栈内状态序列
        shiftStr = [] # 移进规约串

        # 记录步骤 相当于一个快照
        self.parseRst = []

        # start
        wallSymbol = {'class':'T', 'type':'#'}
        #inputStr.append(wallSymbol)
        shiftStr.append(wallSymbol)
        stateStack.append('s0')  # 要做更好的处理
        X = inputStr[0]
        while(True):
            if len(inputStr) <= 2:
                tmpInputStr = self.cfg.getTokensOfOneLine(originCode)
                if len(tmpInputStr) == 0:
                    inputStr.append(wallSymbol)
                else:
                    inputStr += tmpInputStr
                    #print(inputStr)
                
                #inputStr += [t['type'] for t in tmpTokens]

            #self.prtStep(stateStack, shiftStr, inputStr)
            # 'inputStr': list(inputStr) 不然送出去做gui有问题

            # parseRst放在这会重复添加很多项目? 忘记加深拷贝了
            self.parseRst.append({'stateStack':copy.deepcopy(stateStack), 'shiftStr':copy.deepcopy(shiftStr), 'inputStr': copy.deepcopy(inputStr)})

            # 移进
            mv = self.M[stateStack[-1]][X['type']].split(' ')[0]
            #print('mv', mv)
            target = self.M[stateStack[-1]][X['type']].split(' ')[1] \
                if len(self.M[stateStack[-1]][X['type']].split(' '))==2 else None

            if mv =='shift':
                stateStack.append(target)
                inputStr.pop(0)
                shiftStr.append(X)
                X = inputStr[0]

            elif mv == 'goto':
                stateStack.append(target)
                shiftStr.append(X)
                X = inputStr[0]

            elif mv == 'reduce':
                prodIdx = int(target)
                prod = self.prods[prodIdx]

                # 规约时同时做中间代码生成
                #print("reducing:", shiftStr)
                self.semanticAnalyze(prod, shiftStr)
                if False == self.semanticRst:
                    return False

                rightLen = len(prod.right)
                stateLen = len(stateStack)

                if rightLen == 1 and prod.right[0]['type'] == '$':
                    # 是空串
                    # 有问题
                    dst = self.M[stateStack[-1]][prod.left].split(' ')[1]
                    stateStack.append(dst)
                    shiftStr.append({'class':'NT', 'type': prod.left})
                    #X = prod.left
                    X = inputStr[0]

                else: # 不是空串

                    # 判断要归约的是否一致，但没必要，因为如果不一致的话状态转移表就是错的
                    #if shiftStr[stateLen - rightLen:] != [right['type'] for right in prod.right]:
                    #    continue

                    stateStack = stateStack[0:stateLen - rightLen]  # stupid, any better idea ?
                    shiftStr = shiftStr[0:stateLen - rightLen]
                    X = {'class':'NT', 'type': prod.left}

            elif mv == 'acc':
                print('is going to success!')
                # ['s0', 's4'] ['#', 'declarationChain'] ['#'] 
                self.prtStep(stateStack,shiftStr,inputStr)
                # 分析不到 program -> declaraChain
                # 手动加入这一个产生式给语义分析器
                # 注意是1，0是拓广文法时加的program_ -> program
                self.semanticAnalyze(self.prods[1], shiftStr) #pop错
                
                return True
            else:
                print('something is wrong: ')
                self.syntacticRst = False
                print(X)
                sys.stdout.flush()
                self.syntacticErrMsg = "语法分析错误：" + str(X['row']) + "行" + str(X['colum']) + "列"
                self.prtStep(stateStack, shiftStr, inputStr)
                return False

    # 备份
    '''
    def isRecognizable2(self, tokens):
        # 用list当作栈 可方便了
        inputStr = []
        for token in tokens:
            inputStr.append(token['type'])
        #print(inputStr)
        #inputStr = list(tokens)

        #inputStr = list(inputStr)
        stateStack = [] # 栈内状态序列
        shiftStr = [] # 移进规约串

        # 记录步骤 相当于一个快照
        step = []
        self.parseRst = []

        # start
        inputStr.append('#')
        shiftStr.append('#')
        stateStack.append('s0')  # 要做更好的处理
        #self.prtStep(stateStack, shiftStr, inputStr)
        X = inputStr[0]
        while(True):
            # self.prtStep(stateStack, shiftStr, inputStr)
            # 'inputStr': list(inputStr) 不然送出去做gui有问题

            # parseRst放在这会重复添加很多项目? 忘记加深拷贝了
            self.parseRst.append({'stateStack':copy.deepcopy(stateStack), 'shiftStr':copy.deepcopy(shiftStr), 'inputStr': copy.deepcopy(inputStr)})

            # 移进
            mv = self.M[stateStack[-1]][X].split(' ')[0]
            target = self.M[stateStack[-1]][X].split(' ')[1] \
                if len(self.M[stateStack[-1]][X].split(' '))==2 else None

            if mv =='shift':
                stateStack.append(target)
                inputStr.pop(0)
                shiftStr.append(X)
                X = inputStr[0]

            elif mv == 'goto':
                stateStack.append(target)
                shiftStr.append(X)
                X = inputStr[0]

            elif mv == 'reduce':
                prodIdx = int(target)
                prod = self.prods[prodIdx]

                # 规约时同时做中间代码生成
                print("reducing:", shiftStr)
                self.semanticAnalyze(prod, shiftStr)

                rightLen = len(prod.right)
                stateLen = len(stateStack)

                if rightLen == 1 and prod.right[0]['type'] == '$':
                    # 是空串
                    # 有问题
                    dst = self.M[stateStack[-1]][prod.left].split(' ')[1]
                    stateStack.append(dst)
                    shiftStr.append(prod.left)
                    #X = prod.left
                    X = inputStr[0]

                else: # 不是空串
                    if shiftStr[stateLen - rightLen:] != [right['type'] for right in prod.right]:
                        continue

                    stateStack = stateStack[0:stateLen - rightLen]  # stupid, any better idea ?
                    shiftStr = shiftStr[0:stateLen - rightLen]
                    X = prod.left

            elif mv == 'acc':
                return True
            else:

                return False'''


    def prtTables2(self):
        print('----------- Start Print M Tables --------------')

        for i in self.M.keys():
            print(i,self.M[i])
        print('----------- End Print M Tables --------------')
        return

    # debug
    def prtTables(self):
        print('----------- Start Print Tables --------------')
        print('ACTION Table:')
        #print('title:', [key for key in self.ACTION.keys()])
        for i in self.ACTION.keys():
            print(i,self.ACTION[i])

        print('GOTO Table:')
        #print('title:', [key for key in self.GOTO.keys()])
        for i in self.GOTO.keys():
            print(i,self.GOTO[i])
        print('----------- End Print Tables --------------')
        return

    # prod:规约时运用的产生式
    def semanticAnalyze(self, prod, shiftStr):

        # __init__中已有sStack，语义栈
        # Symbol: 见middle
        # Node: 见middle
        nt = prod.left # nt = none terminal
        r = prod.right # rs = right

        # 规划好每个产生式的语义规则
        # 主要分为说明、赋值、布尔表达式、条件控制
        # 注意，一个NT可能有多种产生式，根据r的长度判断
        # 该函数中临时变量名称约定：
            # n : Node()
            # s : symbol()

        #
            # E -> T
            # E.code = T.code
            # E.place = T.place

        print("reducing prod: ", prod.toString())
        # 总共18个NT，加油！
        sys.stdout.flush()

        if nt == 'program':
            n = self.sStack.pop(-1)
            n.name = nt

            #codeTmp = []
            
            for node in n.stack:
                for code in node.code:
                    n.code.append(code) # 不是insert(0, code)，因为stack里的node已经是正序了
                    #self.middleCode.append(code)
                #codeTmp.append(node.code)

            self.middleCode = copy.deepcopy(n.code)
            self.sStack.append(n)
            self.prtNodeCode(n)

        elif nt in ['statement',
                    'block'
                    ]:
            n = self.sStack.pop(-1)
            n.name = nt
            self.prtNodeCode(n)
            self.sStack.append(n)

        elif nt == 'declarationChain':
            n = Node()
            #if len(r) == 1: # $
                
                
            if len(r) == 2: # declaration declarationChain
                n = self.sStack.pop(-1)
                n.stack.insert(0, self.sStack.pop(-1))
                
            n.name = nt
            self.sStack.append(n)
            self.prtNodeCode(n)

        elif nt == 'typeSpecifier':
            n = Node()
            n.name = nt
            n.type = shiftStr[-1]['type'] # 拿到类型名 int
            self.sStack.append(n)

        elif nt == 'declaration': # variable or function
            n = self.sStack.pop(-1)
            n.name = nt

            if len(r) == 3: # -> typeSpecifier id ;
                defType = n.type
                defName = shiftStr[-2]['data'] # 变量名
                #for node in n.stack: 如果有连续声明才用
                #if self.curFuncSymbol == None:
                s = self.findSymbol(defName, self.curFuncSymbol.label)
                if s != None:
                    print("multi defination?")
                    self.semanticRst = False
                    self.semanticErrMsg = "变量重定义：" + str(shiftStr[-2]['row']) + "行" + str(shiftStr[-2]['colum']) +  "列"
                    return
                    # 弹窗报错之类的
                else:
                    s = Symbol()

                if n.place == None:
                    s.name = defName
                    s.place = self.getNewTemp()
                    s.type = defType
                    s.function = self.curFuncSymbol.label
                    s.size = 4
                    s.offset = self.curOffset
                    self.curOffset += s.size

                    self.updateSymbolTable(s)
                    if n.data != None: # 不是常数
                        '''if(n.type != defType): # 进不来，已经在语法分析里处理了
                            token = shiftStr[-2]
                            self.semanticRst = False
                            self.semanticErrMsg = "变量类型错误：" + token['data'] + \
                                ', 在' + str(token['row']) + "行" + \
                                    str(token['colum']) +  "列"
                            return'''
                        code=(':=',n.data,'_',s.place)
                        #print('Gen new code', code)
                        n.code.append(code)
                else:
                    s.name = defName
                    s.place = n.place
                    s.type = defType
                    s.function = self.curFunc
                    s.size = 4
                    s.offset = self.curOffset
                    self.curOffset += s.size
                    self.updateSymbolTable(s)
                    for code in n.code:
                        n.code.stack.insert(0, code)
                #n.stack=[]
                #n.prtNode()
            # elif len(r) == 1: # completeFunction
               # self.curFunc

            self.prtNodeCode(n)
            self.sStack.append(n)

        elif nt == 'completeFunction':
            # completeFunction -> declareFunction block
            n = self.sStack.pop(-1) # block
            nDefine = self.sStack.pop(-1) # declareFunction

            n.name = nt
            codeTmp = []
            codeTmp.append((nDefine.data,':','_','_')) # 函数名
            
            '''
            self.prtNodeCode(nDefine)
            self.prtNodeStack(nDefine)'''
            #print(self.curFuncSymbol.params)
            # prologue
            #codeTmp.append(('push', 'fp', '_', '_'))
            #codeTmp.append((':=', 'sp', '_', 'fp'))

            # 
            #nParas = len(self.curFuncSymbol.tempVar)
            '''codeTmp.append(('-', 'sp', 8, 'sp')) # 包括ra和fp, sp -= 16
            codeTmp.append(('store', '_', 4, 'ra')) # sw ra, 12($sp)
            codeTmp.append(('store', '_', 0, 'fp')) # sw fp, 8($sp)
            codeTmp.append((':=', 'sp', '_', 'fp')) # fp = sp, 也有 fp = '''

            
            for node in nDefine.stack: # para
                codeTmp.append(('pop','_', 4 * nDefine.stack.index(node), node.place))

            if len(nDefine.stack) > 0:
                codeTmp.append(('-', 'fp', 4 * len(nDefine.stack), 'fp'))

            # epilogue
            #codeTmp.append((':=', 'fp', '_', 'sp'))
            #codeTmp.append(('pop', 'fp', '_', '_'))

            '''codeTmp.append(('load', '_', 0, 'fp')) # lw fp, 8($sp)
            codeTmp.append(('load', '_', 4, 'ra')) # lw ra, 12($sp)
            codeTmp.append(('+', 'sp', 8, 'sp')) # 包括ra和fp, sp -= 16'''
            for code in reversed(codeTmp):
                n.code.insert(0, code)

            code_end = n.code[-1]
            if code_end[0][0] == 'l': # 非main函数
                label = code_end[0]
                n.code.remove(code_end)
                for code in n.code:
                    if code[3] == label:
                        n.code.remove(code)
              
            self.prtNodeCode(n)
            self.sStack.append(n)

        elif nt == 'declareFunction':
            # declareFunction -> typeSpecifier id ( formalParaList )
            n = self.sStack.pop(-1) #  formalParaList
            n.name = nt
            nFuncReturnType = self.sStack.pop(-1) # typeSpecifier
            f = FunctionSymbol() # 准备登记一个函数
            f.name = shiftStr[-4]['data']
            f.type = nFuncReturnType.type
            if f.name == 'main':
                f.label = 'main'
                #self.curFunc = 0
            else:
                f.label = self.getNewFuncLabel() # self.curOffset+=1
            
            # 搜索formalParaList表，把参数列表记录下来
            self.prtNodeStack(n)
            for arg in n.stack:
                s = Symbol()
                s.name = arg.data # 在处理para时，变量名放在data里
                s.place = arg.place # 此时是None
                #print('debug arg.place: ', arg.place)
                s.type = arg.type
                s.function = f.label
                s.size = 4
                s.offset = self.curOffset
                self.curOffset += s.size
                self.updateSymbolTable(s)
                #newPara = 
                f.params.append((arg.data, arg.type, arg.place))

            n.data = f.label
            self.updateFuncTable(f)
            self.stack = [] # 可以清空了
            self.curFuncSymbol = f
            self.sStack.append(n)
            print("test function ----------- \n", f.name)

        elif nt == 'formalParaList':
            n = Node()
            
            if len(r) == 3: # formalParaList -> para , formalParaList
                n = self.sStack.pop(-1)
                n.name = nt
                n.stack.insert(0, self.sStack.pop(-1))

            elif len(r) == 1 and (r[0]['type'] in ['$', 'void']): # $ | void
                n.name = nt

            elif len(r) == 1 and r[0]['type'] == 'para': # para
                #n = copy.deepcopy(self.sStack[-1])
                n.stack.insert(0, self.sStack.pop(-1))
                n.name = nt

            self.prtNodeStack(n)
            self.sStack.append(n)

        elif nt == 'para':
            # para -> typeSpecifier id
            n = self.sStack.pop(-1) # typeSpecifier node
            n.name = nt
            # n.type 已经在typeSpecifier里了
            n.place = self.getNewTemp() # 因为是形参，没有在符号表里登记，仅仅是拿个名字
            # print('debug para:', n.place)
            n.data = shiftStr[-1]['data'] # ! 注意！id在para node的data里
            self.sStack.append(n)

        elif nt == 'statementChain':
            if len(r) == 1: # $
                n = Node()
                n.name = nt
                self.sStack.append(n)
            elif len(r) == 2: # statement statementChain
                n = self.sStack.pop(-1)
                n.stack.insert(0, self.sStack.pop(-1))
                n.name = nt

                # statement.code，statementChain.code是顺序的
                # 但前者要在后者前面
                for code in reversed(n.stack[0].code):
                    n.code.insert(0, code)

                self.prtNodeCode(n)
                self.sStack.append(n)
            
        elif nt == 'assignStatement':
            # assignStatement -> id = expression ;
            
            id = shiftStr[-4]['data']  # 取到id的名字
            n = copy.deepcopy(self.sStack.pop(-1)) # expression
            #self.prtNodeStack(n)
            n.name = nt
            self.prtNodeStack(n)
            self.calExpression(n)
            self.prtNodeStack(n)
            '''nLeft = n.stack.pop(0)
            #print('len stack:', len(n.stack))
            #self.prtNodeStack(n)
            sys.stdout.flush()
            while len(n.stack) > 0:
                nOp = n.stack.pop(0)
                nRight = n.stack.pop(0)

                if nLeft.place == None: # 说明是一个常数
                    arg1 = nLeft.data
                else:
                    arg1 = nLeft.place

                if nRight.place == None:
                    arg2 = nRight.data
                else:
                    arg2 = nRight.place

                if len(nLeft.code) > 0:
                    for code in nLeft.code:
                        n.code.append(code)

                if len(nRight.code) > 0:
                    for code in nRight.code:
                        n.code.append(code)
                
                nRst = Node()
                nRst.name = nt
                nRst.place = self.getNewTemp() # 中间变量
                nRst.type = nRight.type
                code = (nOp.type, arg1, arg2, nRst.place)
                #print(code)
                n.code.append(code)
                nLeft = nRst
                n.type = nRight.type

            n.place = n.code[-1][3]  # code的place位置'''

            '''n = copy.deepcopy(self.sStack[-1])
                # 保证下面的循环一定能进入一次 分别是nOp, nRight
                n.stack.insert(0, self.sStack.pop(-1)) # operator
                n.stack.insert(0, self.sStack.pop(-1))
                #n.name = nt

                nLeft = self.sStack.pop(-1)
                #print('len stack:', len(n.stack))
                while len(n.stack) > 0:
                    nOp = n.stack.pop(0)
                    nRight = n.stack.pop(0)

                    if nLeft.place == None:
                        arg1=nLeft.data
                    else:
                        arg1 =nLeft.place

                    if nRight.place == None:
                        arg2=nRight.data
                    else:
                        arg2 =nRight.place

                    if len(nLeft.code)>0:
                        for code in nLeft.code:
                            n.code.append(code)

                    if len(nRight.code)>0:
                        for code in nRight.code:
                            n.code.append(code)
                    
                    nRst = Node()
                    nRst.name = nt
                    nRst.place = self.getNewTemp()
                    nRst.type = nRight.type
                    code = (nOp.type, arg1, arg2, nRst.place)
                    print(code)

                    n.code.append(code)
                    nLeft = nRst
                    n.type = nRight.type
                n.place = n.code[-1][3]  # code的place位置
                n.name = nt
                self.sStack.append(n)
                self.prtNodeCode(n)'''

            s = self.findSymbol(id, self.curFuncSymbol.label)
            if s == None:
                print("Assign before defination")
                self.semanticRst = False
                self.semanticErrMsg = "使用未定义变量：" + str(shiftStr[-4]['row']) + "行" + str(shiftStr[-4]['colum']) +  "列"
                return

            if s.type != n.type:
                #if(n.type != defType): # 进不来，已经在语法分析里处理了
                token = shiftStr[-4]
                self.semanticRst = False
                self.semanticErrMsg = "赋值时变量类型错误：" + token['data'] + \
                    '，在' + str(token['row']) + "行" + \
                        str(token['colum']) +  "列"
                return

            sys.stdout.flush()
            code = None
            if n.place != None: # 不做这个判断，a = 1;这样的式子不存在n.place
                code = (':=', n.place, '_', s.place)
            else:
                code = (':=', n.data, '_', s.place)
            n.code.append(code)
            self.prtNodeCode(n)
            sys.stdout.flush()
            self.sStack.append(n)

        elif nt == 'returnStatement':
            n = None
            if len(r) == 3: # return expression
                n = self.sStack.pop(-1) # expression
                
                # 计算返回值
                self.calExpression(n)
                n.type = r[0]['type'] # == return

                nRst = None
                if n.place != None:
                    nRst = n.place # 返回存放expression的变量
                else:
                    nRst = n.data # 返回expression的值（可能就等于一个常量
                n.code.append((':=', nRst, '_', 'v0')) # 返回地址
            elif len(r) == 2: # return
                n = Node()
                n.type = r[0]['type']

            #if n.type != None:
            n.code.append((n.type, '_', '_', '_'))
            #else:
            #    n.code.append((n.place, '_', '_', '_'))
            n.name = nt
            self.sStack.append(n)
            self.prtNodeCode(n)

        elif nt == 'expression':
            # expression -> primaryExpression | primaryExpression operator expression
            n = None
            if len(r) == 1:  # expression -> primaryExpression
                n = copy.deepcopy(self.sStack[-1])
                self.prtNodeStack(n)
                sys.stdout.flush()
                n.stack.insert(0 ,self.sStack.pop(-1))
                #n = self.sStack.pop(-1)
                
            elif len(r) == 3: # expression -> primaryExpression operator expression
                n = copy.deepcopy(self.sStack.pop(-1))
                n.stack.insert(0, self.sStack.pop(-1)) # operator
                n.stack.insert(0, self.sStack.pop(-1)) 

            n.name = nt
            self.sStack.append(n)
            self.prtNodeStack(n)
            sys.stdout.flush()
            
        elif nt == 'primaryExpression':
            n = Node()

            if len(r) == 1 and r[0]['type'] == 'INT': # 看词法分析
                n.data = shiftStr[-1]['data'] # 具体数字
                n.type = shiftStr[-1]['type'].lower()

            # id ( actualParaList )
            elif len(r) == 4 and r[0]['type'] == 'IDENTIFIER':

                # 找定义过的
                function = self.findFuncSymbolByName(shiftStr[-4]['data'])
                n = self.sStack.pop(-1) # actualParaList
                n.name = nt
                if function == None:
                    print('function not defined!')
                    self.semanticRst = False
                    self.semanticErrMsg = "未定义的函数：" + \
                            shiftStr[-4]['data'] + "，在" + \
                            str(shiftStr[-4]['row']) + "行" + str(shiftStr[-4]['colum']) + "列"
                    return
                
                print('debug function: ', len(function.params), len(n.stack))
                if len(function.params) != len(n.stack):
                    print('function params do not fit!')
                    sys.stdout.flush()
                    self.semanticRst = False
                    self.semanticErrMsg = "实参和形参个数不匹配：" + \
                            shiftStr[-4]['data'] + "，在" + \
                            str(shiftStr[-4]['row']) + "行" + str(shiftStr[-4]['colum']) + "列"
                    return
                '''
                #codeTmp=[]
                #codeTmp.append(('push','fp', '_', '_')) # 保存fp
                #codetmp.append((':=', ''))
                
                for node in n.stack: # 实参列表
                    if node.place != None:
                        node_result = node.place
                    else:
                        node_result = node.data
                    n.code.append(('push','_', 4 * n.stack.index(node), node_result))
                n.code.append(('call', '_', '_', function.label))
                
                codeTmp=[]
                symbolTmpList = copy.deepcopy(self.curFuncSymbol.params) # 获取调用函数参数
                spaceForParas = 4 * len(symbolTmpList)
                codeTmp.append(('-', 'sp', spaceForParas + 4 + 4, 'sp')) # 注意+4给ra留空间
                codeTmp.append(('store', '_', spaceForParas + 4, 'ra')) # 保存ra的值避免复写
                codeTmp.append(('store', '_', spaceForParas, 'fp')) # 保存ra的值避免复写
                codeTmp.((':=', 'sp', '_', 'fp')) # 保存ra的值避免复写
                for symbol in symbolTmpList: # 传参 因为是值传递
                    code_temp.append(('store','_',4 * symbol_temp_list.index(symbol),symbol[2]))

                n.code.append(('call', '_', '_', function.label))
                n.code.append((':=', 'fp', '_', 'sp'))
                n.code.append((':=', 'fp', '_', 'sp'))
                # -----------------------------
                '''
                code_temp=[]
                symbol_temp_list = copy.deepcopy(self.curFuncSymbol.params) # 获取调用函数参数
                code_temp.append(('-', 'sp', 4 * len(symbol_temp_list) + 4, 'sp')) # 注意+4给ra留空间
                code_temp.append(('store', '_', 4 * len(symbol_temp_list), 'ra')) # 保存ra的值避免复写
                for symbol in symbol_temp_list: # 保存变量 因为是值传递，这里都还是t1
                    code_temp.append(('store','_',4 * symbol_temp_list.index(symbol),symbol[2]))
                for code in reversed(code_temp):
                    n.code.insert(0, code)

                if len(function.params) > 0:
                    n.code.append(('+', 'fp', 4*len(function.params), 'fp')) # 被调用函数

                for node in n.stack: # 实参列表
                    if node.place != None:
                        node_result = node.place
                    else:
                        node_result = node.data
                    n.code.append(('push','_',4 * n.stack.index(node),node_result))
                n.code.append(('call', '_', '_', function.label))

                symbol_temp_list.reverse()
                for symbol in symbol_temp_list:
                    n.code.append(('load', '_', 4 * symbol_temp_list.index(symbol), symbol[2]))  # n.place = symbol[2]
                n.code.append(('load', '_', 4 * len(symbol_temp_list), 'ra'))
                n.code.append(('+', 'sp', 4 * len(self.curFuncSymbol.params) + 4, 'sp'))

                n.place = self.getNewTemp()
                n.code.append((':=', 'v0', '_', n.place))
                #self.sStack.append(n)
                
                # ! 关键！查了很久！保证primary的stack是空的，这也是取名primary的原因
                # express里的stack的node个数必为2n+1， n=0，1.
                n.stack = [] 
            # 变量
            elif len(r) == 1 and r[0]['type'] == 'IDENTIFIER':
                n.data = shiftStr[-1]['data'] # 拿到变量名称
                #n.type = shiftStr[-1]['type'].lower()
                nTmp = self.findSymbol(n.data, self.curFuncSymbol.label)
                # 返回的是符号表的symbol的引用，不能用
                n.type = nTmp.type
                n.place = nTmp.place
                if n == None:
                    print('undifined variable used!')
                    self.semanticRst = False
                    self.semanticErrMsg = "未定义的变量：" + \
                            shiftStr[-1]['data'] + "，在" + \
                            str(shiftStr[-1]['row']) + "行" + str(shiftStr[-1]['colum']) + "列"
                    # TODO 返回
                    return

            # ( expression )
            elif len(r) == 3 and r[1]['type'] == 'expression':
                n = self.sStack.pop(-1)
                self.calExpression(n) # 有优先级

            n.name = nt
            
            self.sStack.append(n)
            self.prtNodeStack(n)
            self.prtNodeCode(n)
            sys.stdout.flush()
            
        elif nt == 'operator':
            n = Node()
            n.name = 'operator'
            n.type = ''
            for i in range(len(r)):
                token = shiftStr[-(len(r) - i)]
                n.type += token['type']
            self.sStack.append(n)

        elif nt == 'actualParaList':
            n = None
            if len(r) == 3: # formalParaList -> expression , formalParaList
                n = self.sStack.pop(-1)
                nExp = self.sStack.pop(-1)
                self.calExpression(nExp)
                n.stack.insert(0, nExp)

            elif len(r) == 1 and (r[0]['type'] in ['$']): # $
                n = Node()

            elif len(r) == 1 and r[0]['type'] == 'expression': # expression
                #n = self.sStack.pop(-1)
                '''nExp = copy.deepcopy(self.sStack[-1])
                n = copy.deepcopy(self.sStack.pop(-1))
                self.calExpression(nExp)
                n.stack.insert(0, nExp)'''
                #self.calExpression(n)
                #n.stack = [] # 清空掉，因为expression已经计算完毕

                #nExp = copy.deepcopy(self.sStack[-1])
                n = copy.deepcopy(self.sStack.pop(-1))
                self.calExpression(n)
                self.prtNodeStack(n)
                #n.stack.insert(0, nExp)

            n.name = nt
            self.prtNodeStack(n)
            self.prtNodeCode(n)
            self.sStack.append(n)
            sys.stdout.flush()
            
        elif nt == 'ifStatement':
            n = Node()
            n.name = nt

            # if ( expression ) block
            if len(r) == 5:
                n.true = self.getNewLabel()
                n.end = self.getNewLabel()
                nT = self.sStack.pop(-1) # True
                nExp = self.sStack.pop(-1)
                self.calExpression(nExp)
                n.code.extend(nExp.code)
                n.code.append(('j>', nExp.place, '0', n.true))
                n.code.append(('j', '_', '_', n.end))
                n.code.append((n.true, ':', '_', '_'))
                for code in nT.code:
                    n.code.append(code)
                n.code.append((n.end,':','_','_'))

            # if ( expression ) block else block
            elif len(r) == 7: 
                n.true = self.getNewLabel()
                n.false = self.getNewLabel()
                n.end = self.getNewLabel()
                nF = self.sStack.pop(-1) # False
                nT = self.sStack.pop(-1) # True
                nExp = self.sStack.pop(-1)
                self.calExpression(nExp)

                #for code in nExp.code:
                #    n.code.append(code)
                n.code.extend(nExp.code)
                
                n.code.append(('j>', nExp.place, '0', n.true))
                n.code.append(('j', '_', '_', n.false))
                n.code.append((n.true, ':', '_', '_'))
                for code in nT.code:
                    n.code.append(code)
                n.code.append(('j', '_', '_', n.end))
                n.code.append((n.false, ':', '_', '_'))
                for code in nF.code:
                    n.code.append(code)
                n.code.append((n.end,':','_','_'))
            
            self.sStack.append(n)

        elif nt == 'iterStatement':
            n = Node() #生成新节点
            n.name = nt
            n.true = self.getNewLabel()#四个分支的入口
            n.false = self.getNewLabel()
            n.begin = self.getNewLabel()
            n.end = self.getNewLabel()

            if r[0]['type'] == 'while':
                statement = self.sStack.pop(-1)
                expression = self.sStack.pop(-1)
                self.calExpression(expression)
                n.code.append((n.begin, ':', '_', '_'))
                for code in expression.code:
                    n.code.append(code)
                n.code.append(('j>', expression.place, '0', n.true))
                n.code.append(('j', '_', '_', n.false))
                n.code.append((n.true,':','_','_'))
                for code in statement.code:
                    if code[0] == 'break':
                        n.code.append(('j','_','_', n.false))
                    elif code[0] == 'continue':
                        n.code.append(('j','_','_', n.begin))
                    else:
                        n.code.append(code)
                n.code.append(('j', '_', '_', n.begin))
                n.code.append((n.false,':','_','_'))

            '''elif r[0]['type'] == 'for':
                statement = self.sStack.pop(-1)
                assign = self.sStack.pop(-1)
                expression = self.sStack.pop(-1)
                Declaration = self.sStack.pop(-1)
                for code in  Declaration.code:
                    n.code.append(code)
                n.code.append((n.begin, ':', '_', '_'))
                for code in  expression.code:
                    n.code.append(code)
                n.code.append(('j>', expression.place, '0', n.true))
                n.code.append(('j', '_', '_', n.false))
                n.code.append((n.true, ':', '_', '_'))
                is_continue_existed=False
                for code in statement.code:
                    if code[0]=='break':
                        n.code.append(('j','_','_',n.false))
                    elif code[0]=='continue':
                        n.code.append(('j','_','_',n.end))
                        is_continue_existed=True
                    else:
                        n.code.append(code)
                if is_continue_existed:
                    n.code.append((n.end,':','_','_'))
                for code in assign.code:
                    n.code.append(code)
                n.code.append(('j', '_', '_', n.begin))
                n.code.append((n.false,':','_','_'))'''
            self.sStack.append(n)


        # DEBUG
        self.prtFuncTable()
        self.prtSymbolTable()
        self.prtSemanticStack()
        print("=====================================================================")
        sys.stdout.flush()
        return

    
   
    
    def findSymbol(self, name, function):
        for s in self.symbolTable:
            if s.name == name and s.function == function:
                return s
        return None

    def updateSymbolTable(self, symbol):
        for item in self.symbolTable:
            if item.name == symbol.name and item.function == symbol.function:
                self.symbolTable.remove(item)
                break
        self.symbolTable.append(symbol)
        return

    def getNewTemp(self):
        self.curTempId += 1
        return "t" + str(self.curTempId)

    def prtSemanticStack(self):
        print("------- print semantic stack -----------")
        for s in self.sStack:
            print(s.name)
        #print("------- end print semantic stack -----------")
        return

    def getNewFuncLabel(self):
        self.curFunc+=1
        return 'f' + str(self.curFunc)

    def updateFuncTable(self, functionSymbol):
        for item in self.funcTable:
            if item.name == functionSymbol.name:
                self.funcTable.remove(item)
                break
        self.funcTable.append(functionSymbol)
        return
    
    def prtFuncTable(self):
        print("------- print function table -----------")
        for f in self.funcTable:
            paraList = []
            for para in f.params:
                # para = (arg.data, arg.type, arg.place)
                paraList.append(para[0])
            
            print('Function:', f.name, 'paraList:', paraList)
            #print('code:')
            #for code in f.code:
            #    print(code)
            #print('-------------------------')
        #print("------- end print function table -----------")
        return

    def prtSymbolTable(self):
        print("------- print symbol table -----------")
        for s in self.symbolTable:
            #paraList = []
            #for para in f.params:
            #    paraList.append(para.name)            
            print(s.name, s.type, s.place, s.function)
        #print("------- end print symbol table -----------")
        return

    def popAppend(self, nt):
        n = self.sStack.pop(-1)
        n.name = nt
        self.sStack.append(n)

    def prtNodeCode(self, node):
        print('------ code of node: ' + node.name)
        for code in node.code:
            print(code)

        return

    def prtNodeStack(self, node):
        print('------ stack of node: ' + node.name)
        nameList = []
        for node in node.stack:
            nameList.append(node.name)
        print(nameList)
        return
        
    # 对于expression节点n，生成对应代码，放在属性code里
    def calExpression(self, n):
        
        if len(n.stack) == 1: # 只有一个值 就不用下面的三元计算了
            n = copy.deepcopy(n.stack[0])
            self.prtNodeCode(n)
            n.stack = []
            return True
        # 所有要计算的节点都已经在stack里了，其实相当于生成一个新节点
        # 函数参数的n相当于引用
        n.code = [] 
        self.prtNodeStack(n)
        sys.stdout.flush()
        nLeft = n.stack.pop(0)
        while len(n.stack) > 0:
            nOp = n.stack.pop(0)
            nRight = n.stack.pop(0)

            if nLeft.place == None: # 说明是一个常数
                arg1 = nLeft.data
            else:
                arg1 = nLeft.place

            if nRight.place == None:
                arg2 = nRight.data
            else:
                arg2 = nRight.place

            if len(nLeft.code) > 0:
                for code in nLeft.code:
                    n.code.append(code)

            if len(nRight.code) > 0:
                for code in nRight.code:
                    n.code.append(code)
            
            nRst = Node()
            nRst.name = None # 不需要名字
            nRst.place = self.getNewTemp() # 中间变量
            nRst.type = nRight.type
            code = (nOp.type, arg1, arg2, nRst.place)
            #print(code)
            n.code.append(code)
            nLeft = nRst
            n.type = nRight.type

        n.place = n.code[-1][3]  # code的place位置

        return True

    def findFuncSymbolByName(self, name):
        for f in self.funcTable:
            if f.name == name:
                return f
        return None
        
    def getNewLabel(self):
        self.curLabel += 1
        return 'l' + str(self.curLabel)

    def saveMidCodeToFile(self):
        text = ''
        for code in self.middleCode:
            text += '{}, {}, {}, {}\n'.format(code[0], code[1], code[2], code[3])
        middleCodeObj = open("middleCodeFile.txt", 'w+')
        middleCodeObj.write(text)
        middleCodeObj.close()
        return True

class ObjectCodeGenerator():
    def __init__(self, middleCode, symbolTable):
        self.middleCode = copy.deepcopy(middleCode)
        self.mipsCode = []
        self.regTable = {'$' + str(i):'' for i in range(7, 26)}
        self.varStatus = {} # 记录变量此时是在寄存器当中还是memory
        self.DATA_SEGMENT = 10010000
        self.STACK_OFFSET = 8000
        self.symbolTable = copy.deepcopy(symbolTable)
        return

    def getRegister(self, identifier, codes):
        if identifier[0] != 't':
            return identifier
        if identifier in self.varStatus and \
            self.varStatus[identifier] == 'reg':
            for key in self.regTable:
                if self.regTable[key] == identifier:
                    return key
        print('---------------')
        print(identifier + ' is applying a reg')
        print(self.regTable)
        print(self.varStatus)

        while True:
            for key in self.regTable:
                if self.regTable[key] == '':
                    self.regTable[key] = identifier
                    self.varStatus[identifier] = 'reg'
                    return key
            #return list(self.varStatus.keys()) \ 
            #    [list(self.varStatus.values()).index(identifier)]
            self.freeRegister(codes)

    # 释放一个寄存器，可以优化
    def freeRegister(self, codes):
        # 提取出使用了reg的变量, 形式如t1, t2, ...
        varRegUsed = list(filter(lambda x:x != '', self.regTable.values()))
        #print(varRegUsed)
        # 统计这些变量后续的使用情况
        varUsageCnts = {}
        for code in codes:
            #print(code)
            for item in code:
                #print(item)
                tmp = str(item)
                if tmp[0] == 't': # 是个变量
                    if tmp in varRegUsed:
                        if tmp in varUsageCnts:
                            varUsageCnts[tmp] += 1
                        else:
                            varUsageCnts[tmp] = 1
        
        print('===\n', 'varUsageCnts:', varUsageCnts, '\n===\n')
        
        sys.stdout.flush()
        flag = False

        # 找出之后不会使用的变量所在的寄存器
        for var in varRegUsed:
            if var not in varUsageCnts:
                for reg in self.regTable:
                    if self.regTable[reg] == var:
                        self.regTable[reg] = ''
                        self.varStatus[var] = 'memory'
                        flag = True
        if flag:
            return

        # 释放最少使用的寄存器，
        sorted(varUsageCnts.items(), key=lambda x:x[1])
        varFreed = list(varUsageCnts.keys())[0]
        for reg in self.regTable:
            if self.regTable[reg] == varFreed:
                for item in self.symbolTable:
                    if item.place == varFreed: # t1, t2, ...
                        self.mipsCode.append('addi $at, $zero, 0x{}'.format(self.DATA_SEGMENT))
                        self.mipsCode.append('sw {}, {}($at)'.format(reg, item.offset))
                        self.regTable[reg] = ''
                        self.varStatus[varFreed] = 'memory'
                        return

        return

    def genMips(self):
        mc = self.mipsCode # alias
        dc = self.middleCode # alias
        dc.insert(0, ('call', '_', '_', 'programEnd'))
        dc.insert(0, ('call', '_', '_', 'main'))
        mc.append('addiu $sp, $zero, 0x{}'.format(self.DATA_SEGMENT + self.STACK_OFFSET))
        mc.append('or $fp, $sp, $zero')

        while dc:
            code = dc.pop(0)
            tmp = []
            for item in code:
                if item=='v0':
                    tmp.append('$v0')
                else:
                    tmp.append(item)
            code = tmp
            
            if code[0] == ':=':
                src = self.getRegister(code[1], dc)
                dst = self.getRegister(code[3], dc)
                mc.append('add {},$zero,{}'.format(dst, src))

            # function or label
            elif code[1] == ':':
                if code[0][0] in ['f','main']: # is a function definition
                    mc.append('') # empty line
                mc.append('{}:'.format(code[0]))

            # 跳转到函数的label处
            elif code[0] == 'call':
                mc.append('jal  {}'.format(code[3]))

            # actual arg of a function call
            elif code[0] == 'push':
                '''
                e.g.
                ('push', '_', 0, 't18')
                ('push', '_', 4, 't19')
                ('push', '_', 8, 't21')
                t21
                t19
                t18 <- fp
                '''

                if code[3] == 'ra': # return addr
                    mc.append('sw $ra, {}($fp)'.format(code[2]))
                else:
                    register = self.getRegister(code[3], dc)
                    if str(register)[0] != '$':
                        mc.append("add $a0, $zero, {}".format(register))
                        register = '$a0'
                    mc.append('sw {}, {}($fp)'.format(register, code[2]))

            # get args inside the function
            elif code[0] == 'pop':
                if code[3] == 'ra':
                    mc.append('lw $ra, {}($fp)'.format(code[2]))
                else:
                    register = self.getRegister(code[3], dc)
                    mc.append('lw {}, {}($fp)'.format(register, code[2]))

            # store var from reg to memory
            elif code[0] == 'store':
                if code[3] == 'ra':
                    mc.append('sw $ra, {}($sp)'.format(code[2]))
                else:
                    register = self.getRegister(code[3], dc)
                    if str(register)[0] != '$':
                        mc.append("add $a0,$zero,{}".format(register))
                        register = '$a0'
                    mc.append('sw {}, {}($sp)'.format(register, code[2]))

            # load var from memory to reg
            elif code[0] == 'load':
                if code[3] == 'ra':
                    mc.append('lw $ra, {}($sp)'.format(code[2]))
                else:
                    register = self.getRegister(code[3], dc)
                    mc.append('lw {}, {}($sp)'.format(register, code[2]))

            # jump instruction
            elif code[0] == 'j':
                mc.append('j {}'.format(code[3]))

            elif code[0] == 'j>':
                arg1 = self.getRegister(code[1], dc)
                mc.append('bgt {},$zero,{}'.format(arg1, code[3]))

            elif code[0] == 'return':
                mc.append('jr $ra')
            
            # algorithm operations, has 3 oprand
            else:
                if code[0] == '+':
                    if code[1] == 'fp':
                        mc.append("add $fp,$fp,{}".format(code[2]))
                    elif code[1]=='sp':
                        mc.append("add $sp,$sp,{}".format(code[2]))
                    else:
                        arg1 = self.getRegister(code[1], dc)
                        arg2 = self.getRegister(code[2], dc)
                        arg3 = self.getRegister(code[3], dc)
                        if str(arg1)[0] != '$':
                            mc.append("add $a1,$zero,{}".format(arg1))
                            arg1 = '$a1'
                        mc.append("add {},{},{}".format(arg3, arg1, arg2))

                elif code[0] == '-':
                    if code[1] == 'fp':
                        mc.append("sub $fp,$fp,{}".format(code[2]))
                    elif code[1] == 'sp':
                        mc.append("sub $sp,$sp,{}".format(code[2]))
                    else:
                        arg1 = self.getRegister(code[1], dc)
                        arg2 = self.getRegister(code[2], dc)
                        arg3 = self.getRegister(code[3], dc)
                        if str(arg1)[0]!='$':
                            mc.append("add $a1,$zero,{}".format(arg1))
                            arg1 = '$a1'
                        if str(arg2)[0]!='$':
                            mc.append("add $a2,$zero,{}".format(arg2))
                            arg2 = '$a2'
                        mc.append("sub {},{},{}".format(arg3, arg1, arg2))

                elif code[0] == '*':
                    arg1 = self.getRegister(code[1], dc)
                    arg2 = self.getRegister(code[2], dc)
                    arg3 = self.getRegister(code[3], dc)
                    if str(arg1)[0]!='$':
                        mc.append("add $a1,$zero,{}".format(arg1))
                        arg1 ='$a1'
                    if str(arg2)[0]!='$':
                        mc.append("add $a2,$zero,{}".format(arg2))
                        arg2 = '$a2'
                    mc.append("mul {},{},{}".format(arg3, arg1, arg2))

                elif code[0] == '/':
                    arg1 = self.getRegister(code[1], dc)
                    arg2 = self.getRegister(code[2], dc)
                    arg3 = self.getRegister(code[3], dc)
                    if str(arg1)[0]!='$':
                        mc.append("add $a1,$zero,{}".format(arg1))
                        arg1='$a1'
                    if str(arg2)[0]!='$':
                        mc.append("add $a2,$zero,{}".format(arg2))
                        arg2 = '$a2'
                    mc.append("div {},{},{}".format(arg3, arg1, arg2))
                        
                elif code[0] == '%':
                    arg1 = self.getRegister(code[1], dc)
                    arg2 = self.getRegister(code[2], dc)
                    arg3 = self.getRegister(code[3], dc)
                    if str(arg1)[0]!='$':
                        mc.append("add $a1,$zero,{}".format(arg1))
                        arg1='$a1'
                    if str(arg2)[0]!='$':
                        mc.append("add $a2,$zero,{}".format(arg2))
                        arg2 = '$a2'
                    mc.append("div {},{},{}".format(arg3, arg1, arg2))
                    mc.append("mfhi {}".format(arg3))

                elif code[0] == '<':
                    arg1 = self.getRegister(code[1], dc)
                    arg2 = self.getRegister(code[2], dc)
                    arg3 = self.getRegister(code[3], dc)
                    if str(arg1)[0]!='$':
                        mc.append("add $a1,$zero,{}".format(arg1))
                        arg1='$a1'
                    if str(arg2)[0]!='$':
                        mc.append("add $a2,$zero,{}".format(arg2))
                        arg2 = '$a2'
                    mc.append("slt {},{},{}".format(arg3, arg1, arg2))

                elif code[0] == '>':
                    arg1 = self.getRegister(code[1], dc)
                    arg2 = self.getRegister(code[2], dc)
                    arg3 = self.getRegister(code[3], dc)
                    if str(arg1)[0]!='$':
                        mc.append("add $a1,$zero,{}".format(arg1))
                        arg1='$a1'
                    if str(arg2)[0]!='$':
                        mc.append("add $a2,$zero,{}".format(arg2))
                        arg2 = '$a2'
                    mc.append("sgt {},{},{}".format(arg3, arg1, arg2))

                elif code[0] == '!=':
                    arg1 = self.getRegister(code[1], dc)
                    arg2 = self.getRegister(code[2], dc)
                    arg3 = self.getRegister(code[3], dc)
                    if str(arg1)[0] != '$':
                        mc.append("add $a1,$zero,{}".format(arg1))
                        arg1 = '$a1'
                    if str(arg2)[0] != '$':
                        mc.append("add $a2,$zero,{}".format(arg2))
                        arg2 = '$a2'
                    mc.append("sne {},{},{}".format(arg3, arg1, arg2))

                elif code[0] == '==':
                    arg1 = self.getRegister(code[1], dc)
                    arg2 = self.getRegister(code[2], dc)
                    arg3 = self.getRegister(code[3], dc)
                    if str(arg1)[0] != '$':
                        mc.append("add $a1,$zero,{}".format(arg1))
                        arg1 = '$a1'
                    if str(arg2)[0] != '$':
                        mc.append("add $a2,$zero,{}".format(arg2))
                        arg2 = '$a2'
                    mc.append("seq {},{},{}".format(arg3, arg1, arg2))
        
        self.prtMips()
        sys.stdout.flush()
        return

    def prtMips(self):
        for i in self.mipsCode:
            print(i)

        return

    def saveObjCodeToFile(self):
        
        return True