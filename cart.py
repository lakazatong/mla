import itertools, json, colorsys

# TODO: look at line 184

def insert_in_sorted(lst, item, key=lambda x: x):
	for i in range(len(lst)):
		if key(lst[i]) > key(item):
			return i
	return len(lst)

def get_color(index, total):
	h = index / total
	s = 1.0
	v = 1.0
	return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h, s, v))

def indices_to_index(indices):
	number = 0
	for index in indices:
		number |= (1 << index)
	return number

"""
example with x0 in d0 = {1, 2} and x1 in d1 = {2, 3}

					v subtract hash(min(d0), min(d1)) = 5
12 -> 1 + 2 * 2 = 5 - 5 = 0
13 -> 1 + 3 * 2 = 7 - 5 = 2

22 -> 2 + 2 * 2 = 6 - 5 = 1
23 -> 2 + 3 * 2 = 8 - 5 = 3
"""
def custom_hash_coeffs(ranges):
	coeffs = [1]
	# yes the last range is ignored, each number only has to skip all possible values of the precedent ones
	# so custom_hash([1, 2, 3], [10, 10, 10]) == 321, here how many values the 3 can take is not our concern
	# to successfully hash the numbers 1 2 and 3
	for i in range(len(ranges)-1):
		coeffs.append(coeffs[i] * ranges[i + 1])
	return coeffs

def custom_hash(numbers, coeffs):
	# hash numbers given the set's cardinal they are in
	# so numbers[i] can take ranges[i] values
	return sum(coeffs[i] * numbers[i] for i in range(len(numbers)))

