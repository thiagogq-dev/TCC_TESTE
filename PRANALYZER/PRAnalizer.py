import re

class PRAnalizer():
	def __init__(self, language):
		self.language = language
		self.possibilidades = {}

		if(language == "Python"):
			self.possibilidades = {
				# '.*def.*\(.*\)\:'		: 'functions',
				# '.*class.*\(.*\)\:'		: 'class',
				'.*assert.*\(.*'		: 'tests',  #olhar só esse
				'.*expect.*\(.*'		: 'tests',  #olhar só esse
				'.*import .*'			: 'imports', #olhar só esse
				'..*from .*import .*'	: 'imports', #olhar só esse
				'[\-|\+]\s{0,}#.*'		: 'comments',
				'[\-|\+]\s{0,}""".*"""'		: 'comments',
				"[\-|\+]\s{0,}'''.*'''"		: 'comments',
			}

		if(language == "JAVA"):
			self.possibilidades = {				
				'.*assert.*\(.*'	: 'tests', 

				'.*import .*\;': 'imports',

				'[\-|\+]\s{0,}#.*'		: 'comments',
				'[\-|\+]\s{0,}\/\*\*.*'	: 'comments',
				'[\-|\+]\s{0,}\*\/.*'	: 'comments',
				'[\-|\+]\s{0,}\/\/.*' 	: 'comments',
			}

		if(language == "C"):
			self.possibilidades = {
				'.*assert.*\(.*'	: 'tests', 
				'.*\#include.*\.h'	: 'imports', 
				
				'[\-|\+]\s{0,}\/\*.*\*\/'		: 'comments',
				'[\-|\+]\s{0,}\/\/.*'			: 'comments',
			}

		if(language == "C++"):
			self.possibilidades = {
				'.*assert.*\(.*'	: 'tests', 
				'.*TEST_EQUAL\(.*'	: 'tests', 
				'.*import .*\;'		: 'imports',
				
				'.*[\-|\+]\s{0,}\/\*.*\*\/'		: 'comments',
				'[\-|\+]\s{0,}\/\/.*'			: 'comments',
			}

		if(language == "C#"):
			self.possibilidades = {
				'.*assert.*\(.*'	: 'tests', 
				'.*Assert.*\(.*'	: 'tests', 
				'.*import .*\;'		: 'imports',
				'.*using .*\;'		: 'imports',

				'.*[\-|\+]\s{0,}\/\*.*\*\/'		: 'comments',
				'[\-|\+]\s{0,}\/\/.*'			: 'comments',
			}


# ----
		if(language == "Javascript"):
			self.possibilidades = {
				'.*assert.*\(.*'	: 'tests', 
				'.*expect\(.*\).*'	: 'tests', 
				'.*import .*\;'		: 'imports',
				
				'.*[\-|\+]\s{0,}\/\*.*\*\/'		: 'comments',
				'[\-|\+]\s{0,}\/\/.*'			: 'comments',
			}

		if(language == "Ruby"):
			self.possibilidades = {
				'.*assert.*'	 : 'tests', 
				'.*require .*\;' : 'imports',
				
				'.*[\-|\+]\s{0,}\/\*.*\*\/'		: 'comments',
				'[\-|\+]\s{0,}\/\/.*'			: 'comments',
			}


	def verify(self, text):
		tipo = "code"

		if (len(text.strip()[1::]) == 0): 
			tipo = 'whiteLines'

		
		for expressao in self.possibilidades:
			validador 	= re.compile(expressao)
			
			if validador.match(text.strip()):
				tipo = self.possibilidades[expressao]


		return tipo



	def checkModifierType(self, text):
		if(len(text) >= 1):
			if(text.strip()[0] == "-"):
				return 'removed'

			if(text.strip()[0] == "+"):
				return 'added'
		else:
			return 'others'
		return 'others'

	def checkIfModifier(self, text):
		if(len(text) >= 1):
			if(text.strip()[0] == "-" or text.strip()[0] == "+"):
				return True
		else:
			return False

	def retornaEstrutura(self):
		return {
			'functions': {
				'removed':0,
				'added':0,
				'others':0,
			},
			'tests': {
				'removed':0,
				'added':0,
				'others':0,
			},
			'class': {
				'removed':0,
				'added':0,
				'others':0,
			},
			'code': {
				'removed':0,
				'added':0,
				'others':0,
			},

			'imports': {
				'removed':0,
				'added':0,
				'others':0,
			},

			'comments': {
				'removed':0,
				'added':0,
				'others':0,
			},

			'whiteLines': {
				'removed':0,
				'added':0,
				'others':0,
			},

			'all': {
				'removed':0,
				'added':0,
				'others':0,
			},

		}