
// THIS FILE IS AUTO GENERATED, EVERYTHING WRITTEN HERE WILL BE OVERWRITTEN

#include <chrono>

#define DEF_CHRONO(line_number) std::chrono::time_point<std::chrono::high_resolution_clock> st##line_number; double stet##line_number = 0; double stet##line_number##_hits = 0;
#define OPEN_CHRONO(line_number) st##line_number = std::chrono::high_resolution_clock::now();
#define CLOSE_CHRONO(line_number) std::chrono::duration<double, std::milli> elapsed##line_number = std::chrono::high_resolution_clock::now() - st##line_number; stet##line_number += elapsed##line_number.count(); stet##line_number##_hits++;
#define REP_CHRONO(line_number) std::cout << "line " << std::to_string(line_number) << ": " << stet##line_number << "ms " << "(" << stet##line_number##_hits << " hits, " << stet##line_number / stet##line_number##_hits << "ms per hit)" << std::endl;

DEF_CHRONO(383) DEF_CHRONO(385) DEF_CHRONO(386) DEF_CHRONO(387) DEF_CHRONO(388) DEF_CHRONO(389) DEF_CHRONO(390) DEF_CHRONO(391) DEF_CHRONO(392) DEF_CHRONO(393) DEF_CHRONO(397) DEF_CHRONO(398) DEF_CHRONO(399) DEF_CHRONO(400) DEF_CHRONO(401) DEF_CHRONO(402) DEF_CHRONO(403) DEF_CHRONO(404) DEF_CHRONO(406) DEF_CHRONO(407) DEF_CHRONO(408) DEF_CHRONO(410) DEF_CHRONO(411) DEF_CHRONO(412) DEF_CHRONO(414) DEF_CHRONO(415) DEF_CHRONO(416)
DEF_CHRONO(427) DEF_CHRONO(428) DEF_CHRONO(429) DEF_CHRONO(432) DEF_CHRONO(433) DEF_CHRONO(434) DEF_CHRONO(435) DEF_CHRONO(436) DEF_CHRONO(437) DEF_CHRONO(438) DEF_CHRONO(439) DEF_CHRONO(440) DEF_CHRONO(443) DEF_CHRONO(444)

#include <iostream>
#include <algorithm>
#include <bitset>
#include <chrono>
#include <numeric>
#include <memory>
#include <string>
#include <iomanip>

#include "mla.hpp"

using namespace std;

// categories
const int NONE = 0;
const int ANTIQUE = 1;
const int WEAPON = 2;
const int FOOD = 3;

// rarities
const int NORMAL_GOOD = 0;
const int RARE_GOOD = 1;
const int VITAL_GOOD = 2;
const int ATTRIBUTE_STONE = 3;

vector<unique_ptr<Item>> all_items;
int all_items_length = 0;

const int cart_width = 6;
const int cart_height = 4;
const int cart_size = cart_height * cart_width;
// const int trailing_zeros_length = 32 - cart_size;

void apply_full_cart_bonus(Cart& cart) {
	cart.value += cart_width * cart_height * 20;
}

// -------------------
// Utils

inline bool valid_pos(int index) {
	return index >= 0 && index < cart_size;
}

vector<int> get_neighbours(int index) {
	vector<int> r;
	int left = index - 1;
	int right = index + 1;
	int top = index - cart_width;
	int bottom = index + cart_width;
	if (valid_pos(left)) r.push_back(left);
	if (valid_pos(right)) r.push_back(right);
	if (valid_pos(top)) r.push_back(top);
	if (valid_pos(bottom)) r.push_back(bottom);
	return r;
}

bool has_common_element(const set<int>& set1, const set<int>& set2) {
	for (int element : set1) {
		if (set2.count(element) > 0) { return true; }
	}
	return false;
}

template <typename T>
std::ostream& operator<<(std::ostream& os, const std::vector<T>& vec) {
	os << "[";
	for (size_t i = 0; i < vec.size(); ++i) {
		os << setw(2) << setfill(' ') << vec[i];
		if (i != vec.size() - 1) {
			os << ", ";
		}
	}
	os << "]";
	return os;
}

