import numpy as np
import logging
import os
import gc
import shutil
import tempfile
from pathlib import Path
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create cache directory for models
CACHE_DIR = Path.home() / ".cache" / "huggingface"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ['TRANSFORMERS_CACHE'] = str(CACHE_DIR)
os.environ['HF_HOME'] = str(CACHE_DIR)

try:
    import torch
    import transformers
    from transformers import pipeline
    import diffusers
    from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
    HAS_ML_DEPS = True
except ImportError as e:
    HAS_ML_DEPS = False
    logger.warning(f"ML dependencies not available: {str(e)}")
    logger.warning("Image generation and speech recognition will be disabled.")

class LocalModelHandler:
    def __init__(self):
        self.device = None
        self.text_to_image = None
        self.voice_to_text = None
        if HAS_ML_DEPS:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self.device}")
        else:
            logger.warning("ML features disabled due to missing dependencies")

    @staticmethod
    def _clear_memory():
        """Clear memory and caches"""
        try:
            gc.collect()
            torch.cuda.empty_cache()
            if hasattr(torch, 'compile'):
                torch._dynamo.reset()
        except:
            pass

    @staticmethod
    def _find_best_cache_dir():
        """Find directory with most free space"""
        drives = [tempfile.gettempdir(), str(CACHE_DIR), os.path.expanduser("~"), "."]
        best_path = max(drives, key=lambda p: shutil.disk_usage(p).free if os.path.exists(p) else 0)
        cache_dir = os.path.join(best_path, ".sd_cache")
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir
        
    def init_stable_diffusion(self):
        """Initialize Stable Diffusion model with minimal disk and memory usage"""
        if not HAS_ML_DEPS:
            logger.error("Stable Diffusion not available - missing dependencies")
            return False
            
        try:
            if self.text_to_image is None:
                logger.info("Loading Stable Diffusion model...")
                
                # Clear memory before loading
                self._clear_memory()
                
                # Find best cache location
                cache_dir = self._find_best_cache_dir()
                total, used, free = shutil.disk_usage(cache_dir)
                logger.info(f"Using cache dir: {cache_dir} with {free // (2**30)}GB free")
                logger.info(f"Free disk space: {free // (2**30)} GB")
                # Use smallest possible model with minimal settings
                model_id = "CompVis/stable-diffusion-v1-1"
                
                # Configure optimized download directory
                import tempfile
                import os
                
                # Try to find directory with most free space
                tmp_dir = tempfile.gettempdir()
                drives = [tmp_dir, os.path.expanduser("~"), "."]
                best_path = max(drives, key=lambda p: shutil.disk_usage(p).free if os.path.exists(p) else 0)
                
                cache_dir = os.path.join(best_path, ".stable_diffusion_cache")
                os.makedirs(cache_dir, exist_ok=True)
                
                try:
                    # Load model with minimal settings
                    self.text_to_image = StableDiffusionPipeline.from_pretrained(
                        "CompVis/stable-diffusion-v1-1",
                        torch_dtype=torch.float16,
                        revision="fp16",
                        cache_dir=cache_dir,
                        local_files_only=False,
                        safety_checker=None,
                        requires_safety_checker=False,
                        use_auth_token=False,
                        low_memory=True,
                        variant="fp16"
                    )
                except Exception as e1:
                    logger.warning(f"Failed to load model in temp dir: {e1}")
                    try:
                        # Try loading with absolute minimum settings
                        self.text_to_image = StableDiffusionPipeline.from_pretrained(
                            model_id,
                            torch_dtype=torch.float32,
                            cache_dir=CACHE_DIR,
                            local_files_only=True,
                            safety_checker=None,
                            requires_safety_checker=False,
                            use_auth_token=False,
                            low_memory=True
                        )
                    except Exception as e2:
                        logger.error(f"Failed to load model: {e2}")
                        return False
                
                # Enable memory optimizations
                if self.text_to_image is not None:
                    try:
                        self.text_to_image.enable_attention_slicing("max")
                        if hasattr(self.text_to_image, 'enable_model_cpu_offload'):
                            self.text_to_image.enable_model_cpu_offload()
                        if hasattr(self.text_to_image, 'enable_sequential_cpu_offload'):
                            self.text_to_image.enable_sequential_cpu_offload()
                        if hasattr(self.text_to_image, 'enable_vae_slicing'):
                            self.text_to_image.enable_vae_slicing()
                    except Exception as e:
                        logger.warning(f"Could not enable all optimizations: {e}")
                    
                logger.info("Model loaded with minimal configuration")
                return True
                
        except Exception as e:
            logger.error(f"Error loading Stable Diffusion: {e}")
            logger.info("Check if you have enough disk space and RAM available")
            return False
            
    def init_voice_recognition(self):
        """Initialize Whisper model for voice recognition"""
        if not HAS_ML_DEPS:
            logger.error("Whisper not available - missing dependencies")
            return False
            
        try:
            if self.voice_to_text is None:
                logger.info("Loading Whisper model...")
                # Use smaller model for better performance
                model_name = "openai/whisper-tiny"
                
                try:
                    # Try tiny model first
                    self.voice_to_text = pipeline(
                        "automatic-speech-recognition",
                        model=model_name,
                        device=self.device,
                        cache_dir=CACHE_DIR
                    )
                except Exception as e1:
                    logger.warning(f"Error loading tiny model: {e1}, trying base model...")
                    # Fallback to base model
                    model_name = "openai/whisper-base"
                    self.voice_to_text = pipeline(
                        "automatic-speech-recognition",
                        model=model_name,
                        device=self.device,
                        cache_dir=CACHE_DIR
                    )
                
                logger.info(f"Whisper model {model_name} loaded successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error loading Whisper: {e}")
            logger.info("Check if you have enough disk space and RAM available")
            return False
    
    def generate_image(self, prompt, num_inference_steps=20):
        """Generate image from text prompt with progressive quality reduction on memory constraints"""
        if not HAS_ML_DEPS:
            logger.error("Image generation not available - missing dependencies")
            return None
            
        try:
            if not self.text_to_image:
                if not self.init_stable_diffusion():
                    logger.error("Failed to initialize model")
                    return None
            
            # Clean up prompt
            prompt = prompt.strip()[:100]  # Limit length
            
            # Use system temp directory if cache is full
            import tempfile
            tmp_dir = tempfile.gettempdir()
            
            logger.info(f"Generating image for prompt: {prompt}")
            try:
                # Clear memory
                try:
                    torch.cuda.empty_cache()
                    import gc
                    gc.collect()
                except:
                    pass
                    
                with torch.inference_mode():
                    # Try progressively lower quality settings until success
                    for settings in [
                        {"height": 512, "width": 512, "steps": 20, "guidance": 7.0},
                        {"height": 384, "width": 384, "steps": 15, "guidance": 6.0},
                        {"height": 256, "width": 256, "steps": 10, "guidance": 5.0},
                        {"height": 128, "width": 128, "steps": 5, "guidance": 3.0}
                    ]:
                        try:
                            image = self.text_to_image(
                                prompt,
                                num_inference_steps=settings["steps"],
                                guidance_scale=settings["guidance"],
                                height=settings["height"],
                                width=settings["width"],
                                output_type="pil"
                            ).images[0]
                            # If successful, break out of the loop
                            break
                        except RuntimeError as e:
                            if "out of memory" in str(e) and settings != {"height": 128, "width": 128, "steps": 5, "guidance": 3.0}:
                                # Clear memory and try next settings
                                torch.cuda.empty_cache()
                                gc.collect()
                                continue
                            raise  # Re-raise if it's the last attempt or not a memory error
                    
                try:
                    torch.cuda.empty_cache()
                    gc.collect()
                except:
                    pass
                    
                logger.info("Image generated successfully")
                return image
                    
            except RuntimeError as e:
                if "out of memory" in str(e):
                    logger.warning("Memory error - final attempt with minimal settings")
                    try:
                        # Clear everything possible
                        torch.cuda.empty_cache()
                        gc.collect()
                        import sys
                        if hasattr(sys, 'exc_clear'):
                            sys.exc_clear()
                    except:
                        pass
                        
                    # Last resort with absolute minimum
                    image = self.text_to_image(
                        prompt[:50],  # Even shorter prompt
                        num_inference_steps=2,
                        guidance_scale=1.0,
                        height=32,
                        width=32,
                        output_type="np"
                    ).images[0]
                    
                    # Try to resize
                    try:
                        from PIL import Image
                        image = Image.fromarray(image)
                        image = image.resize((96, 96), Image.Resampling.LANCZOS)
                    except:
                        pass
                        
                    return image
                    
                raise  # Re-raise if not memory error
                    
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def transcribe_audio(self, audio_file):
        """Transcribe audio to text using local Whisper model"""
        if not HAS_ML_DEPS:
            logger.error("Audio transcription not available - missing dependencies")
            return None
            
        try:
            if not self.voice_to_text:
                if not self.init_voice_recognition():
                    return None
                    
            logger.info("Transcribing audio...")
            result = self.voice_to_text(audio_file)
            text = result["text"]
            logger.info(f"Audio transcribed: {text}")
            return text
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None
