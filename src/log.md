## 11/27 2027

* 一直使用空产生式规约：
block
	{ statementChain }
	#
statementChain
	$
	statement statementChain
	#
statement
	InterDeclaration
	ifStatement
	whileStatement
	returnStatement
	assignStatement
	#
InterDeclaration
	$
	InterVariableDeclaration InterDeclaration
	#
InterVariableDeclaration
	typeSpecifier id ;
	#

* 改成这个就ok了：
block
	{ statementChain }
	#
statementChain
	$
	statement statementChain
	#
statement
	declaration
	ifStatement
	whileStatement
	returnStatement
	assignStatement
	#
declaration
	typeSpecifier id ;
	declareFunction
	#