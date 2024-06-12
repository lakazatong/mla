import os, json
import numpy as np
from skimage.metrics import structural_similarity as ssim
from PIL import Image
from crop import extract_items_from_cart_screenshot

items_folder_path = "assets/items"

def find_most_similar_item_filename(item_image_as_array, item_height, item_width, items_folder_path):
	highest_similarity = -1
	most_similar_item_filename = None
	
	items_height_folder_path = os.path.join(items_folder_path, str(item_height))
	if not os.path.isdir(items_height_folder_path):
		return None
	
	items_width_folder_path = os.path.join(items_height_folder_path, str(item_width))
	if not os.path.isdir(items_width_folder_path):
		return None
	
	item_height, item_width, _ = item_image_as_array.shape

	for filename in sorted(os.listdir(items_width_folder_path)):
		file_path = os.path.join(items_width_folder_path, filename)
		with Image.open(file_path) as candidate_image:
			candidate_array = np.array(candidate_image)
			candidate_height, candidate_width, _ = candidate_array.shape
			n, m = min(item_height, candidate_height), min(item_width, candidate_width)
			similarity = ssim(item_image_as_array[:n, :m, :], candidate_array[:n, :m, :], channel_axis=2)	
			if similarity > highest_similarity:
				highest_similarity = similarity
				most_similar_item_filename = filename
	
	return most_similar_item_filename

def cart_from_image(screenshot_img_path):
	tmp_save_path = "assets/tmp"
	cart_items_info, cart_space, attribute_stone_storage_items_info, attribute_stone_storage_space = extract_items_from_cart_screenshot(screenshot_img_path, tmp_save_path)
	items_file_path = os.listdir(tmp_save_path)
	if len(cart_items_info) + len(attribute_stone_storage_items_info) != len(items_file_path):
		print("oopsie? extract_items_from_cart_screenshot failed?")
		exit(1)
	
	item_id = 1

	def _cart_from_image(items_info, space):
		nonlocal item_id
		for i in range(len(items_info)):
			item_image_path = os.path.join(tmp_save_path, items_file_path[i]).replace("\\", "/")
			item_shape, item_i, item_j = items_info[i]
			item_height, item_width = len(item_shape), len(item_shape[0])
			item_image_as_array = np.array(Image.open(item_image_path))
			most_similar_item_filename = find_most_similar_item_filename(item_image_as_array, item_height, item_width, items_folder_path)
			item_index = int(most_similar_item_filename.split(".")[0])
			space[space == item_id] = item_index
			items_info[i] = (*items_info[i], item_index)
			item_id += 1

	_cart_from_image(cart_items_info, cart_space)
	_cart_from_image(attribute_stone_storage_items_info, attribute_stone_storage_space)
	
	return cart_items_info, cart_space, attribute_stone_storage_items_info, attribute_stone_storage_space

def count_files_in_folder(folder_path):
	count = 0
	for root, dirs, files in os.walk(folder_path):
		count += len(files)
	return count

def main():
	content = None
	with open("cart_config.json", "r") as f:
		content = f.read()
	config = json.loads(content)
	items = config["items"]
	# print("\n".join([f"{i}: {item}" for i, item in enumerate(items) if len(item["shape"]) == 1 and len(item["shape"][0]) == 1 and item.get("rarity", "") == "Rare Goods"]))
	print(f"current progress = {round(count_files_in_folder(items_folder_path) / len(items) * 100, 0)}%")
	cart_items_info, cart_space, attribute_stone_storage_items_info, attribute_stone_storage_space = cart_from_image("assets/ss/5.png")
	for item_info in cart_items_info:
		print(item_info)
	for item_info in attribute_stone_storage_items_info:
		print(item_info)
	print()
	print(cart_space)
	print(attribute_stone_storage_space)

if __name__ == "__main__":
	main()
