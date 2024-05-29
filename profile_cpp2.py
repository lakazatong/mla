
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
		self.filename = "mla"

file = File([SingleLine(2, " al lo "), FunctionLine(3, "aluile")], [Function(1, 2, 3), Function(1, 2, 3)])

a = f"""
	""yo""
"""
# print(a)

content = ""

# ----------------------------------------------------------------------
# parameters

profile_namespace = "Profiled"

# parameters
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# profile.hpp

profile_hpp = f"""

"""

# profile.hpp
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# profile.cpp

profile_hpp = f"""

"""

# profile.cpp
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# profile_{filename}.cpp

with open("profile_{filename}.cpp", "r") as f:
	content = f.read()

profile_filename_cpp = lambda file: content.format(profile_namespace=profile_namespace, file_filename=file.filename)

# profile_{filename}.cpp
# ----------------------------------------------------------------------

print(profile_filename_cpp(file))

exit(0)

# string to put before functions / lines to add profiling to
profile_function_pattern = re.compile(r"\/\/ @profile\s+function\s*\r?\n")
profile_line_pattern = re.compile(r"\/\/ @profile\s+line\s*\r?\n")
# lines to ignore
ignore_patterns = [
	re.compile(r"^\s*[{}]+\s*$"), # ignore only brackets
	re.compile(r"^\s*//(?:a|[^a])*$"), # ignore single line comments
	re.compile(r"^\s*return;\s*$") # ignore empty returns
]
# line reports
report_line_pattern = re.compile(rf"\/\/ {report_line_macro_name}\((\d+)\)")
# function reports (any character is captured, the function name check will be performed after)
report_function_pattern = re.compile(rf"\/\/ {report_function_macro_name}\(((?:a|[^a])+?)\)")
# chrono include
# a = re.compile(r"#include <chrono>")

def main():
	if len(sys.argv) < 2:
		print("provide cpp files")
		return

	for file_path in sys.argv[1:]:
		handle_file_path(file_path, file_path.split('.')[0] + '_profiled.cpp')

if __name__ == "__main__":
	main()
