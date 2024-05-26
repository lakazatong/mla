import sys, re, shutil

# ONLY WORK IF
# // @profile is the line just above the function declaration
# the function declaration is one only one line

# parameters
nb_space_line_prefix = 10
nb_space_line_suffix = 30
tab_width = 4
preamble_spacing = 2

# string to put before functions to add profiling to
profile_pattern = re.compile(r"\/\/ @profile\s*\r?\n")
# lines to ignore
ignore_bracket_line_pattern = re.compile(r'^\s*[{}]+\s*$')
ignore_comment_line_pattern = re.compile(r'^\s*//(?:a|[^a])*$')
ignore_empty_return_line_pattern = re.compile(r'^\s*return;\s*$')

max_line_number = 0
max_line_width = 0

define_chrono_macro_name = "DEF_CHRONO"
open_chrono_macro_name = "OPEN_CHRONO"
close_chrono_macro_name = "CLOSE_CHRONO"

class File:
	def __init__(self, content, functions):
		self.content = content
		self.functions = functions
		self.preamble = ""

	def add_profiling(self):
		self.preamble = f"\n#define {define_chrono_macro_name}(chrono_id) std::chrono::time_point<std::chrono::high_resolution_clock> st##chrono_id; double stet##chrono_id = 0; double stet##chrono_id##_hits = 0;\n#define {open_chrono_macro_name}(chrono_id) st##chrono_id = std::chrono::high_resolution_clock::now();\n#define {close_chrono_macro_name}(chrono_id) std::chrono::duration<double, std::milli> elapsed##chrono_id = std::chrono::high_resolution_clock::now() - st##chrono_id; stet##chrono_id += elapsed##chrono_id##.count(); stet##chrono_id##_hits++;\n"
		line_number_offset = self.preamble.count("\n") + len(self.functions) + preamble_spacing
		for f in self.functions:
			f.update_line_numbers(line_number_offset)
			self.preamble += f"\n{" ".join(f"{define_chrono_macro_name}({line.line_number})" for line in f.lines if not line.ignore)}"
		self.preamble += "\n" * preamble_spacing
		for f in self.functions: f.add_profiling()

	def write_to(self, path):
		with open(path, "w", encoding="utf-8") as f:
			f.write(str(self))

	def __repr__(self, only_functions=False):
		if only_functions:
			return '\n'.join(str(f) for f in sorted(self.functions, key=lambda f: f.start_index))
		r = self.preamble
		last_index = 0
		for f in sorted(self.functions, key=lambda f: f.start_index):
			r += f"{self.content[last_index:f.start_index]}{f}"
			last_index = f.end_index + 1
		return (r + self.content[last_index:]).replace(u'\ufeff', '')

get_line_prefix = lambda given_line_number = None: f"{open_chrono_macro_name}({(max_line_number if given_line_number == None else given_line_number):>{len(str(max_line_number))}}){" " * nb_space_line_prefix}" 

class Function:
	def __init__(self, decl, lines, start_index, end_index, first_body_line_number):
		self.decl = decl
		# self.first_body_line_number = first_body_line_number
		line_number = first_body_line_number
		for line in lines:
			line.set_line_number(line_number)
			line_number += 1
		self.lines = lines
		# in original file, correspond to the very next character after the profile_pattern match
		# and the last } index
		self.start_index, self.end_index = start_index, end_index
		self.closing = "\n}"

	def add_profiling(self):
		self.decl = f"{" " * len(get_line_prefix())}{self.decl}\n"
		# max_line_width = max(len(f"{get_line_prefix(line.line_number)}{line.txt}") for line in self.lines)
		for line in self.lines:
			line.add_profiling()
		self.closing = f"\n{" " * len(get_line_prefix())}" + "}"

	def update_line_numbers(self, line_number_offset):
		for line in self.lines:
			line.line_number += line_number_offset

	def __repr__(self):
		return f"{self.decl}{"\n".join(line.txt for line in self.lines)}{self.closing}"

	def __len__(self):
		return len(self.__repr__())

class Line:
	def __init__(self, ignore, txt):
		self.ignore = ignore
		self.txt = txt.replace("\t", " " * tab_width)
		self.line_number = 0

	def set_line_number(self, line_number):
		global max_line_number, max_line_width
		self.line_number = line_number
		if line_number > max_line_number:
			max_line_number = line_number
		n = len(f"{get_line_prefix(self.line_number)}{self.txt}")
		if n > max_line_width:
			max_line_width = n

	def add_profiling(self):
		self.txt = f"{" " * len(get_line_prefix())}{self.txt}" if self.ignore else f"{get_line_prefix(self.line_number)}{self.txt}{" " * (max_line_width - (len(f"{get_line_prefix(self.line_number)}{self.txt}")) + nb_space_line_suffix)}{close_chrono_macro_name}({self.line_number})"

	def __repr__(self):
		return self.txt

	def __len__(self):
		return len(self.__repr__())

def function_body_to_lines(function_body):
	return [
		Line((
				ignore_bracket_line_pattern.match(line)
				or ignore_comment_line_pattern.match(line)
				or ignore_empty_return_line_pattern.match(line)
			) != None,
			line
		)
		for line in function_body.replace('\r\n', '\n').split('\n')[1:-1]
	]

def handle_file_path(original_file_path, working_file_path):
	shutil.copyfile(original_file_path, working_file_path)
	with open(working_file_path, 'r', encoding='utf-8') as file:
		content = file.read()
		matches = [match for match in profile_pattern.finditer(content)]
		if len(matches) == 0:
			print(f"found no match in {original_file_path}")
			return
		print(f"found match in {original_file_path}")
		functions = []
		for match in matches:
			start_index, end_index = match.end(), 0
			function = None
			N, K = 0, 0
			for i in range(start_index, len(content)):
				if content[i] == '{':
					if N == 0:
						K = i + 1
					N += 1
				elif content[i] == '}':
					N -= 1
					if N == 0:
						function = Function(content[start_index:K],
											function_body_to_lines(content[K:i]),
											start_index, i, content[:start_index].count('\n') + 2)
						break
			
			if function == None:
				raise ValueError("Mismatched brackets")
			functions.append(function)
		file = File(content, functions)

	file.add_profiling()
	file.write_to(working_file_path)

def main():
	if len(sys.argv) < 2:
		print("provide cpp files")
		return

	for file_path in sys.argv[1:]:
		handle_file_path(file_path, file_path.split('.')[0] + '_profiled.cpp')

if __name__ == "__main__":
	main()
