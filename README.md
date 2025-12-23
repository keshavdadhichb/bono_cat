# Bono AI Fashion Catalog Pipeline

An automated pipeline that transforms flat-lay t-shirt photos into a professional PDF catalog featuring AI-generated fashion models wearing the garments.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🎯 Overview

This pipeline automates the creation of fashion catalogs by:

1. **Watching** Google Drive for new garment images
2. **Generating** photorealistic AI models wearing the garments (via RunPod + ComfyUI)
3. **Assembling** a modern, print-ready PDF catalog
4. **Uploading** outputs back to Google Drive

### Current Phase: Teen Boys (13-15 Years) | Brand: Bono

The modular architecture supports easy expansion to other demographics (Infants, Girls, etc.).

---

## 📋 Prerequisites

- **Python 3.9+**
- **RunPod Account** with serverless endpoint configured
- **Google Cloud Project** with Drive API enabled
- **ComfyUI** deployed on RunPod with required models

### Required Models on RunPod

Your ComfyUI instance needs these models installed:

| Model | Purpose | Download |
|-------|---------|----------|
| `juggernautXL_v9.safetensors` | Base SDXL model | [CivitAI](https://civitai.com/models/133005) |
| `idm_vton_model.safetensors` | Virtual try-on | [HuggingFace](https://huggingface.co/yisol/IDM-VTON) |
| `face_yolov8m.pt` | Face detection | Included with FaceDetailer |
| `sam_vit_b_01ec64.pth` | Segmentation | [GitHub](https://github.com/facebookresearch/segment-anything) |
| `4x-UltraSharp.pth` | Upscaling | [OpenModelDB](https://openmodeldb.info/) |

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/keshavdadhichb/bono_cat.git
cd bono_cat
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# RunPod Configuration
RUNPOD_API_KEY=rpa_XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
RUNPOD_ENDPOINT_ID=your_comfyui_endpoint_id

# Hugging Face (optional, for model downloads)
HUGGINGFACE_TOKEN=hf_XXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Google Drive Configuration
GOOGLE_DRIVE_CREDENTIALS_PATH=./credentials.json
GOOGLE_DRIVE_INPUT_FOLDER_ID=your_input_folder_id
GOOGLE_DRIVE_OUTPUT_FOLDER_ID=your_output_folder_id

# Pipeline Settings
DEFAULT_CATEGORY=teen_boy
DEFAULT_BRAND=bono
OUTPUT_RESOLUTION=4096
```

### 5. Set Up Google Drive API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the **Google Drive API**
4. Go to **Credentials** → Create **OAuth 2.0 Client ID**
5. Download the JSON and save as `credentials.json` in project root
6. First run will open a browser for OAuth consent

### 6. Add Brand Assets

Place your brand assets in the `assets` folder:

```
assets/
├── logos/
│   └── bono.png
└── fonts/
    └── (optional custom fonts)
```

---

## 💻 Usage

### Validate Configuration

```bash
python pipeline.py validate
```

### Process a Local Batch

```bash
python pipeline.py batch --input ./tests --output ./output
```

### Watch Google Drive for New Batches

```bash
python pipeline.py watch --poll-interval 60
```

### Generate PDF from Existing Images

```bash
python pipeline.py catalog --images ./output/HighRes_Images --output catalog.pdf
```

### Enable Debug Mode

```bash
python pipeline.py --debug batch --input ./tests --output ./output
```

---

## 📁 Project Structure

```
bono_cat/
├── pipeline.py              # Main CLI entry point
├── workflow_api.json        # ComfyUI workflow definition
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
│
├── src/
│   ├── config.py            # Configuration management
│   │
│   ├── generators/          # AI Generation (Modular)
│   │   ├── base.py          # BaseGenerator abstract class
│   │   ├── teen_boy.py      # Teen Boys (Phase 1)
│   │   └── infant.py        # Infants (Future)
│   │
│   ├── integrations/        # External Services
│   │   ├── runpod.py        # RunPod API client
│   │   └── google_drive.py  # Google Drive client
│   │
│   ├── catalog/             # PDF Generation
│   │   ├── assembler.py     # PDF assembly
│   │   └── templates.py     # Layout styles
│   │
│   └── utils/               # Utilities
│       ├── image.py         # Image processing
│       └── logging.py       # Structured logging
│
├── assets/                  # Brand assets
│   └── logos/bono.png
│
└── tests/                   # Test images
    ├── test1.png
    └── test2.png
```

---

## 🔧 Configuration

### Switching Categories

Edit `.env` or pass configuration programmatically:

```python
from src.config import Config, PipelineConfig

config = Config.from_env()
config.pipeline.category = "infant"  # Switch to infant generator
```

### Adding New Categories

1. Create a new generator in `src/generators/`:

```python
# src/generators/teen_girl.py
from .base import BaseGenerator, GenerationConfig

class TeenGirlGenerator(BaseGenerator):
    POSITIVE_PROMPT = "..."
    
    def get_model_prompt(self) -> str:
        return self.POSITIVE_PROMPT
    # ... implement other methods
```

2. Register in `pipeline.py`:

```python
GENERATORS = {
    "teen_boy": TeenBoyGenerator,
    "teen_girl": TeenGirlGenerator,  # Add new
    "infant": InfantGenerator,
}
```

---

## 🖼️ Google Drive Folder Structure

```
Input/
├── Batch_01/
│   ├── tee_red.png
│   ├── tee_blue.png
│   └── tee_green.png
└── Config/
    └── config.json (optional batch settings)

Output/
├── Batch_01/
│   ├── Final_Catalog_Bono.pdf
│   └── HighRes_Images/
│       ├── full_body_001.png
│       ├── closeup_001.png
│       └── ...
```

---

## 🎨 Catalog Design

The PDF catalog features a modern, minimalist design:

- **Cover Page**: Brand logo, tagline, collection title
- **Product Pages**: Full-body shot + optional closeup
- **Back Cover**: Brand info and contact

### Customizing Style

Edit `src/catalog/templates.py`:

```python
@dataclass
class ModernMinimalistStyle:
    colors: ColorScheme = field(default_factory=ColorScheme)
    typography: Typography = field(default_factory=Typography)
    # Customize fonts, colors, spacing...
```

---

## 🐛 Troubleshooting

### "No images found"
- Ensure images are PNG/JPG/JPEG/WEBP format
- Check file permissions

### "RunPod job timeout"
- Increase `RUNPOD_TIMEOUT` in `.env`
- Check RunPod endpoint status
- Verify models are loaded correctly

### "Google Drive authentication failed"
- Delete `token.json` and re-authenticate
- Verify OAuth credentials are for correct project
- Ensure Drive API is enabled

### "ComfyUI workflow errors"
- Verify all required custom nodes are installed
- Check model file names match workflow
- Review RunPod logs for detailed errors

---

## 📄 License

MIT License - Feel free to modify and use commercially.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📞 Support

For issues or questions, open a GitHub issue or contact the development team.
