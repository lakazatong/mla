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
}}

function_t::function_t(file_t file, long first_line_number, long last_line_number)
	: first_line_number(first_line_number), last_line_number(last_line_number),
	nb_call(0), hits(0), time(0), per_hit(0), file(file) {{
	// function lines' line numbers are deduced
	for (long line_number = first_line_number; line_number <= last_line_number; line_number++) {{
		lines[line_number].line_number = line_number;
	}}
}}

line_t::line_t(std::string txt)
	: line_number(0), hits(0), time(0), per_hit(0), prefix(""), suffix("") {{
	// this is importat so that this.txt.length() is rightfully the number of characters
	// this would not be true with tabs
	txt = std::regex_replace(txt, tab_regex("\t"), spaces({tab_width}, ' '));
	base_txt = txt;
}}

{single_line_class_name}::{single_line_class_name}(std::string txt, long line_number)
	: line_t(txt), line_number(line_number) {{
	files[{filename}].lines[line_number] = this;
}}

{function_line_class_name}::{function_line_class_name}(std::string txt)
	: line_t(txt), hits_percentage(0), time_percentage(0), per_hit_percentage(0) {{
	ignore = anyMatch(txt, ignore_patterns);
}}

}}