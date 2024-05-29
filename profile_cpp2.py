
class SingleLine:
	def __init__(self, line_number, txt):
		self.line_number = line_number
		self.txt = txt
		self.base_txt = txt

class FunctionLine:
	def __init__(self, line_number, txt):
		self.line_number = line_number
		self.txt = txt
		self.base_txt = txt

class Function:
	def __init__(self, first_line_number, last_line_number, longest_line_number):
		self.first_line_number = first_line_number
		self.last_line_number = last_line_number
		self.longest_line_number = longest_line_number

class File:
	def __init__(self, lines, functions):
		self.lines = lines
		self.functions = functions

file = File([SingleLine(2, " al lo "), FunctionLine(3, "aluile")], [Function(1, 2, 3), Function(1, 2, 3)])

a = f"""
	functions_t functions{{ {", ".join(f"function_t({function.first_line_number}, {function.last_line_number}, {function.longest_line_number})" for function in file.functions)} }};
"""
print(a)