#include "profile.hpp"

namespace {profile_namespace} {{

namespace {filename} {{

	// lines[0] is a dummy since line numbers start at 1
	// all lines that were not profiled will have an empty base_txt and a line_number of 0
	lines_t lines{{ std::make_unique<single_line_t>(0, ""), {", ".join(f'std::make_unique<{"single_line_t" if isinstance(line, SingleLine) else "function_line_t"}>({line.line_number}, "{line.base_txt}")' for line in file.lines)} }};
	functions_t functions{{ {", ".join(f"function_t({function.first_line_number}, {function.last_line_number}, {function.longest_line_number})" for function in file.functions)} }};
	files[{filename}] = file_t{{lines, functions}};

}}

}}