# This Python file uses the following encoding: utf-8

# if__name__ == "__main__":
#     pass


class Node():
    def __init__(self):
        self.place = None #语句块入口的中间变量
        self.code = [] #传递而来的或者生成的中间代码
        self.stack = [] #翻译闭包表达式所用的临时栈
        self.name = None #语句块的标识符
        self.type = None #结点的数据类型
        self.data = None #结点携带的数据
        self.begin = None #循环入口
        self.end = None #循环出口
        self.true = None #为真时的跳转位置
        self.false = None #为假时的跳转位置
    def prtNode(self):
        print('Node name:', self.name, ',type:', self.type, ',data:', self.data, ',code:',self.code)
        return

class Symbol:
    def __init__(self):
        self.name = None #符号的标识符
        self.type = None #类型
        self.size = None #占用字节数
        self.offset = None #内存偏移量
        self.place = None #对应的中间变量
        self.function = None #所在函数

class FunctionSymbol:
    def __init__(self):
        self.name = None #函数的标识符
        self.type = None #返回值类型
        self.label = None #入口处的标签
        self.params = [] #形参列表
        self.tempVar = [] #局部变量列表


class SemanticAnalyzer():
    def __init__(self):
        return


    