constexpr unsigned long long factorial(int n) {
	unsigned long long result = 1;
	for (int i = 2; i <= n; ++i) {
		result *= i;
	}
	return result;
}

constexpr unsigned long long nChooseK(int n, int k) {
	return factorial(n) / (factorial(k) * factorial(n - k));
}

constexpr unsigned int count_ones(unsigned int n) {
	unsigned int count = 0;
	while (n) {
		n &= (n - 1);
		count++;
	}
	return count;
}


// Utils
// -------------------

// -------------------
// Item

Item::Item(int category, int rarity, int value, const vector<int>& shape, int width)
	: category(category), rarity(rarity), base_value(value), value(value),
	shape(shape), width(width), item_type(0) {
	height = ((int)shape.size()) / width;
	size = height * width;
	id = all_items_length++;
	for (int i = 0; i <= cart_height - height; i++) {
		for (int j = 0; j <= cart_width - width; j++) {
			possible_positions.push_back(i * cart_width + j);
		}
	}
}

void Item::set_adjacent_items(const vector<int>& cells, int k) {
	set<int> r;
	for (int i = 0; i < height; i++) {
		for (int j = 0; j < width; j++) {
			if (shape[i * width + j] == 0) continue;
			for (auto j : get_neighbours(k + i * cart_width + j)) {
				int neighbour_id = cells[j];
				if (neighbour_id != -1 && neighbour_id != id) { r.insert(neighbour_id); }
			}
		}
	}
	adjacent_items.assign(r.begin(), r.end());
}

template<typename T>
void Item::create(int category, int rarity, int value, const vector<int>& shape, int width) {
	static_assert(is_base_of<Item, T>::value, "T must be derived from Item");
	all_items.push_back(make_unique<T>(category, rarity, value, shape, width));
}

std::ostream& operator<<(std::ostream& os, const Item& item) {
	os << "category: " << item.category << ", rarity: " << item.rarity << ", base_value: " << item.base_value
		<< ", value: " << item.value << ", width: " << item.width << ", height: " << item.height << ", id: " << item.id
		<< ", size: " << item.size << ", item_type: " << item.item_type << std::endl;
	os << "shape: [";
	for (size_t i = 0; i < item.shape.size(); ++i) {
		os << item.shape[i];
		if (i != item.shape.size() - 1) {
			os << ", ";
		}
	}
	os << "]" << std::endl;
	os << "possible_positions: ";
	for (int pos : item.possible_positions) {
		os << pos << " ";
	}
	os << std::endl;
	os << "adjacent_items: ";
	for (int adj : item.adjacent_items) {
		os << adj << " ";
	}
	os << std::endl;
	return os;
}

// Item
// -------------------

// -------------------
// Cart

Cart::Cart() : value(0), cells(cart_size, -1), cells_as_number(0) {}

bool Cart::full() const {
	return find(cells.begin(), cells.end(), -1) == cells.end();
}

void Cart::add_item(const Item& item, int k) {
	items.push_back(item.id);
	items_coords.push_back(k);
	for (int i = 0; i < item.height; i++) {
		for (int j = 0; j < item.width; j++) {
			if (item.shape[i * item.width + j] == 1) {
				cells[k + i * cart_width + j] = item.id;
			}
		}
	}
}

int Cart::set_value() {
	for (size_t i = 0; i < items.size(); ++i) {
		Item& item = *all_items[items[i]];
		item.value = item.base_value;
		item.set_adjacent_items(cells, items_coords[i]);
	}
	for (int i : items) { all_items[i]->apply_effect(*this); }
	value = 0;
	for (int i : items) { value += all_items[i]->value; }
	if (full()) { apply_full_cart_bonus(*this); }
	return value;
}

