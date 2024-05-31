#ifndef PROFILE_HPP
#define PROFILE_HPP

#include <vector>
#include <regex>
#include <string>
#include <chrono>
#include <unordered_map>

#define line_t {line_class_name}
#define lines_t std::vector<line_t>

#define single_line_t {single_line_class_name}
#define single_lines_t std::vector<single_line_t>

#define function_line_t {function_line_class_name}
#define function_lines_t std::vector<function_line_t>

#define function_t {function_class_name}
#define functions_t std::unordered_map<std::string, function_t>

#define file_t {file_class_name}
#define files_t std::vector<file_t>

// #define _CONCAT(a, b) a ## b
#define CONCAT(a, b) _CONCAT(a, b)
#define {define_chrono_macro_name}(line_number) std::chrono::time_point<std::chrono::high_resolution_clock> start##line_number; std::chrono::time_point<std::chrono::high_resolution_clock> top##line_number; double total##line_number = 0; long hits##line_number = 0;
#define {start_chrono_macro_name} CONCAT(start, __LINE__) = std::chrono::high_resolution_clock::now();
#define {top_chrono_macro_name} CONCAT(top, __LINE__) = std::chrono::high_resolution_clock::now(); std::chrono::duration<double, std::milli> CONCAT(elapsed, __LINE__) = CONCAT(top, __LINE__) - CONCAT(start, __LINE__); CONCAT(total, __LINE__) += CONCAT(elapsed, __LINE__).count(); CONCAT(hits, __LINE__)++; CONCAT(start, __LINE__) = CONCAT(top, __LINE__);

namespace {profile_namespace} {{

// fwd
struct line_t;
struct function_t;
struct file_t;

struct file_t {{
public:
	// lines[0] is a dummy since line numbers start at 1
	lines_t lines;
	functions_t functions;

	file_t(lines_t lines, functions_t functions);
}};

struct function_t {{
public:
	file_t file;

	long first_line_number;
	long last_line_number;
	long longest_line_number;

	long nb_call;
	// totals
	long hits;
	double time;
	double per_hit;

	std::string ignore_line_prefix;
	std::string ignore_line_suffix;

	function_t(long first_line_number, long last_line_number, long longest_line_number);
}};

struct line_t {{
public:
	file_t file;

	long line_number;
	long hits;
	double time; // total time spent on this line
	double per_hit; // time spent every hit in average

	std::string prefix;
	std::string base_txt;
	std::string txt;
	std::string suffix;

	line_t(long line_number, std::string txt);
}};

struct single_line_t : public line_t {{
public:
	single_line_t(long line_number, std::string txt);
}};

struct function_line_t : public line_t {{
public:
	function_t function;

	double hits_percentage;
	double time_percentage;
	double per_hit_percentage; // kind of weird to think about

	bool ignore;

	function_line_t(long line_number, std::string txt);
}};

std::unordered_map<std::string, file_t> files;

}}
#endif /* PROFILE_HPP */