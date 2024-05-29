#include "profile_{filename}.hpp"
namespace {namespace_name} {{

/*
	long first_line_number;
	long last_line_number;

	long nb_call;
	// totals
	long hits;
	double time;
	double per_hit;
*/
{function_class_name}::{function_class_name}() {{

}}

{line_class_name}::{line_class_name}(std::string txt)
	: line_number(0), hits(0), time(0), per_hit(0), prefix(""), suffix("") {{
	// this is importat so that len(this.txt) is rightfully the number of characters
	// this would not be true with tabs
	txt = std::regex_replace(txt, tab_regex("\t"), spaces({tab_width}, ' '));
	base_txt = txt;
}}

{single_line_class_name}::{single_line_class_name}(std::string txt, long line_number)
	: {line_class_name}(txt), line_number(line_number) {{
	lines[line_number] = this;
}}

{function_line_class_name}::{function_line_class_name}(std::string txt, bool ignore)
	: {line_class_name}(txt), hits_percentage(0), time_percentage(0), per_hit_percentage(0) {{
	ignore = anyMatch(txt, ignore_patterns);
}}

}}