void Cart::compress_attributes() {
	// items_set = set<int>(items.begin(), items.end());
	cells_as_number = 0;
	for (int i = cart_size - 1; i >= 0; i--) {
		cells_as_number |= ~(cells[i] >> 31U) & (1U << i);
		/*cout << cells[i] << endl;
		cout << bitset<8>(cells[i]) << endl;
		cout << bitset<8>(~(cells[i] >> 31U)) << endl;
		if (cells[i] != -1) {
			cells_as_number |= (1U << (cart_size - 1 - i));
		}*/
	}
	/*
	if (cells_as_number != cells_as_number2) {
		cout << "cells_as_number: " << cells_as_number << ", cells_as_number2: " << cells_as_number2 << endl;
		cout << cells << endl;
		cout << "[ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]" << endl;
		cout << "[23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10,  9,  8,  7,  6,  5,  4,  3,  2,  1,  0]" << endl;
		exit(1);
	}*/
	// cells_as_number <<= trailing_zeros_length;
}

void Cart::set_canonical_form() {
	canonical_form.clear();
	for (size_t i = 0; i < items.size(); ++i) {
		// hash item type and pos
		canonical_form.push_back(all_items[items[i]]->item_type * cart_size + items_coords[i]);
	}
	sort(canonical_form.begin(), canonical_form.end());
}

string Cart::to_string() const {
	const int GREY = 90, RED = 31, GREEN = 32, YELLOW = 33, BLUE = 34, PURPLE = 35, CYAN = 36, WHITE = 37;
	vector<int> colors = { GREY, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, WHITE };
	string r;

	for (int i = 0; i < cart_height; ++i) {
		string row_str = "";
		for (int j = 0; j < cart_width; ++j) {
			int cell = cells[i * cart_width + j];
			if (cell < -1 || cell >= static_cast<int>(colors.size()) - 1) {
				throw invalid_argument("Unknown cell value: " + std::to_string(cell));
			}
			row_str += "\033[" + std::to_string(colors[cell + 1]) + "m██\033[0m";
		}
		r += row_str + "\n";
	}

	return r;
}

// Cart
// -------------------

// -------------------
// Define all items

class AncientHolyGrail : public Item {
public:
	AncientHolyGrail(int category, int rarity, int value, const vector<int>& shape, int width)
		: Item(category, rarity, value, shape, width) {
		this->item_type = 0;
	}

	void apply_effect(Cart& cart) override {
		for (int adj_index : adjacent_items) {
			if (all_items[adj_index]->rarity == ATTRIBUTE_STONE) {
				cart.value += 200;
			}
		}
	}
};

// Define all items
// -------------------

// -------------------
// Algorithm

vector<vector<Cart>> all_carts;
// as many as there are items combinations
unsigned int all_carts_length;
// basically: one_item_carts_index[i] = available_items_to_index({i}) since they will be often needed
vector<unsigned int> one_item_carts_index;

/*

example with 4 items ({abcd} means "all possible carts with items of index 0 if a, 1 if b, 2 if c and 3 if d"):

1000 = ...
0100 = ...
0010 = ...
0001 = ...

0011 = {{0010 + 0001} + {0001 + 0010}}
0101 = {{0100 + 0001} + {0001 + 0100}}
1001 = {{1000 + 0001} + {0001 + 1000}}
0110 = {{0100 + 0010} + {0010 + 0100}}
1010 = {{1000 + 0010} + {0010 + 1000}}
1100 = {{1000 + 0100} + {0100 + 1000}}

0111 = {{0110 + 0001} + {0101 + 0010} + {0011 + 0100}}
1011 = {{1010 + 0001} + {1001 + 0010} + {0011 + 1000}}
1101 = {{1100 + 0001} + {1001 + 0100} + {0101 + 1000}}
1110 = {{1100 + 0010} + {1010 + 0100} + {0110 + 1000}}

1111 = {{1110 + 0001} + {1101 + 0010} + {1011 + 0100} + {0111 + 1000}}

re ordered as it will be indexed:

0001 = ...
0010 = ...
0011 = {{0010 + 0001} + {0001 + 0010}}
0100 = ...
0101 = {{0100 + 0001} + {0001 + 0100}}
0110 = {{0100 + 0010} + {0010 + 0100}}
0111 = {{0110 + 0001} + {0101 + 0010} + {0011 + 0100}}
1000 = ...
1001 = {{1000 + 0001} + {0001 + 1000}}
1010 = {{1000 + 0010} + {0010 + 1000}}
1011 = {{1010 + 0001} + {1001 + 0010} + {0011 + 1000}}
1100 = {{1000 + 0100} + {0100 + 1000}}
1101 = {{1100 + 0001} + {1001 + 0100} + {0101 + 1000}}
1110 = {{1100 + 0010} + {1010 + 0100} + {0110 + 1000}}
1111 = {{1110 + 0001} + {1101 + 0010} + {1011 + 0100} + {0111 + 1000}}

there are 2^4 - 1 = 15 unique combinations for 4 items
this algorithm only works with <= 31 items
this is reasonable because if we try as many 1x1 items as there are cells in a cart 6 * 4 = 24 we would be under 31
meaning we would need to have at least 7 duplicates of any 1x1 item to reach the limit

*/

