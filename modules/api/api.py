from modules.api.processing import StableDiffusionTxt2ImgProcessingAPI, StableDiffusionImg2ImgProcessingAPI
from modules.processing import StableDiffusionProcessingTxt2Img, StableDiffusionProcessingImg2Img, process_images
from modules.sd_samplers import all_samplers
import modules.shared as shared
import uvicorn
from fastapi import APIRouter, HTTPException
import json
import io
import base64
from modules.api.models import *
from PIL import Image
from modules.extras import run_extras
from gradio import processing_utils

def upscaler_to_index(name: str):
    try:
        return [x.name.lower() for x in shared.sd_upscalers].index(name.lower())
    except:
        raise HTTPException(status_code=400, detail="Upscaler not found")

sampler_to_index = lambda name: next(filter(lambda row: name.lower() == row[1].name.lower(), enumerate(all_samplers)), None)

# def img_to_base64(img: str):
#     buffer = io.BytesIO()
#     img.save(buffer, format="png")
#     return base64.b64encode(buffer.getvalue())

# def base64_to_bytes(base64Img: str):
#     if "," in base64Img:
#         base64Img = base64Img.split(",")[1]
#     return io.BytesIO(base64.b64decode(base64Img))

# def base64_to_images(base64Imgs: list[str]):
#     imgs = []
#     for img in base64Imgs:
#         img = Image.open(base64_to_bytes(img))
#         imgs.append(img)
#     return imgs

class ImageToImageResponse(BaseModel):
    images: list[str] = Field(default=None, title="Image", description="The generated image in base64 format.")
    parameters: dict
    info: str


class Api:
    def __init__(self, app, queue_lock):
        self.router = APIRouter()
        self.app = app
        self.queue_lock = queue_lock
        self.app.add_api_route("/sdapi/v1/txt2img", self.text2imgapi, methods=["POST"], response_model=TextToImageResponse)
        self.app.add_api_route("/sdapi/v1/img2img", self.img2imgapi, methods=["POST"], response_model=ImageToImageResponse)
        self.app.add_api_route("/sdapi/v1/extra-single-image", self.extras_single_image_api, methods=["POST"], response_model=ExtrasSingleImageResponse)
        self.app.add_api_route("/sdapi/v1/extra-batch-image", self.extras_batch_images_api, methods=["POST"], response_model=ExtrasBatchImagesResponse)

    # def __base64_to_image(self, base64_string):
    #     # if has a comma, deal with prefix
    #     if "," in base64_string:
    #         base64_string = base64_string.split(",")[1]
    #     imgdata = base64.b64decode(base64_string)
    #     # convert base64 to PIL image
    #     return Image.open(io.BytesIO(imgdata))

    def text2imgapi(self, txt2imgreq: StableDiffusionTxt2ImgProcessingAPI):
        sampler_index = sampler_to_index(txt2imgreq.sampler_index)
        
        if sampler_index is None:
            raise HTTPException(status_code=404, detail="Sampler not found") 
        
        populate = txt2imgreq.copy(update={ # Override __init__ params
            "sd_model": shared.sd_model, 
            "sampler_index": sampler_index[0],
            "do_not_save_samples": True,
            "do_not_save_grid": True
            }
        )
        p = StableDiffusionProcessingTxt2Img(**vars(populate))
        # Override object param
        with self.queue_lock:
            processed = process_images(p)
        
        b64images = list(map(processing_utils.encode_pil_to_base64, processed.images))
        
        return TextToImageResponse(images=b64images, parameters=json.dumps(vars(txt2imgreq)), info=processed.info)

    def img2imgapi(self, img2imgreq: StableDiffusionImg2ImgProcessingAPI):
        sampler_index = sampler_to_index(img2imgreq.sampler_index)
        
        if sampler_index is None:
            raise HTTPException(status_code=404, detail="Sampler not found") 


        init_images = img2imgreq.init_images
        if init_images is None:
            raise HTTPException(status_code=404, detail="Init image not found") 

        mask = img2imgreq.mask
        if mask:
            mask = processing_utils.decode_base64_to_image(mask)

        
        populate = img2imgreq.copy(update={ # Override __init__ params
            "sd_model": shared.sd_model, 
            "sampler_index": sampler_index[0],
            "do_not_save_samples": True,
            "do_not_save_grid": True, 
            "mask": mask
            }
        )
        p = StableDiffusionProcessingImg2Img(**vars(populate))

        imgs = []
        for img in init_images:
            img = processing_utils.decode_base64_to_image(img)
            imgs = [img] * p.batch_size

        p.init_images = imgs
        # Override object param
        with self.queue_lock:
            processed = process_images(p)
        
        b64images = list(map(processing_utils.encode_pil_to_base64, processed.images))
        # for i in processed.images:
        #     buffer = io.BytesIO()
        #     i.save(buffer, format="png")
        #     b64images.append(base64.b64encode(buffer.getvalue()))
        return ImageToImageResponse(images=b64images, parameters=vars(img2imgreq), info=processed.info)

    def extras_single_image_api(self, req: ExtrasSingleImageRequest):
        upscaler1Index = upscaler_to_index(req.upscaler_1)
        upscaler2Index = upscaler_to_index(req.upscaler_2)

        reqDict = vars(req)
        reqDict.pop('upscaler_1')
        reqDict.pop('upscaler_2')

        reqDict['image'] = processing_utils.decode_base64_to_file(reqDict['image'])

        with self.queue_lock:
            result = run_extras(**reqDict, extras_upscaler_1=upscaler1Index, extras_upscaler_2=upscaler2Index, extras_mode=0, image_folder="", input_dir="", output_dir="")

        return ExtrasSingleImageResponse(image=processing_utils.encode_pil_to_base64(result[0]), html_info_x=result[1], html_info=result[2])

    def extras_batch_images_api(self, req: ExtrasBatchImagesRequest):
        upscaler1Index = upscaler_to_index(req.upscaler_1)
        upscaler2Index = upscaler_to_index(req.upscaler_2)

        reqDict = vars(req)
        reqDict.pop('upscaler_1')
        reqDict.pop('upscaler_2')

        reqDict['image_folder'] = list(map(processing_utils.decode_base64_to_file, reqDict['imageList']))
        reqDict.pop('imageList')

        with self.queue_lock:
            result = run_extras(**reqDict, extras_upscaler_1=upscaler1Index, extras_upscaler_2=upscaler2Index, extras_mode=1, image="", input_dir="", output_dir="")

        return ExtrasBatchImagesResponse(images=list(map(processing_utils.encode_pil_to_base64, result[0])), html_info_x=result[1], html_info=result[2])
    
    def extras_folder_processing_api(self):
        raise NotImplementedError

    def pnginfoapi(self):
        raise NotImplementedError

    def launch(self, server_name, port):
        self.app.include_router(self.router)
        uvicorn.run(self.app, host=server_name, port=port)
