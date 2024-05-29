#include "profile.hpp"

namespace {profile_namespace} {{

std::vector<std::regex> ignore_patterns {{
	{',\n'.join(ignore_patterns)}
}};

bool anyMatch(const std::string& txt, const std::vector<std::regex>& patterns) {{
	for (const auto& pattern : patterns) {{
		if (std::regex_search(txt, pattern)) {{
			return true;
		}}
	}}
	return false;
}}

file_t::file_t(lines, functions)
	: lines(lines), functions(functions) {{
	for (const auto& line : lines) {{
		line.file = this;
	}}
	for (const auto& function : functions) {{
		function.file = this;

		long longest_line_length = lines[function.longest_line_number].length();
		function.ignore_line_prefix = std::string({len(start_chrono_macro_name)} + 1 + longest_line_length + 1 + {nb_space_line_prefix}, " ");
		function.ignore_line_suffix = "";
		std::ostringstream oss;
		for (long line_number = function.first_line_number; line_number <= function.last_line_number; line_number++) {{
			auto& line = lines[line_number];
			line.function = function;
			
			if (line.ignore) {{
				line.prefix = function.ignore_line_prefix;
				line.suffix = function.ignore_line_suffix;
			}} else {{
				oss << std::setw(longest_line_length) << std::right << line_number;
				std::string aligned_line_number = oss.str();
				line.prefix = {start_chrono_macro_name} + "(" + aligned_line_number + ")" + std::string({nb_space_line_prefix}, " ");
				line.suffix = std::string(longest_line_length - line.base_txt.length() + {nb_space_line_suffix}, " ") + {top_chrono_macro_name} + "(" + aligned_line_number + ")";
				oss.str("");
			}}
		}}
	}}
}}

function_t::function_t(long first_line_number, long last_line_number, long longest_line_number)
	: first_line_number(first_line_number), last_line_number(last_line_number), longest_line_number(longest_line_number),
	nb_call(0), hits(0), time(0), per_hit(0) {{
}}

line_t::line_t(long line_number, std::string txt)
	: line_number(line_number), hits(0), time(0), per_hit(0), prefix(""), suffix("") {{
	// this is importat so that this.txt.length() is rightfully the number of characters
	// this would not be true with tabs
	txt = std::regex_replace(txt, tab_regex("\t"), spaces({tab_width}, ' '));
	base_txt = txt;
}}

{single_line_class_name}::{single_line_class_name}(long line_number, std::string txt)
	: line_t(line_number, txt) {{
}}

{function_line_class_name}::{function_line_class_name}(long line_number, std::string txt)
	: line_t(line_number, txt),
	hits_percentage(0), time_percentage(0), per_hit_percentage(0) {{
	ignore = anyMatch(txt, ignore_patterns);
}}

}}