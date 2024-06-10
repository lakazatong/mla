import os, json
import numpy as np
from skimage.metrics import structural_similarity as ssim
from PIL import Image
from crop import extract_items_from_cart_image

items_folder_path = "assets/items"

def crop_to_match(candidate_array, target_height, target_width):
	height, width, _ = candidate_array.shape
	start_i = (height - target_height) // 2
	start_j = (width - target_width) // 2
	return candidate_array[start_i:start_i + target_height, start_j:start_j + target_width]

def find_most_similar_item(item_image_as_array, item_height, item_width, items_folder_path):
	highest_similarity = -1
	most_similar_item = None
	
	items_height_folder_path = os.path.join(items_folder_path, str(item_height))
	if not os.path.isdir(items_height_folder_path):
		return None
	
	items_width_folder_path = os.path.join(items_height_folder_path, str(item_width))
	if not os.path.isdir(items_width_folder_path):
		return None
	
	target_height, target_width, _ = item_image_as_array.shape

	for filename in sorted(os.listdir(items_width_folder_path)):
		file_path = os.path.join(items_width_folder_path, filename)
		with Image.open(file_path) as candidate_image:
			candidate_array = np.array(candidate_image)
			candidate_height, candidate_width, _ = candidate_array.shape
			
			if candidate_height > target_height or candidate_width > target_width:
				candidate_array = crop_to_match(candidate_array, target_height, target_width)
			elif candidate_height < target_height or candidate_width < target_width:
				item_image_as_array = crop_to_match(item_image_as_array, candidate_height, candidate_width)
			
			similarity = ssim(item_image_as_array, candidate_array, channel_axis=2)
							
			if similarity > highest_similarity:
				highest_similarity = similarity
				most_similar_item = filename
	
	return most_similar_item

def items_id_from_cart_image(cart_img_path):
	tmp_save_path = "assets/tmp"
	items_info, cart_space = extract_items_from_cart_image(cart_img_path, tmp_save_path)
	items_file_path = os.listdir(tmp_save_path)
	if len(items_info) != len(items_file_path):
		print("oopsie? extract_items_from_cart_image failed?")
		exit(1)
	for i in range(len(items_file_path)):
		item_image_path = os.path.join(tmp_save_path, items_file_path[i]).replace("\\", "/")
		item_shape, item_i, item_j = items_info[i]
		item_height, item_width = len(item_shape), len(item_shape[0])
		item_image_as_array = np.array(Image.open(item_image_path))
		most_similar_item = find_most_similar_item(item_image_as_array, item_height, item_width, items_folder_path)
		print(item_image_path, most_similar_item)

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
	# print("\n".join([f"{i}: {item}" for i, item in enumerate(items) if len(item["shape"]) == 2 and len(item["shape"][0]) == 2 and item["rarity"] == "Normal Goods"]))
	print(f"current progress = {round(count_files_in_folder(items_folder_path) / len(items) * 100, 0)}%")
	items_id_from_cart_image("assets/ss/1.png")

if __name__ == "__main__":
	main()
