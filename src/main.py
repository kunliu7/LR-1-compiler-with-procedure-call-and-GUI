# This Python file uses the following encoding: utf-8
import sys
#from PySide2.QtWidgets import QApplication, QMainWindow
from LR1Compiler import *

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *

class Ui_MainWindow(object):
    #def __init__(self):
    #    QMainWindow.__init__(self)
    #    self.setupUi(self)

    def setupUi(self, MainWindow, cfg, family, parseRst,tokens):
        self.tokens=None #tokens
        #self.parseRst=parseRst
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)

        self.MainWindow=MainWindow
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.resize(800, 600)


        #提示 代码
        self.label_code = QtWidgets.QLabel("输入代码：")



        '''index_codeWidget = QtWidgets.QWidget(MainWindow)
        #写代码的框
        self.textCode = QtWidgets.QTextEdit()
        #self.textCode.setGeometry(QtCore.QRect(330, 60, 401, 401))
        self.textCode.setObjectName("textCode")
        #inputProgram = self.textCode.text()
        #print(inputProgram)
        '''
        index_codeWidget = QtWidgets.QWidget(MainWindow)
        #写代码的框
        self.textCode = QtWidgets.QTextEdit(index_codeWidget)
        self.textCode.setObjectName("textCode")
        #self.textCode.setGeometry(QtCore.QRect(330, 60, 401, 401))
        label_rowIndex = QtWidgets.QLabel(index_codeWidget)
        label_rowIndex.setText("0\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n14\n15\n16\n17\n18\n19\n20\n21\n22\n23\n24\n25\n26\n27\n28\n29");
        hhbox = QHBoxLayout()           #横向布局
        hhbox.addWidget(label_rowIndex)    #把行号加入布局
        hhbox.addWidget(self.textCode)    #把文本框加入布局
        index_codeWidget.setLayout(hhbox)

        # 所有按钮的布局
        self.vboxcode = QVBoxLayout()
        self.vboxcode.addWidget(self.label_code)
        self.vboxcode.addWidget(index_codeWidget)

        #self.okButton = QPushButton(self.centralwidget)
        #self.okButton.setText('词法分析')
        #self.okButton.setSizePolicy(Fixed,Fixed);

        self.all4Button = QPushButton(self.centralwidget)
        self.all4Button.setText('语法分析+语义分析+中间代码生成')
        self.all4Button.setEnabled(True)

        button4widget = QtWidgets.QWidget(MainWindow)
        button4widget.setObjectName("button4widget")
        button4widget.resize(800, 600)

        self.GramButton = QPushButton(button4widget)
        self.GramButton.setText('语法分析结果')
        #self.GramButton.setStyleSheet("color: rgb(190,190,190)")
        self.GramButton.setEnabled(False)

        self.midCodeButton = QPushButton(button4widget)
        self.midCodeButton.setText('中间代码')
        self.midCodeButton.setEnabled(False)

        self.FuncButton = QPushButton(button4widget)
        self.FuncButton.setText('函数表')
        self.FuncButton.setEnabled(False)

        self.SignButton = QPushButton(button4widget)
        self.SignButton.setText('符号表')
        self.SignButton.setEnabled(False)

        self.objCodeButton = QPushButton(self.centralwidget)
        self.objCodeButton.setText('目标代码生成')
        self.objCodeButton.setEnabled(False)

        hhbox = QHBoxLayout()           #横向布局
        hhbox.addWidget(self.GramButton)    #把按钮加入布局
        hhbox.addWidget(self.midCodeButton)    #把按钮加入布局
        hhbox.addWidget(self.FuncButton)    #把按钮加入布局
        hhbox.addWidget(self.SignButton)    #把按钮加入布局

        button4widget.setLayout(hhbox)

        #self.gramButton.setSizePolicy(Fixed,Fixed);
        # 将按钮添加至布局
        #self.vboxcode.addWidget(self.okButton)
        self.vboxcode.addWidget(self.all4Button)
        self.vboxcode.addWidget(button4widget)
        self.vboxcode.addWidget(self.objCodeButton)

        # 将按钮和信号关联
        #self.okButton.clicked.connect(self.LexTest)
        self.all4Button.clicked.connect(self.GramTest)
        self.GramButton.clicked.connect(self.GramResTest)
        self.midCodeButton.clicked.connect(self.midResTest)
        self.FuncButton.clicked.connect(self.FuncResTest)
        self.SignButton.clicked.connect(self.SignResTest)
        self.objCodeButton.clicked.connect(self.objCodeTest)

        self.centralwidget.setLayout(self.vboxcode)

        #self.button.clicked.connect(self.prtTest)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        # 以上是GUI相关
        # 语法相关设置:
        os.chdir(os.path.dirname(sys.argv[0])) # 将工作路径改为该文件目录
        self.cfg = CFG()
        #self.cfg.readGrammerFile('C:\\Users\\95223\\Documents\\Compiling_Principle\\bhw1\\copy\\test2\\grammer_middle.txt')
        self.cfg.readGrammerFile('.\\grammer_final.txt')

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))

    # 语法分析+语义分析+中间代码生成
    def GramTest(self):
        self.cfg.getDotItems()
        self.cfg.calFirstSet()
        self.family = ItemSetSpecificationFamily(self.cfg)
        self.family.buildFamily()
        self.ana = SyntacticAnalyzer(self.cfg, self.family)  # 'S'不需要，要结束符#
        self.ana.getTables2()
        self.originCode = self.textCode.toPlainText()
        self.ana.isRecognizable2(self.originCode)

        # 以下是执行isRecognizable2后的结果
        '''
        self.ana.syntacticRst = True
        self.ana.syntacticErrMsg = "语法分析成功！"
        self.ana.semanticRst = True
        self.ana.semanticErrMsg = "语义分析成功！"
        '''

        if False == self.ana.syntacticRst:
            ErrorDialog = QMessageBox.question(self.MainWindow,
                                            "语法分析出错了！",
                                            self.ana.syntacticErrMsg,
                                            QMessageBox.Yes)
            return
        elif False == self.ana.semanticRst:
            ErrorDialog = QMessageBox.question(self.MainWindow,
                                            "语义分析出错了！",
                                            self.ana.semanticErrMsg,
                                            QMessageBox.Yes)
            return
        else:
            self.ana.saveMidCodeToFile()
            ErrorDialog = QMessageBox.information(self.MainWindow,
                                            "成功！",
                                            '语法分析和语义分析成功！请点击按钮查看中间代码、函数表、符号表\n中间代码已写入文件middleCodeFile.txt',
                                            QMessageBox.Yes)

        # 语法分析成功后结果
        self.parseRst = self.ana.getParseRst()

        self.GramButton.setEnabled(True)
        self.midCodeButton.setEnabled(True)
        self.FuncButton.setEnabled(True)
        self.SignButton.setEnabled(True)
        self.objCodeButton.setEnabled(True)
        # TODO: pxn，按下“语法分析”的按钮后，这三张表的按钮由灰变可选，点击后能查看以下三张表
        # 注：原先在点击'语法分析'按钮的时候，会直接弹出结果，现在变成点击按钮式的
        # 语义分析和中间代码生成成功后结果：
        # self.ana.middleCode = []
        # 其中元素为一个元组，也就是四元式，(operation, arg1, arg2, result)，如果是'_'则表示为空

        # self.ana.funcTable = []
        # 其中元素为FunctionSymbol，其声明在middle.py，所有成员都要显示，不一定所有成员都有值

        # self.ana.symbolTable = []
        # 其中元素为Symbol，其声明在middle.py，所有成员都要显示，不一定所有成员都有值


        # -------------- 以上是程序相关 ---------------------------------

    # 展示符号表分析结果
    def SignResTest(self):
        # -------------- 以下是GUI相关 ---------------------------------
       # print(self.ana.funcTable)

        GramDialog = QDialog(self.MainWindow)
        GramDialog.resize(900,600)
        table = QTableWidget(GramDialog)
        table.setColumnCount(6)
        table.setRowCount(len(self.ana.symbolTable))
        table.setHorizontalHeaderLabels(['符号的标识符', '类型', '占用字节数','内存偏移量','对应的中间变量','所在函数'])
        table.horizontalScrollBar().setStyleSheet("QScrollBar{background:transparent; height:10px;}"
                                                "QScrollBar::handle{background:lightgray; border:2px solid transparent; border-radius:5px;}"
                                                "QScrollBar::handle:hover{background:gray;}"
                                                "QScrollBar::sub-line{background:transparent;}"
                                                "QScrollBar::add-line{background:transparent;}");
        table.verticalScrollBar().setStyleSheet("QScrollBar{background:transparent; width: 10px;}"
                                                "QScrollBar::handle{background:lightgray; border:2px solid transparent; border-radius:5px;}"
                                                "QScrollBar::handle:hover{background:gray;}"
                                                "QScrollBar::sub-line{background:transparent;}"
                                                "QScrollBar::add-line{background:transparent;}");
        #table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        #table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        #table.setItem(0,0,QTableWidgetItem("111"))
        cnt_row=0
        for dir in self.ana.symbolTable:
            cnt_col=0;
            table.setItem(cnt_row,cnt_col,QTableWidgetItem(dir.name))
            cnt_col+=1
            table.setItem(cnt_row,cnt_col,QTableWidgetItem(dir.type))
            cnt_col+=1
            table.setItem(cnt_row,cnt_col,QTableWidgetItem(str(dir.size)))
            cnt_col+=1
            table.setItem(cnt_row,cnt_col,QTableWidgetItem(str(dir.offset)))
            cnt_col+=1
            table.setItem(cnt_row,cnt_col,QTableWidgetItem(dir.place))
            cnt_col+=1
            table.setItem(cnt_row,cnt_col,QTableWidgetItem(dir.function))
            cnt_row+=1



        hhbox = QHBoxLayout()           #横向布局
        hhbox.addWidget(table)    #把表格加入布局
        GramDialog.setLayout(hhbox)
        GramDialog.show()
    
    # 展示函数表分析结果
    def FuncResTest(self):
        # -------------- 以下是GUI相关 ---------------------------------
       # print(self.ana.funcTable)

        GramDialog = QDialog(self.MainWindow)
        GramDialog.resize(900,600)
        table = QTableWidget(GramDialog)
        table.setColumnCount(4)
        table.setRowCount(len(self.ana.funcTable))
        table.setHorizontalHeaderLabels(['函数的标识符', '返回值类型', '入口处的标签','形参列表'])
        table.horizontalScrollBar().setStyleSheet("QScrollBar{background:transparent; height:10px;}"
                                                "QScrollBar::handle{background:lightgray; border:2px solid transparent; border-radius:5px;}"
                                                "QScrollBar::handle:hover{background:gray;}"
                                                "QScrollBar::sub-line{background:transparent;}"
                                                "QScrollBar::add-line{background:transparent;}");
        table.verticalScrollBar().setStyleSheet("QScrollBar{background:transparent; width: 10px;}"
                                                "QScrollBar::handle{background:lightgray; border:2px solid transparent; border-radius:5px;}"
                                                "QScrollBar::handle:hover{background:gray;}"
                                                "QScrollBar::sub-line{background:transparent;}"
                                                "QScrollBar::add-line{background:transparent;}");
        #table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        #table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        #table.setItem(0,0,QTableWidgetItem("111"))
        cnt_row=0
        print(len(self.ana.funcTable))
        for dir in self.ana.funcTable:

            cnt_col=0;

            table.setItem(cnt_row,cnt_col,QTableWidgetItem(dir.name))
            cnt_col+=1

            table.setItem(cnt_row,cnt_col,QTableWidgetItem(dir.type))
            cnt_col+=1

            table.setItem(cnt_row,cnt_col,QTableWidgetItem(dir.label))
            cnt_col+=1

            table.setItem(cnt_row,cnt_col,QTableWidgetItem(str(dir.params)))
            cnt_row+=1



        hhbox = QHBoxLayout()           #横向布局
        hhbox.addWidget(table)    #把表格加入布局
        GramDialog.setLayout(hhbox)
        GramDialog.show()

    # 展示中间代码
    def midResTest(self):
        # -------------- 以下是GUI相关 ---------------------------------

        GramDialog = QDialog(self.MainWindow)
        GramDialog.resize(900,600)
        table = QTableWidget(GramDialog)
        table.setColumnCount(4)
        table.setRowCount(len(self.ana.middleCode))
        table.setHorizontalHeaderLabels(['operation', 'arg1', 'arg2','result'])
        table.horizontalScrollBar().setStyleSheet("QScrollBar{background:transparent; height:10px;}"
                                                "QScrollBar::handle{background:lightgray; border:2px solid transparent; border-radius:5px;}"
                                                "QScrollBar::handle:hover{background:gray;}"
                                                "QScrollBar::sub-line{background:transparent;}"
                                                "QScrollBar::add-line{background:transparent;}");
        table.verticalScrollBar().setStyleSheet("QScrollBar{background:transparent; width: 10px;}"
                                                "QScrollBar::handle{background:lightgray; border:2px solid transparent; border-radius:5px;}"
                                                "QScrollBar::handle:hover{background:gray;}"
                                                "QScrollBar::sub-line{background:transparent;}"
                                                "QScrollBar::add-line{background:transparent;}");
        #table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        #table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        #table.setItem(0,0,QTableWidgetItem("111"))
        cnt_row=0
        for dir in self.ana.middleCode:
            cnt_col=0;

            table.setItem(cnt_row,cnt_col,QTableWidgetItem(dir[cnt_col]))
            cnt_col+=1

            table.setItem(cnt_row,cnt_col,QTableWidgetItem(dir[cnt_col]))
            cnt_col+=1

            table.setItem(cnt_row,cnt_col,QTableWidgetItem(dir[cnt_col]))
            cnt_col+=1

            table.setItem(cnt_row,cnt_col,QTableWidgetItem(dir[cnt_col]))
            cnt_row+=1

        hhbox = QHBoxLayout()           #横向布局
        hhbox.addWidget(table)    #把表格加入布局
        GramDialog.setLayout(hhbox)
        GramDialog.show()

    # 展示语法分析结果
    def GramResTest(self):
        # -------------- 以下是GUI相关 ---------------------------------

        GramDialog = QDialog(self.MainWindow)
        GramDialog.resize(900,600)
        table = QTableWidget(GramDialog)
        #titles = ['type', 'row', 'col']
        table.setColumnCount(3)
        table.setRowCount(len(self.parseRst))
        table.setHorizontalHeaderLabels(['状态栈', '移动栈', '输入栈'])
        table.horizontalScrollBar().setStyleSheet("QScrollBar{background:transparent; height:10px;}"
                                                "QScrollBar::handle{background:lightgray; border:2px solid transparent; border-radius:5px;}"
                                                "QScrollBar::handle:hover{background:gray;}"
                                                "QScrollBar::sub-line{background:transparent;}"
                                                "QScrollBar::add-line{background:transparent;}");
        table.verticalScrollBar().setStyleSheet("QScrollBar{background:transparent; width: 10px;}"
                                                "QScrollBar::handle{background:lightgray; border:2px solid transparent; border-radius:5px;}"
                                                "QScrollBar::handle:hover{background:gray;}"
                                                "QScrollBar::sub-line{background:transparent;}"
                                                "QScrollBar::add-line{background:transparent;}");

        cnt_row=0
        for dir in self.parseRst:
            cnt_col=0;
            li = dir['stateStack']
            s = ""
            for item in li:
                s = s + str(item)+" "
            #label_type.append(s)
            table.setItem(cnt_row,cnt_col,QTableWidgetItem(s.strip("->")))
            cnt_col+=1

            li = dir['shiftStr']
            s = ""
            for item in li:
                s = s + str(item['type'])+" "
            table.setItem(cnt_row,cnt_col,QTableWidgetItem(s))
            cnt_col+=1

            li = dir['inputStr']
            s = ""
            for item in li:
                #print(s)
                s = s + str(item['type'])+" "
            table.setItem(cnt_row,cnt_col,QTableWidgetItem(s))
            cnt_row+=1

        hhbox = QHBoxLayout()           #横向布局
        hhbox.addWidget(table)    #把表格加入布局
        GramDialog.setLayout(hhbox)
        GramDialog.show()

    # 词法分析
    def LexTest(self):
        inputProgram = self.textCode.toPlainText()
        self.originCode = inputProgram
        self.tokens = self.cfg.genTokensFromInputBox(inputProgram)  # GUI!!!!!
        #self.originCode
        # 以上是程序相关 ---------------------------------
        # 以下是GUI相关 ---------------------------------
        self.all4Button.setEnabled(True)
        LexDialog=QDialog(self.MainWindow)
        LexDialog.resize(600, 400)

        table = QTableWidget(LexDialog)
        #titles = ['type', 'row', 'col']
        table.setColumnCount(4)
        table.setRowCount(len(self.tokens))
        table.setHorizontalHeaderLabels(['类型','值', '行', '列'])
        table.horizontalScrollBar().setStyleSheet("QScrollBar{background:transparent; height:10px;}"
                                                "QScrollBar::handle{background:lightgray; border:2px solid transparent; border-radius:5px;}"
                                                "QScrollBar::handle:hover{background:gray;}"
                                                "QScrollBar::sub-line{background:transparent;}"
                                                "QScrollBar::add-line{background:transparent;}");
        table.verticalScrollBar().setStyleSheet("QScrollBar{background:transparent; width: 10px;}"
                                                "QScrollBar::handle{background:lightgray; border:2px solid transparent; border-radius:5px;}"
                                                "QScrollBar::handle:hover{background:gray;}"
                                                "QScrollBar::sub-line{background:transparent;}"
                                                "QScrollBar::add-line{background:transparent;}");
        #table.setItem(0,0,QTableWidgetItem("111"))


        cnt_row=0
        for dir in self.tokens:
            cnt_col=0
            #v[1], v[0], QTableWidgetItem(str(list(v[2])[v[0]]))
            table.setItem(cnt_row,cnt_col,QTableWidgetItem(dir['type']))
            cnt_col=cnt_col+1
            table.setItem(cnt_row,cnt_col,QTableWidgetItem(dir['data']))
            cnt_col=cnt_col+1
            table.setItem(cnt_row,cnt_col,QTableWidgetItem(str(dir['row'])))
            cnt_col=cnt_col+1
            table.setItem(cnt_row,cnt_col,QTableWidgetItem(str(dir['colum'])))
            cnt_row=cnt_row+1
            #label_type.append(dir['type'])
            #label_col.append(str(dir['colum']))
            #label_row.append(str(dir['row']))

        #item = [(j, c,Example.data[c].values()) for j in range(len(Example.data)) for c in range(5)]


        hhbox = QHBoxLayout()           #横向布局
        hhbox.addWidget(table)    #把表格加入布局
        LexDialog.setLayout(hhbox)

        LexDialog.show()

    # 目标代码生成
    def objCodeTest(self):
        #self.getOriginCode()
        self.ocg = ObjectCodeGenerator(self.ana.middleCode, self.ana.symbolTable)
        self.ocg.genMips()
        self.mipsText = ''
        for code in self.ocg.mipsCode:
            self.mipsText += code + '\n'
        objCodeFile = open("objCodeFile.txt", "w+")
        objCodeFile.write(self.mipsText)
        objCodeFile.close()
        ErrorDialog = QMessageBox.information(self.MainWindow,
                                            "成功！",
                                            '目标代码生成成功！请点击OK查看目标代码\n目标代码已写入文件objCodeFile.txt',
                                            QMessageBox.Yes)
        codeDialog = QDialog(self.MainWindow)
        codeDialog.resize(900,600)
        hhbox = QHBoxLayout()
        objCodeTextBox = QTextEdit(codeDialog)
        #objCodeTextBox.setSizePolicy()
        hhbox.addWidget(objCodeTextBox)
        codeDialog.setLayout(hhbox)
        objCodeTextBox.setText(self.mipsText)
        codeDialog.show()
        return

    def getOriginCode(self):
        code = ''
        regNum = 26 - 7
        for i in range(regNum):
            c = chr(ord('a') + i) 
            code += 'int ' + c + ';\n'
        for i in range(regNum):
            c = chr(ord('a') + i) 
            code += c + '=' + str(i) + ';\n'
        print(code)
        sys.stdout.flush()
        return
            