std::chrono::time_point<std::chrono::high_resolution_clock> st1;
std::chrono::time_point<std::chrono::high_resolution_clock> st2;
double stet1 = 0;
double stet1_hits = 0;
double stet2 = 0;
double stet2_hits = 0;

inline void try_adding_cart(Cart& cart, int index) {
	for (const Cart& existing_cart : all_carts[index]) {
		if (cart.canonical_form == existing_cart.canonical_form) {
			return;
		}
	}
	st1 = std::chrono::high_resolution_clock::now();
	cart.compress_attributes();
	std::chrono::duration<double, std::milli> elapsed1 = std::chrono::high_resolution_clock::now() - st1;
	stet1 += elapsed1.count();
	stet1_hits++;
	st2 = std::chrono::high_resolution_clock::now();
	all_carts[index].push_back(cart);
	std::chrono::duration<double, std::milli> elapsed2 = std::chrono::high_resolution_clock::now() - st2;
	stet2 += elapsed2.count();
	stet2_hits++;
}

inline unsigned int available_items_to_index(const vector<int>& available_items) {
	unsigned int index = 0;
	for (size_t i = 0; i < available_items.size(); ++i) {
		index |= (1U << available_items[i]);
	}
	return index - 1;
}

// @profile
                          void generate_all_carts(const vector<int>& available_items) {
OPEN_CHRONO(383)              if (available_items.size() == 1) {                                                                                                                           CLOSE_CHRONO(383)
                                  // base case
OPEN_CHRONO(385)                  int item_index = available_items[0];                                                                                                                     CLOSE_CHRONO(385)
OPEN_CHRONO(386)                  unsigned int index = one_item_carts_index[item_index];                                                                                                   CLOSE_CHRONO(386)
OPEN_CHRONO(387)                  const Item& item = *all_items[item_index];                                                                                                               CLOSE_CHRONO(387)
OPEN_CHRONO(388)                  for (int pos : item.possible_positions) {                                                                                                                CLOSE_CHRONO(388)
OPEN_CHRONO(389)                      Cart cart;                                                                                                                                           CLOSE_CHRONO(389)
OPEN_CHRONO(390)                      cart.add_item(item, pos);                                                                                                                            CLOSE_CHRONO(390)
OPEN_CHRONO(391)                      cart.set_canonical_form();                                                                                                                           CLOSE_CHRONO(391)
OPEN_CHRONO(392)                      cart.compress_attributes();                                                                                                                          CLOSE_CHRONO(392)
OPEN_CHRONO(393)                      all_carts[index].push_back(cart);                                                                                                                    CLOSE_CHRONO(393)
                                  }
                                  return;
                              }
OPEN_CHRONO(397)              unsigned int index = available_items_to_index(available_items);                                                                                              CLOSE_CHRONO(397)
OPEN_CHRONO(398)              for (size_t i = 0; i < available_items.size(); i++) {                                                                                                        CLOSE_CHRONO(398)
OPEN_CHRONO(399)                  int removed_item_index = available_items[i];                                                                                                             CLOSE_CHRONO(399)
OPEN_CHRONO(400)                  auto one_less_available_items = available_items;                                                                                                         CLOSE_CHRONO(400)
OPEN_CHRONO(401)                  one_less_available_items.erase(one_less_available_items.begin() + i);                                                                                    CLOSE_CHRONO(401)
OPEN_CHRONO(402)                  unsigned int one_less_index = index - (1U << removed_item_index);                                                                                        CLOSE_CHRONO(402)
OPEN_CHRONO(403)                  if (all_carts[one_less_index].empty()) {                                                                                                                 CLOSE_CHRONO(403)
OPEN_CHRONO(404)                      generate_all_carts(one_less_available_items);                                                                                                        CLOSE_CHRONO(404)
                                  }
OPEN_CHRONO(406)                  for (const Cart& cart : all_carts[one_less_index]) {                                                                                                     CLOSE_CHRONO(406)
OPEN_CHRONO(407)                      for (const Cart& one_item_cart : all_carts[one_item_carts_index[removed_item_index]]) {                                                              CLOSE_CHRONO(407)
OPEN_CHRONO(408)                          if (cart.cells_as_number & one_item_cart.cells_as_number) { continue; }                                                                          CLOSE_CHRONO(408)
                                          // merge cart with one_item_cart
OPEN_CHRONO(410)                          Cart merged;                                                                                                                                     CLOSE_CHRONO(410)
OPEN_CHRONO(411)                          for (size_t j = 0; j < cart.items.size(); j++) {                                                                                                 CLOSE_CHRONO(411)
OPEN_CHRONO(412)                              merged.add_item(*all_items[cart.items[j]], cart.items_coords[j]);                                                                            CLOSE_CHRONO(412)
                                          }
OPEN_CHRONO(414)                          merged.add_item(*all_items[removed_item_index], one_item_cart.items_coords[0]);                                                                  CLOSE_CHRONO(414)
OPEN_CHRONO(415)                          merged.set_canonical_form();                                                                                                                     CLOSE_CHRONO(415)
OPEN_CHRONO(416)                          try_adding_cart(merged, index);                                                                                                                  CLOSE_CHRONO(416)
                                      }
                                  }
                              }
                          }

