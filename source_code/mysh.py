import sys,os,time

# VariableManager manages all the shell variables when execute mysh.py
class VariableManager:
	def __init__(self):
		# variable PS is predefined to '$'
		self.variables = {'PS': '$'}

	# Return variable's value named by variable_name, if variable_name
	# doesn't exist, return None.
	def get_value_by_name(self, variable_name):
		return self.variables.get(variable_name, None)
		
	def add(self, name, value):
		self.variables[name] = value
	
	def keys(self):
		return self.variables.keys()

	def remove(self, key):
		if key in self.variables.keys():
			del self.variables[key]

variable_manager = VariableManager()

# Emulate one single command.
class BuiltIn:
	history_list = [os.getcwd()]
	def __init__(self,  command_name,  args):
		self.command_name = command_name
		self.args = args
		self.commands = {
			'exit': self.do_exit, 	'changedir': self.do_changedir, 
			'say':self.do_say,  	'showdir': self.do_showdir,
			'cdn': self.do_cdn, 	'historylist': self.do_historylist,
			'show': self.do_show, 	'set':self.do_set, 
			'unset':self.do_unset, 	'sleep': self.do_sleep}

	def is_builtin(command):
		#return true or false
		return command in [
			'exit', 'say', 'changedir', 'showdir', 'historylist', 
			'cdn', 'show', 'set', 'unset', 'sleep'] #return true or false

	def do_exit(self):
		print('Goodbye!')
		quit()
	
	def do_say(self):
		if not len(self.args): #check length
			print()
		else:
			result = ''
			for i,arg in enumerate(self.args):
				if arg == None:
					continue
				result += arg +" "
			#strip the last space at the end
			print(result.strip())
	def do_changedir(self):
		dest = ''
		if not len (self.args): # directory not specified
			dest = variable_manager.get_value_by_name("HOME")
			if not dest:
				# print("Home not exits")
				return

		else:
			dest = self.args[0]
			if dest[0] != '/':  # Absolute path
				cur = os.getcwd()
				dest = cur + '/' + dest
		if os.path.exists(dest):
			os.chdir(dest)
			self.history_list.append(os.getcwd())
		else:
			# print("Path not exists!")
			return

	def do_showdir(self):
		print(os.getcwd())
		

	def do_historylist(self):
		#reverse print
		for i,e in enumerate(self.history_list[::-1]):
			print(str(i) + ": " + e)

	def do_cdn(self):
		n = 0
		if len(self.args):
			n = int(self.args[0])
			# change value of n if it is given
		if n < 0 or n >= len(self.history_list):
			# chech if the n is legit in the range
			print("n: " + str(n) + " is out of range.")
			return
		
		for i,e in enumerate(BuiltIn.history_list[::-1]):
			#remove all the directories earlier in the list 
			if i < n:
				self.history_list.remove(e)
			if i == n:
				os.chdir(e)
				
	def do_show(self):
		if len(self.args):
			for fname in self.args:
			#	print("FILE: " + fname)
				try:
					f = open(fname, 'r')
					print(f.read(), end = '')
					f.close()
				except Exception:
					pass
		else:
			try:
				while True:
					s = input() #userinput
					print(s)
			except EOFError:
				pass

	def do_set(self):
		if not len(self.args):
			# If no arguments are given, print all variables which are currently defined, in lexicographical order
			keys = sorted(list(variable_manager.keys()), key = str.lower) #reverse dic keys
			for item in keys:
				value = variable_manager.get_value_by_name(item)
				print(item + "="+ value)
		else:
			# add variable and value to the dictionary
			name = self.args[0]
			value = ''
			if len(self.args) > 1:
				for i,self.arg in enumerate(self.args[1:]):
					try:
						value = value + self.arg + ' '
					except TypeError:
						value = ""
			if name == None:
				if value.strip() != "":
					name = value.strip()
					value = ""
				else:
					return
			variable_manager.add(name, value.strip())
	
	def do_unset(self):
		# remove the value by key
		if len(self.args): # check if no value given
			variable_manager.remove(self.args[0])
		else:
			print("please tell me what you want to unset")
	
	def do_sleep(self):
		if not len(self.args): # check if no value given
			print("Need a value!")
			return
		n = int(self.args[0])
		time.sleep(n)
	
	def Buildin_execute(self):
		func = self.commands[self.command_name]
		return func() # will execute do_someing()