class Cart:
	def __init__(self, config, items_index, items_position):
		# assumes given argument make up for a valid Cart (no overlap)
		if len(items_index) != len(items_position):
			raise ValueError("len(items_index) != len(items_position)")
		self.config = config
		self.items = config["items"]
		self.cart_width, self.cart_height = config["cart_width"], config["cart_height"]
		# if so the caller is responsible for assigning the following attributes
		# space, items_index, items_position
		# as well as calling set_hashed_items on it after its items were set, and set_value
		if len(items_index) == 0: return
		self.space = [[-1 for _ in range(self.cart_width)] for _ in range(self.cart_height)]
		for k in range(len(items_index)):
			item_index = items_index[k]
			i0, j0 = items_position[k]
			item = self.items[item_index]
			shape = item["shape"]
			for i in range(item["height"]):
				tmp = i0 + i
				for j in range(item["width"]):
					if shape[i][j] != 0:
						self.space[tmp][j0 + j] = item_index
		self.items_index = items_index
		self.items_position = items_position
		# hash now since it will be reused a lot
		self.set_hashed_items()
		self.set_value()

	def try_merge(self, item_index, item_position):
		# returns None if it creates an overlap or a new cart with this item added
		item = self.items[item_index]
		shape = item["shape"]
		i0, j0 = item_position
		space_copy = [[self.space[i][j] for j in range(self.cart_width)] for i in range(self.cart_height)]
		for i in range(item["height"]):
			tmp = i0 + i
			for j in range(item["width"]):
				if self.space[tmp][j0 + j] != -1 and shape[i][j] != 0:
					return None
				space_copy[tmp][j0 + j] = shape[i][j]
		merged_cart = Cart(self.config, [], [])
		merged_cart.space = space_copy
		# copy items' index and position
		merged_cart.items_index = [i for i in self.items_index]
		merged_cart.items_position = [pos for pos in self.items_position]

		# add the merged item
		index = insert_in_sorted(merged_cart.items_index, item_index)
		merged_cart.items_index.insert(index, item_index)
		merged_cart.items_position.insert(index, item_position)

		merged_cart.set_hashed_items()
		merged_cart.set_value()
		
		return merged_cart

	def full(self):
		for i in range(self.cart_height):
			for j in range(self.cart_width):
				if self.space[i][j] == -1:
					return False
		return True

	def is_valid(self, pos):
		y, x = pos
		return x >= 0 and x < self.cart_width and y >= 0 and y < self.cart_height

	def get_neighbours(self, pos):
		y, x = pos
		r = []
		left, right, top, down = (y, x-1), (y, x+1), (y-1, x), (y+1, x)
		if self.is_valid(left): r.append(left)
		if self.is_valid(right): r.append(right)
		if self.is_valid(top): r.append(top)
		if self.is_valid(down): r.append(down)
		return r

	def get_adjacent_items(self, item_index, item_position):
		item = self.items[item_index]
		shape = item["shape"]
		i0, j0 = item_position
		r = set()
		for i in range(item["height"]):
			tmp = i0 + i
			for j in range(item["width"]):
				if shape[i][j] == 0: continue
				neighbours = self.get_neighbours((j0 + j, tmp))
				for neighbour in neighbours:
					y, x = neighbour
					r.add(self.space[y][x])
		return list(r)

	def set_value(self):
		self.value = 0
		adjs = [self.get_adjacent_items(self.items_index[i], self.items_position[i]) for i in range(len(self.items_index))]
		self.has_items_with_effect = False
		self.added_value = 0
		# apply all effects
		for i in range(len(self.items_index)):
			item_index = self.items_index[i]
			# item_position = self.items_position[i]
			
			# all items with an effect
			# too lazy to have a class Item and have a class for all item and override an abstract "apply_effect" method
			# here effects are translated to effects to the cart value directly
			# tho we still apply all effects before adding their base value as we should
			match item_index:
				# Gleaming Earrings (Normal)
				case 9:
					self.has_items_with_effect = True
					for adj in adjs[i]:
						if self.items[adj]["rarity"] == "Rare Goods":
							self.value += 20
							self.added_value += 20
				# Gleaming Earrings (Rare)
				case 10:
					self.has_items_with_effect = True
					for adj in adjs[i]:
						if self.items[adj]["rarity"] == "Rare Goods":
							self.value += 30
							self.added_value += 30
		self.value += sum(self.items[i]["value"] for i in self.items_index)
		self.is_full = self.full()
		if self.is_full:
			self.value += self.cart_width * self.cart_height * 20
		return self.value

	# not true deep equality, but rather "equivalent"
	def __equal__(self, other):
		# make sure this won't happen by the caller
		# n = len(self.items_index)
		# if n != len(other.items_index):
		# 	return False
		for i in range(len(self.items_index)):
			if self.hashed_items[i] != other.hashed_items[i]:
				return False
		# TODO: ??????????????????? figure out why this never prints ???????????????????
		print("found two equivalent cart")
		return True

	def set_hashed_items(self):
		# hashes the space (items' type, rarity and position)
		# will use that to compare carts and detect equivalent ones:
		# the ones with the same items and rarity on the same positions but swapped in some way
		# all thanks to the sorting of the items by type and then by rarity rather than position
		
		# since items' type are basically their index they are already sorted
		# they are also grouped by their rarity in the config already so no sorting to do here
		# rarities are technically considered different items all together since they have different indices in this implementation lol
		
		# in the end we end up just hashing their indices and their position
		# this hashing technique, why it works and how it is related to number bases is explained just under this function
		# here the hashes are already 0 based (hashing a the item of type 0 at pos 0, 0 yields 0)
		
		coeffs = custom_hash_coeffs([self.cart_width, self.cart_height, 0])
		# hash x, y and type of all items
		offset = self.items_index[0] # == min(self.items_index)
		# we want the items' index (<=> type + rarity), hence the offset + i
		self.hashed_items = []
		for i in range(len(self.items_index)):
			item_index = self.items_index[i]
			item_position = self.items_position[i]
			self.hashed_items.append(custom_hash([item_position[1], item_position[0], item_index], coeffs))

		# since self.items_index is sorted, the hashes are sorted by type as well
		return self.hashed_items

		# we could hash the hashes as such:
		# the range of an item hash
		# hashed_range = len(self.items) * self.cart_width * self.cart_height
		# coeffs = custom_hash_coeffs([hashed_range] * len(hashed_items)) <- 100% overflow lmao
		# return custom_hash(hashed_items, coeffs)

		# but it would yield hashes in the order of 10^100 lmao
		# we are better off having a non unique hash function and deal with collisions but that sounds like a pain to do
		# since we want to pre compute the hashes to compare carts' spaces later

	"""
		to hash x0, x1, ..., x(n-1), xn with x0 in d0, x1 in d1, ..., x(n-1) in d(n-1) and xn in dn
		we can do:
		hash(x0, x1, ..., x(n-1), xn) = x0 * Acard(d1) + x1 * Acard(d2) + ... + x(n-1) * Acard(dn) + xn
		with Acard(di) = the product of all card(dj) with j from i to n
		we could subtract hash(min(d0), min(d1), ..., min(dn)) if we want the hashes to start at 0
		taking x0, x1, ..., xn in [[0, k-1]] yields the base k (which I find quite interesting and beautiful in a way, it also straight up "proves" why it works)
	"""

	def __repr__(self):
		total_items = len(self.items)
		colored_space = ""
		for row in self.space:
			for cell in row:
				if cell == -1:
					colored_space += "\u2588\u2588\u2588"
				else:
					color = get_color(cell, total_items)
					colored_space += f"\033[38;2;{color[0]};{color[1]};{color[2]}m\u2588\u2588\u2588\033[0m"
			colored_space += "\n"
		return colored_space

