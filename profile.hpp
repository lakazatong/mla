#ifndef PROFILE_HPP
#define PROFILE_HPP

#include <vector>
#include <regex>
#include <string>

#define line_t line_t
#define lines_t std::vector<line_t>

#define single_line_t {single_line_class_name}
#define single_lines_t std::vector<single_line_t>

#define function_line_t {function_line_class_name}
#define function_lines_t std::vector<function_line_t>

#define function_t function_t
#define functions_t std::unordered_map<std::string, function_t>

#define file_t file_t
#define files_t std::vector<file_t>

namespace {profile_namespace} {{

std::vector<std::regex> ignore_patterns({len(ignore_patterns)});

bool anyMatch(const std::string& txt, const std::vector<std::regex>& patterns);

struct file_t {{
public:
	// lines[0] is a dummy since line numbers start at 1
	lines_t lines;
	functions_t functions;

	file_t(lines_t lines, functions_t functions);
}}

struct function_t {{
public:
	// first_line_number == last_line_number if there is 1 line
	// first_line_number == last_line_number == line of the function declaration if there is 0 line
	long first_line_number;
	long last_line_number;

	long nb_call;
	// totals
	long hits;
	double time;
	double per_hit;

	file_t file;

	function_t(file_t file, long first_line_number, long last_line_number);
}}

struct line_t {{
public:
	long line_number;
	long hits;
	double time; // total time spent on this line
	double per_hit; // time spent every hit in average

	std::string prefix;
	std::string base_txt;
	std::string txt;
	std::string suffix;

	file_t file;

	line_t(file_t file, std::string txt);
}}

struct single_line_t : public line_t {{
public:
	single_line_t(std::string txt, long line_number);
}}

struct function_line_t : public line_t {{
public:
	double hits_percentage;
	double time_percentage;
	double per_hit_percentage; // kind of weird to think about

	bool ignore;

	function_t function;

	function_line_t(function_t function, std::string txt);
}}

std::unordered_map<std::string, file_t> files({len(files)});

}}
#endif /* PROFILE_HPP */