# Manage how commands executes, such as redirection and piping... 
class Repipe:
	# Duplicate the file at stdin/stdout and save to variable
	default_stdin = None
	default_stdout = None
	def __init__(self,stdin,stdout):
		self.default_stdin = stdin
		self.default_stdout = stdout
	
	def redirction(self,command):
		tokens = command.split()
		cmd = tokens[0]

		if len(cmd)==1:
			args = ['']
		else:
			args = tokens[1:]
		if '>' in args:
			i = args.index('>')
			if i+1 >= len(args):
				print("A filename must follow the character >")
			else:
				outf = open(args[i+1].strip(),'w')
				del args[i:i+2]
				os.dup2(outf.fileno(),sys.stdout.fileno())

		if '<' in args:
			i = args.index('<')
			if i+1 >= len(args):
				print("A filename must follow the character <")
			else:
				if not os.path.isfile(args[i+1].strip()):
					print("No file found")
					return
				inf = open(args[i+1].strip(),'r')
				del args[i:i+2]
				os.dup2(inf.fileno(),sys.stdin.fileno())

		if BuiltIn.is_builtin(cmd): #return true or false
			c = BuiltIn(cmd, args)
			c.Buildin_execute()
		else:
			new_tokens = ('%s %s' % (cmd,' '.join(args))).split()
			if not os.path.exists(cmd):
				print('Unable to execute %s' % cmd)
			else:
				if not os.fork():
					os.execv(cmd,new_tokens)
				else:
					os.wait()

	def pipe(self, command):
		# first search for '|'	
		if '|' in command:
			pidx = command.index('|')
			left = command[:pidx].strip()
			right = command[pidx+1:].strip()

			pi = os.pipe() #0 = read 1 = write
			pid = os.fork()
			if pid==0: #child
				os.close(pi[0])
				os.dup2(pi[1],sys.stdout.fileno())
				self.pipe(left) #recursion
				os._exit(0)
			else: #parent
				os.waitpid(pid,0)
				os.close(pi[1])
				os.dup2(pi[0],sys.stdin.fileno())
				self.pipe(right) #recursion
		else:
			self.redirction(command)

class Execute:
	repipe = None
	filelist = None
	def __init__(self,file = None):
		self.repipe = Repipe(os.dup(sys.stdin.fileno()),os.dup(sys.stdout.fileno()))
		self.filelist = self.filetolist(file) # will return None if file == None
	def preprocess(self,tokens): # Convert $-prefixed token to value of an environment variable
		processed_token = []
		for token in tokens:
		# Convert $-prefixed token to value of an environment variable
			if token.startswith('$') and len(token) > 1:
				value = variable_manager.get_value_by_name(token[1:])
				if value != None:
					processed_token.append(value) #change $value
				else:
					processed_token.append("") # not find replace by empty string
			else:
				processed_token.append(token)
		return ' '.join(processed_token).strip() #return string

	def filetolist(self,file):
		if file == None:
			return
		f = open(file,'r')
		lines = f.readlines()
		temp = []
		for i,e in enumerate(lines):
			if i == 0 and e.strip() == "": #skip first invaild line in the file
				continue
			elif i > 0:
				if lines[i].strip() == "" and not lines[i-1].strip().endswith("\\") : #skip rest of invaild line in the file
					continue
			temp.append(e.strip())
		return temp
	
	def shell_loop(self):
		# variable_manager = VariableManager()
		fileindex = 0
		while True:
			if self.filelist != None:
				if fileindex == len(self.filelist):
					break
			if self.filelist == None:
				value = variable_manager.get_value_by_name('PS')
				if value != None:
					print(value,end=' ')
				else:
					print("$", end=" ") #default is $ if no PS value.
			command = ''
			while True:
				if self.filelist == None:
					try:
						line = input().strip() # Read command input
					except EOFError:
						quit()
				else:
					line = self.filelist[fileindex]
				command += line
				if not len(line) or line[-1] != '\\':
					break
				if self.filelist == None:
					print('> ', end = '')
				command = command[:-1]
				fileindex += 1		
			if len(command):
				self.repipe.pipe(self.preprocess(command.strip().split())) # (e.g. convert $<env> into environment value) and Execute the comman
				# Restore the stdin stdout
				os.dup2(self.repipe.default_stdin, sys.stdin.fileno())
				os.dup2(self.repipe.default_stdout, sys.stdout.fileno())
				fileindex += 1

if __name__ == "__main__":
	if len(sys.argv) == 1:
		Execute().shell_loop()
	elif len(sys.argv) == 2:
		Execute(sys.argv[1]).shell_loop()
