"""
Layout templates for catalog design.

Provides style configurations and page templates for creating
modern, minimalist fashion catalog layouts.
"""

from dataclasses import dataclass, field
from typing import Tuple, Optional, List
from enum import Enum


class PageLayout(Enum):
    """Available page layouts."""
    SINGLE_FULL = "single_full"  # One full-body image
    SPLIT_HORIZONTAL = "split_horizontal"  # Full + closeup side by side
    SPLIT_VERTICAL = "split_vertical"  # Full on top, closeup below
    COLLAGE = "collage"  # Creative multi-image layout
    COVER = "cover"  # Cover page layout
    BACK_COVER = "back_cover"


@dataclass
class ColorScheme:
    """Color scheme for the catalog."""
    primary: Tuple[int, int, int] = (0, 0, 0)  # Black
    secondary: Tuple[int, int, int] = (255, 255, 255)  # White
    accent: Tuple[int, int, int] = (41, 128, 185)  # Modern blue
    background: Tuple[int, int, int] = (250, 250, 250)  # Light grey
    text: Tuple[int, int, int] = (33, 33, 33)  # Dark grey
    text_light: Tuple[int, int, int] = (120, 120, 120)  # Light text


@dataclass
class Typography:
    """Typography settings."""
    heading_font: str = "Helvetica-Bold"
    body_font: str = "Helvetica"
    accent_font: str = "Helvetica-Oblique"
    
    # Font sizes (in points)
    title_size: int = 48
    heading_size: int = 28
    subheading_size: int = 18
    body_size: int = 12
    caption_size: int = 10
    
    # Line heights
    heading_leading: float = 1.2
    body_leading: float = 1.5


@dataclass
class Spacing:
    """Spacing and margin settings (in points, 72 points = 1 inch)."""
    page_margin: int = 50
    content_padding: int = 20
    image_gap: int = 15
    text_image_gap: int = 25
    
    # Footer area
    footer_height: int = 60
    header_height: int = 40


@dataclass
class ModernMinimalistStyle:
    """
    Modern minimalist style configuration for Bono catalog.
    
    Emphasizes clean lines, whitespace, and bold product presentation.
    """
    
    name: str = "Modern Minimalist"
    colors: ColorScheme = field(default_factory=ColorScheme)
    typography: Typography = field(default_factory=Typography)
    spacing: Spacing = field(default_factory=Spacing)
    
    # Page settings (A4 size in points)
    page_width: float = 595.28  # 210mm
    page_height: float = 841.89  # 297mm
    
    # Image settings
    image_border_radius: int = 0  # Sharp corners for modern look
    image_shadow: bool = False  # Clean, flat design
    image_border: bool = False
    
    # Logo settings
    logo_width: int = 80
    logo_height: int = 40
    logo_position: str = "top_left"  # or "top_center", "bottom_center"
    
    def get_content_width(self) -> float:
        """Get usable content width."""
        return self.page_width - (2 * self.spacing.page_margin)
    
    def get_content_height(self) -> float:
        """Get usable content height (excluding header/footer)."""
        return (
            self.page_height 
            - (2 * self.spacing.page_margin)
            - self.spacing.header_height
            - self.spacing.footer_height
        )


@dataclass
class CatalogPage:
    """Represents a single page in the catalog."""
    
    page_number: int
    layout: PageLayout
    
    # Primary image (full body shot)
    full_body_image: Optional[str] = None
    
    # Secondary image (closeup/detail)
    closeup_image: Optional[str] = None
    
    # Product info
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    product_description: Optional[str] = None
    
    # Additional images for collage layout
    additional_images: List[str] = field(default_factory=list)
    
    # Custom text elements
    headline: Optional[str] = None
    tagline: Optional[str] = None


@dataclass  
class CatalogConfig:
    """Configuration for the entire catalog."""
    
    brand_name: str = "BONO"
    tagline: str = "Streetwear for the Next Generation"
    catalog_title: str = "Collection 2024"
    
    # Brand assets
    logo_path: Optional[str] = None
    
    # Style
    style: ModernMinimalistStyle = field(default_factory=ModernMinimalistStyle)
    
    # Pages configuration
    include_cover: bool = True
    include_back_cover: bool = True
    include_page_numbers: bool = True
    
    # Output settings
    output_dpi: int = 300
    compress_images: bool = False
