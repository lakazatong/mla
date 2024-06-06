import itertools, json

class CartSolver:

	class Cart:
		def __init__(self, config, items_index, items_position):
			# assumes given argument make up for a valid Cart (no overlap)
			if len(items_index) != len(items_position):
				raise ValueError("len(items_index) != len(items_position)")
			self.config = config
			self.items = config["items"]
			self.cart_width, self.cart_height = config["cart_width"], config["cart_height"]
			if len(items_index) == 0: return
			self.space = [[0] * self.cart_width] * self.cart_height
			for k in items_index:
				item = self.items[k]
				shape = item["shape"]
				j0, i0 = items_position[k]
				for i in range(item["height"]):
					tmp = i0 + i
					for j in range(item["width"]):
						self.space[tmp][j0 + j] = shape[i][j]

		def try_merge(self, item_index, item_position):
			# returns None if it creates an overlap or a new cart with this item added
			item = self.items[item_index]
			shape = item["shape"]
			j0, i0 = item_position
			space_copy = [[self.space[i][j] for j in range(self.cart_width)] for i in range(self.cart_height)]
			for i in range(item["height"]):
				tmp = i0 + i
				for j in range(item["width"]):
					if self.space[tmp][j0 + j] and shape[i][j]:
						return None
					space_copy[tmp][j0 + j] = shape[i][j]
			merged_cart = Cart(self.config, [], [])
			merged_cart.space = space_copy
			return merged_cart

		def __hash__(self):
			return 

	def __init__(self, config):
		self.config = config
		self.items = config["items"]
		self.cart_width, self.cart_height = config["cart_width"], config["cart_height"]
		self.compute_items_sizes()
		self.compute_items_possible_positions()

	def compute_items_sizes(self):
		for item in self.items:
			shape = item["shape"]
			item["height"] = len(shape)
			item["width"] = len(shape[0])
			item["size"] = sum(sum(row) for row in shape)

	def compute_items_possible_positions(self):
		for item in self.items:
			item["possible_positions"] = [(i, j) for i in range(self.cart_height - item.height + 1) for j in range(self.cart_width - item.width + 1)]

	def generate_carts(self, left_indices):
		if len(left_indices) == 1: return [Cart(self.config, [left_indices[0]], [pos]) for pos in self.items[left_indices[0]]["possible_positions"]]
		index = left_indices.pop()
		item = self.items[index]
		# all carts with one less item
		carts = generate_carts([i for i in left_indices])
		# try merging each of them with the removed item
		r = []
		for cart in carts:
			for position in item["possible_positions"]:
				merged_cart = cart.try_merge(item, position)
				if merged_cart != None:
					r.append(merged_cart)
		return r

	def solve(self, min_price=5000):
		must_have_items_index = [i for i in range(len(self.items)) if "Non-discardable" in self.items[i].get("feature", "").split(",") or self.items[i].get("rarity", "") == "Vital Goods"]
		valid_combinations = []
		associated_prices = []
		for n in range(1, len(items) + 1):
			for indices in itertools.combinations(range(len(items)), n):
				total_size = sum(items[i]["size"] for i in indices)
				if total_size > self.cart_size: continue
				total_price = sum(items[i]["value"] for i in indices)
				if total_price < min_price: continue
				if not any(i not in indices for i in must_have_items_index): continue
				if len(indices) == 0: continue
				arrangements = self.generate_carts(indices)
				index = 0
				while index < len(valid_combinations) and associated_prices[index] > total_price:
					index += 1
				valid_combinations.insert(index, [i for i in indices])
				associated_prices.insert(index, total_price)
					
		return valid_combinations, associated_prices

def main():
	content = None

	with open("cart_config.json", "r") as f:
		content = f.read()

	config = json.loads(content)
	solver = CartSolver(config)
	best_combination = solver.solve()

	print(best_combination)

if __name__ == '__main__':
	main()