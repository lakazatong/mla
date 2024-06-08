import itertools, json, colorsys

# TODO: separer generate_carts et generate_carts_with_effect

# en supposont qu'on a une config d'item qui a une size <= taille du cart

# si < taille du cart:
# si aucun item a effet: renvoyer premiere config qui les fait tous rentrer
# sinon: renvoyer la config qui fait tout rentrer avec le + de bonus value

# si == taille du cart:
# si aucun item a effet: renvoyer premiere config qui est full
# sinon: renvoyer la config full avec le + de bonus value

def get_color(index, total):
	h = index / total
	s = 1.0
	v = 1.0
	return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h, s, v))

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
		# as well as calling set_value
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
					if shape[i][j] == 0: continue
					self.space[tmp][j0 + j] = items_index
		self.items_index = items_index
		self.items_position = items_position
		self.set_value()

	@profile
	def try_merge(self, item_index, item_position):
		# returns None if it creates an overlap or a new cart with this item added
		item = self.items[item_index]
		shape = item["shape"]
		i0, j0 = item_position
		space_copy = [[self.space[i][j] for j in range(self.cart_width)] for i in range(self.cart_height)]
		for i in range(item["height"]):
			tmp = i0 + i
			for j in range(item["width"]):
				if shape[i][j] == 0: continue
				if space_copy[tmp][j0 + j] != -1: return None
				space_copy[tmp][j0 + j] = items_index
		merged_cart = Cart(self.config, [], [])
		merged_cart.space = space_copy
		# copy items' index and position
		merged_cart.items_index = [i for i in self.items_index] + [items_index]
		merged_cart.items_position = [pos for pos in self.items_position] + [item_position]

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
		adjs = [self.get_adjacent_items(self.items_index[k], self.items_position[k]) for k in range(len(self.items_index))]
		self.added_value = 0
		# apply all effects
		for k in range(len(self.items_index)):
			item_index = self.items_index[k]
			# item_position = self.items_position[k]
			
			# all items with an effect
			# too lazy to have a class Item and have a class for all item and override an abstract "apply_effect" method
			# here effects are translated to effects to the cart value directly
			# tho we still apply all effects before adding their base value as we should
			match item_index:
				# Gleaming Earrings (Normal)
				case 9:
					for adj in adjs[k]:
						if self.items[adj]["rarity"] == "Rare Goods":
							self.value += 20
							self.added_value += 20
				# Gleaming Earrings (Rare)
				case 10:
					for adj in adjs[k]:
						if self.items[adj]["rarity"] == "Rare Goods":
							self.value += 30
							self.added_value += 30
		self.value += sum(self.items[i]["value"] for i in self.items_index)
		self.is_full = self.full()
		if self.is_full:
			self.value += self.cart_width * self.cart_height * 20
		return self.value

	def __repr__(self):
		total_items = len(self.items)
		colored_space = "\n"
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
		self.must_have_items_index = [i for i in range(len(self.items)) if "Non-discardable" in self.items[i].get("feature", "").split(",") or self.items[i].get("rarity", "") == "Vital Goods"]
		self.compute_items_sizes()
		self.compute_items_possible_positions()
		self.compute_all_indices_combinations()

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
		self.all_indices_combinations = []
		for n_items in range(self.start_number_of_items, n + 1):
			tmp = []
			for indices in itertools.combinations(self.available_items_index, n_items):
				
				total_size = sum(self.items[i]["size"] for i in indices)
				if total_size > self.cart_size: continue

				if any(i not in indices for i in self.must_have_items_index): continue

				total_price = sum(self.items[i]["value"] for i in indices)

				with_effects = any("effect" in self.items[i] and self.items[i]["name"] != "Attribute Stone" for i in indices)

				# sort by size to fill up the cart as fast as possible
				tmp.append((sorted(list(indices), key=lambda i: -self.items[i]["size"]), total_size, total_price, with_effects))
			self.all_indices_combinations.append(tmp)

	def best_full_cart_with_effects(indices):


	def best_cart_with_effects(indices):


	def find_full_cart(indices):


	def _find_cart(i, indices, positions):
		if i == len(indices): return


	def find_cart(indices):
		positions = [(0, 0) for _ in indices]
		self._find_cart(0, indices, positions)
		return Cart(self.config, indices, positions)

	def _solve(self, min_base_price):
		best_cart = Cart(self.config, [], [])
		best_cart.value = -1
		for n_items in range(self.start_number_of_items, len(self.available_items_index) + 1):
			for indices, total_size, total_price, with_effects in self.all_indices_combinations[n_items - self.start_number_of_items]:

				if total_price < min_base_price: continue
				
				if with_effects:
					
					cart = self.best_full_cart_with_effects(indices) if total_size == self.cart_size else self.best_cart_with_effects(indices)
					
					if cart.value > best_cart.value:
						best_cart = cart

				else:

					if total_price <= best_cart.value: continue
					
					best_cart = self.find_full_cart(indices) if total_size == self.cart_size else self.find_cart(indices)

		return best_cart

	def solve(self):

		# cart1 = Cart(self.config, [0, 0], [(0, 0), (0, 1)])
		# cart2 = Cart(self.config, [0, 0], [(0, 1), (0, 0)])
		# print(cart1 == cart2)
		# exit(0)

		for min_base_price in range(7000, -1, -10):
			# print(f"trying with {min_base_price = }")
			r = self._solve(min_base_price)
			if r.value != -1:
				return r
		return None

def main():

	content = None

	with open("cart_config.json", "r") as f:
		content = f.read()

	config = json.loads(content)
	solver = CartSolver(config, [1, 2, 3, 4, 5])
	best_cart = solver.solve()

	print("\n" + "-" * 40 + "\n\nbest cart found:")
	print(best_cart)

if __name__ == '__main__':
	main()