std::chrono::time_point<std::chrono::high_resolution_clock> time_took_start;
std::chrono::time_point<std::chrono::high_resolution_clock> time_took_end;

// @profile
                          void compute_best_carts() {
OPEN_CHRONO(427)              vector<int> available_items;                                                                                                                                 CLOSE_CHRONO(427)
OPEN_CHRONO(428)              for (int i = 0; i < all_items.size(); ++i) {                                                                                                                 CLOSE_CHRONO(428)
OPEN_CHRONO(429)                  available_items.push_back(i);                                                                                                                            CLOSE_CHRONO(429)
                              }
                              // cout << available_items << endl;
OPEN_CHRONO(432)              time_took_start = std::chrono::high_resolution_clock::now();                                                                                                 CLOSE_CHRONO(432)
OPEN_CHRONO(433)              generate_all_carts(available_items);                                                                                                                         CLOSE_CHRONO(433)
OPEN_CHRONO(434)              time_took_end = std::chrono::high_resolution_clock::now();                                                                                                   CLOSE_CHRONO(434)
OPEN_CHRONO(435)              vector<Cart>& carts = all_carts[all_carts_length - 1];                                                                                                       CLOSE_CHRONO(435)
OPEN_CHRONO(436)                                                                                                                                                                           CLOSE_CHRONO(436)
OPEN_CHRONO(437)              int max_value = 0;                                                                                                                                           CLOSE_CHRONO(437)
OPEN_CHRONO(438)              for (auto& cart : carts) {                                                                                                                                   CLOSE_CHRONO(438)
OPEN_CHRONO(439)                  if (cart.set_value() > max_value) {                                                                                                                      CLOSE_CHRONO(439)
OPEN_CHRONO(440)                      max_value = cart.value;                                                                                                                              CLOSE_CHRONO(440)
                                  }
                              }
OPEN_CHRONO(443)                                                                                                                                                                           CLOSE_CHRONO(443)
OPEN_CHRONO(444)              carts.erase(remove_if(carts.begin(), carts.end(),[max_value](const auto& cart) {return cart.value != max_value;}),carts.end());                              CLOSE_CHRONO(444)
                          }