if __name__ == "__main__":
    #print('?')
    '''
    cfg = CFG()
    cfg.readGrammerFile('C:/Users/95223/Documents/Compiler_Principle/bhw1/copy/test2/grammer_final.txt')
    #cfg.loadGrammer()
    #cfg.readGrammerJson('C:/Users/95223/Documents/Compiler_Principle/bhw1/copy/test2/withGUI1.0/g4.json')
    tokens = cfg.generate_tokens('C:/Users/95223/Documents/Compiler_Principle/bhw1/copy/test2/test_final.txt')  # GUI!!!!!
    #print(tokens)
    cfg.getDotItems()
    #cfg.prtGrammer()
    cfg.calFirstSet()
    #cfg.prtFirstSet()
    family = ItemSetSpecificationFamily(cfg)
    family.buildFamily()
    #family.prtFamily()
    ana = SyntacticAnalyzer(cfg, family)  # 'S'不需要，要结束符#
    ana.getTables2()
    #ana.getTables()
    #ana.prtTables2()
    #ana.prtTables()
    #print(tokens)
    #print(ana.isRecognizable('baab'))
    #print(ana.isRecognizable2('baab'))
    #print(ana.isRecognizable2('bz'))
    #print(ana.isRecognizable('bz'))
    print(ana.isRecognizable2(tokens))
    #print(ana.isRecognizable(tokens))
    parseRst = ana.getParseRst()  # GUI !!!!!
    #print(parseRst)
    '''

    # look here!!!!!!tokens
    #print(tokens)

    app = QtWidgets.QApplication(sys.argv)
    mainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(mainWindow, None, None, None, None)
    #ui.setupUi(mainWindow, none, family, parseRst, tokens)
    mainWindow.show()



    sys.exit(app.exec_())


