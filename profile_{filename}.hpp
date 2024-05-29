#ifndef PROFILE_{filename}_HPP
#define PROFILE_{filename}_HPP
namespace {namespace_name} {{

#include "profile_{common_filename}.hpp"

struct {function_class_name} {{
	// first_line_number == last_line_number if there is 1 line
	// first_line_number == last_line_number == line of the function declaration if there is 0 line
	long first_line_number;
	long last_line_number;

	long nb_call;
	// totals
	long hits;
	double time;
	double per_hit;
}}

struct {line_class_name} {{
public:
	long line_number;
	long hits;
	double time; // total time spent on this line
	double per_hit; // time spent every hit in average

	std::string prefix;
	std::string base_txt;
	std::string txt;
	std::string suffix;

	{line_class_name}(std::string txt);
}}

struct {single_line_class_name} : public {line_class_name} {{

}}

struct {function_line_class_name} : public {line_class_name} {{
	double hits_percentage;
	double time_percentage;
	double per_hit_percentage; // kind of weird to think about

	bool ignore;
}}

// lines[0] is a dummy since line numbers start at 1
std::vector<{line_class_name}> lines(1 + {max_line_number});
std::unordered_map<{function_class_name}> functions({len(functions)});

}}
#endif /* PROFILE_{filename}_HPP */