// Algorithm
// -------------------

void test(const vector<int>& available_items) {
	cout << available_items_to_index(available_items) << " -> " << available_items << endl;
}

int main() {
	/*
	for (int i = -1; i <= 10; i++) {
		std::cout << setw(2) << setfill(' ') << i << ": " << bitset<8>(i) << " -> " << std::bitset<8>((i & ~(i >> 31)) << 1) << std::endl;
	}
	return 0;
	
	test({ 0 });
	test({ 1 });
	test({ 0, 1 });
	test({ 2 });
	test({ 0, 2 });
	test({ 1, 2 });
	test({ 0, 1, 2 });
	test({ 3 });
	test({ 0, 3 });
	test({ 1, 3 });
	test({ 0, 1, 3 });
	test({ 2, 3 });
	test({ 0, 2, 3 });
	test({ 1, 2, 3 });
	test({ 0, 1, 2, 3 });
	return 0;
	*/
	// init
	Item::create<AncientHolyGrail>(ANTIQUE, RARE_GOOD, 180, { 1, 1 }, 1);
	Item::create<AncientHolyGrail>(ANTIQUE, RARE_GOOD, 180, { 1, 1 }, 1);
	Item::create<AncientHolyGrail>(ANTIQUE, RARE_GOOD, 180, { 1, 1 }, 1);
	Item::create<AncientHolyGrail>(ANTIQUE, RARE_GOOD, 180, { 1, 1 }, 1);
	// Item::create<AncientHolyGrail>(ANTIQUE, RARE_GOOD, 180, { 1, 1 }, 1);
	// Item::create<AncientHolyGrail>(ANTIQUE, RARE_GOOD, 180, { 1, 1 }, 1);
	// Item::create<AncientHolyGrail>(ANTIQUE, RARE_GOOD, 180, { 1, 1 }, 1);

	if (all_items_length < 1 || all_items_length > 31) {
		cout << "all_items_length must be between 1 and 31" << endl;
		exit(1);
	}

	all_carts_length = (1U << all_items_length) - 1;

	all_carts.resize(all_carts_length);
	// cout << "all_carts.size() = " << all_carts.size() << endl;
	// cout << "all_carts.capacity() = " << all_carts.capacity() << endl;
	
	for (int i = 0; i < all_carts_length; i++) {
		// worst case is when n items are of shape 1x1
		// meaning the number of possible carts is factorial
		// 
		// nb possible carts =
		// cart_size! / (cart_size - n)!		if 0 <= n < cart_size
		// cart_size!							if n = cart_size
		// cart_size! * (n choose cart_size)	if n > cart_size
		// 
		// we do this to help push back
		unsigned int n = count_ones(i);
		constexpr unsigned int cart_size_fact = factorial(cart_size);
		all_carts[i].resize(n == cart_size ? cart_size_fact :
			n > cart_size ? cart_size_fact * nChooseK(n, cart_size) :
			cart_size_fact / factorial(cart_size - n));
	}
	
	one_item_carts_index.reserve(all_items_length);
	auto* buffer = one_item_carts_index.data();
	for (int i = 0; i < all_items_length; i++) {
		buffer[i] = available_items_to_index({ i });
	}
	one_item_carts_index.resize(all_items_length);
	compute_best_carts();
	/*
	for (const auto& cart : all_carts[all_carts_length - 1]) {
		cout << cart.to_string() << endl;
	}
	*/
	std::chrono::duration<double, std::milli> elapsed = time_took_end - time_took_start;
	cout << "nb carts found: " << all_carts[all_carts_length - 1].size() << " (" << elapsed.count() << "ms)" << endl;
	REP_CHRONO(383)
	REP_CHRONO(427)
}