class CartSolver:

	carts_cache = []
	total_sizes_cache = []
	total_prices_cache = []

	def __init__(self, config, available_items_index):
		self.config = config
		self.items = config["items"]
		self.available_items_index = available_items_index
		self.cart_width, self.cart_height = config["cart_width"], config["cart_height"]
		self.cart_size = self.cart_width * self.cart_height
		self.start_number_of_items = min(1, len(available_items_index))
		self.compute_items_sizes()
		self.compute_items_possible_positions()
		self.compute_all_indices_combinations()
		self.init_caches()

	def compute_items_sizes(self):
		for item in self.items:
			shape = item["shape"]
			item["height"] = len(shape)
			item["width"] = len(shape[0])
			item["size"] = sum(sum(row) for row in shape)

	def compute_items_possible_positions(self):
		for item in self.items:
			item["possible_positions"] = [(i, j) for i in range(self.cart_height - item["height"] + 1) for j in range(self.cart_width - item["width"] + 1)]

	def compute_all_indices_combinations(self):
		n = len(self.available_items_index)
		self.all_indices_combinations = []
		for n_items in range(self.start_number_of_items, n + 1):
			self.all_indices_combinations.append([(list(indices), indices_to_index(list(indices))) for indices in itertools.combinations(range(len(self.available_items_index)), n_items)])

	def init_caches(self):
		nb_indices_as_index_possible = indices_to_index(range(len(self.available_items_index))) + 1

		if len(self.carts_cache) == 0:
			for _ in range(nb_indices_as_index_possible):
				self.carts_cache.append([])
		
		if len(self.total_sizes_cache) == 0:
			for _ in range(nb_indices_as_index_possible):
				self.total_sizes_cache.append(-1)
		
		if len(self.total_prices_cache) == 0:
			for _ in range(nb_indices_as_index_possible):
				self.total_prices_cache.append(-1)

	# should not be called with one index in left_indices (except from itself)
	@profile
	def generate_carts(self, left_indices, indices_as_index):
		if len(self.carts_cache[indices_as_index]) != 0:
			return self.carts_cache[indices_as_index]
		print(f"generating all carts with {left_indices}")
		if len(left_indices) == 1:
			item_index = self.available_items_index[left_indices[0]]
			r = [Cart(self.config, [item_index], [pos]) for pos in self.items[item_index]["possible_positions"]]
			self.carts_cache[indices_as_index] = [cart for cart in r]
			return r
		available_item_index = left_indices.pop()
		item_index = self.available_items_index[available_item_index]
		item = self.items[item_index]
		# all carts with one less item
		carts = self.generate_carts([i for i in left_indices], indices_as_index & ~(1 << available_item_index))
		r = []
		# number of carts with one item less
		n = len(carts)
		# try merging each of them with the removed item
		for cart in carts:
			for position in item["possible_positions"]:
				merged_cart = cart.try_merge(item_index, position)
				# append if (the merged cart is "interesting")
				# merge succeeded (no overlap) and
				# the merged cart has no items with effect or has some and have them add value and
				# the merged cart is not equivalent to any other already found
				if (merged_cart != None and
					(not merged_cart.has_items_with_effect or merged_cart.has_items_with_effect and merged_cart.added_value > 0) and
					all(cart != merged_cart for cart in r[n:])):
					# print(f"adding one more cart with {len(left_indices) + 1} items")
					r.append(merged_cart)
		# cache generated carts
		self.carts_cache[indices_as_index] = [cart for cart in r]
		return r

	def _solve(self, min_base_price):
		must_have_items_index = [i for i in range(len(self.items)) if "Non-discardable" in self.items[i].get("feature", "").split(",") or self.items[i].get("rarity", "") == "Vital Goods"]
		best_cart = Cart(self.config, [], [])
		best_cart.value = 0
		for n_items in range(self.start_number_of_items, len(self.available_items_index) + 1):
			for indices, indices_as_index in self.all_indices_combinations[n_items - self.start_number_of_items]:

				total_size = 0
				if self.total_sizes_cache[indices_as_index] != -1:
					total_size = self.total_sizes_cache[indices_as_index]
				else:
					total_size = sum(self.items[self.available_items_index[i]]["size"] for i in indices)
					self.total_sizes_cache[indices_as_index] = total_size
				if total_size > self.cart_size: continue
				
				total_price = 0
				if self.total_prices_cache[indices_as_index] != -1:
					total_price = self.total_prices_cache[indices_as_index]
				else:
					total_price = sum(self.items[self.available_items_index[i]]["value"] for i in indices)
					self.total_prices_cache[indices_as_index] = total_price
				if total_price < min_base_price: continue

				actual_items_index = list(set([self.available_items_index[i] for i in indices]))
				if not any(i not in actual_items_index for i in must_have_items_index): continue
				
				carts = self.generate_carts(indices, indices_as_index)
				
				if len(carts) > 0:
					print(f'generated {len(carts)} "interesting" carts with {len(indices)} items')
				for cart in carts:
					if cart.value > best_cart.value:
						# print("found a better cart! c:")
						best_cart = cart
		return best_cart

	def solve(self):
		for min_base_price in range(7000, -1, -10):
			print(f"trying with {min_base_price = }")
			r = self._solve(min_base_price)
			if r.value > 0:
				return r
		return None

def main():
	content = None

	with open("cart_config.json", "r") as f:
		content = f.read()

	config = json.loads(content)
	solver = CartSolver(config, [0, 0])
	best_cart = solver.solve()

	print(best_cart)

if __name__ == '__main__':
	main()