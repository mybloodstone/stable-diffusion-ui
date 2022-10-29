import unittest
import requests
import time

url_txt2img = "http://localhost:7860/sdapi/v1/txt2img"
simple_txt2img = {
    "enable_hr": False,
    "denoising_strength": 0,
    "firstphase_width": 0,
    "firstphase_height": 0,
    "prompt": "example prompt",
    "styles": [
      ""
    ],
    "seed": -1,
    "subseed": -1,
    "subseed_strength": 0,
    "seed_resize_from_h": -1,
    "seed_resize_from_w": -1,
    "batch_size": 1,
    "n_iter": 1,
    "steps": 5,
    "cfg_scale": 7,
    "width": 64,
    "height": 64,
    "restore_faces": False,
    "tiling": False,
    "negative_prompt": "",
    "eta": 0,
    "s_churn": 0,
    "s_tmax": 0,
    "s_tmin": 0,
    "s_noise": 1,
    "sampler_index": "Euler a"
}

class TestTxt2ImgWorking(unittest.TestCase):
    def test_txt2img_simple_performed(self):
        self.assertEqual(requests.post(url_txt2img, json=simple_txt2img).status_code, 200)

    def test_txt2img_with_negative_prompt_performed(self):
        params = simple_txt2img.copy()
        params["negative_prompt"] = "example negative prompt"
        self.assertEqual(requests.post(url_txt2img, json=params).status_code, 200)

    def test_txt2img_not_square_image_performed(self):
        params = simple_txt2img.copy()
        params["height"] = 128
        self.assertEqual(requests.post(url_txt2img, json=params).status_code, 200)

    def test_txt2img_with_hrfix_performed(self):
        params = simple_txt2img.copy()
        params["enable_hr"] = True
        self.assertEqual(requests.post(url_txt2img, json=params).status_code, 200)

    def test_txt2img_with_restore_faces_performed(self):
        params = simple_txt2img.copy()
        params["restore_faces"] = True
        self.assertEqual(requests.post(url_txt2img, json=params).status_code, 200)

    def test_txt2img_with_tiling_faces_performed(self):
        params = simple_txt2img.copy()
        params["tiling"] = True
        self.assertEqual(requests.post(url_txt2img, json=params).status_code, 200)

    def test_txt2img_with_vanilla_sampler_performed(self):
        params = simple_txt2img.copy()
        params["sampler_index"] = "PLMS"
        self.assertEqual(requests.post(url_txt2img, json=params).status_code, 200)

    def test_txt2img_multiple_batches_performed(self):
        params = simple_txt2img.copy()
        params["n_iter"] = 2
        self.assertEqual(requests.post(url_txt2img, json=params).status_code, 200)

class TestTxt2ImgCorrectness(unittest.TestCase):
    pass

if __name__ == "__main__":
    unittest.main()
