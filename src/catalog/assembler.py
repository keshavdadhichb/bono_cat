"""
PDF Catalog Assembler.

Generates professional, print-ready PDF catalogs with modern,
minimalist design for fashion products.
"""

from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import Color, HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
import structlog

from .templates import (
    ModernMinimalistStyle,
    CatalogPage,
    CatalogConfig,
    PageLayout
)

logger = structlog.get_logger()


class CatalogAssembler:
    """
    Assembles generated images into a branded PDF catalog.
    
    Creates a modern, minimalist catalog with:
    - Cover page with brand logo
    - Product pages with full-body and closeup images
    - Consistent styling and typography
    - Print-ready output
    
    Example:
        assembler = CatalogAssembler(
            brand="Bono",
            logo_path="./assets/bono.png"
        )
        assembler.create_catalog(images, "output/catalog.pdf")
    """
    
    def __init__(
        self,
        brand: str = "BONO",
        logo_path: Optional[str] = None,
        config: Optional[CatalogConfig] = None
    ):
        """
        Initialize the catalog assembler.
        
        Args:
            brand: Brand name to display
            logo_path: Path to brand logo image
            config: Optional catalog configuration
        """
        self.brand = brand
        self.logo_path = logo_path
        self.config = config or CatalogConfig(brand_name=brand, logo_path=logo_path)
        self.style = self.config.style
        
        # PDF canvas (created during generation)
        self.canvas: Optional[canvas.Canvas] = None
        self.current_page = 0
    
    def create_catalog(
        self,
        images: List[dict],
        output_path: str,
        include_cover: bool = True
    ) -> str:
        """
        Create a complete catalog PDF.
        
        Args:
            images: List of image dictionaries with 'full_body' and 'closeup' keys
            output_path: Path for the output PDF
            include_cover: Whether to include cover page
            
        Returns:
            str: Path to generated PDF
        """
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create canvas
        self.canvas = canvas.Canvas(
            output_path,
            pagesize=(self.style.page_width, self.style.page_height)
        )
        self.canvas.setTitle(f"{self.brand} Catalog")
        self.canvas.setAuthor(self.brand)
        
        logger.info("Creating catalog", pages=len(images) + (2 if include_cover else 0))
        
        # Cover page
        if include_cover:
            self._create_cover_page()
        
        # Product pages
        for i, image_set in enumerate(images):
            self._create_product_page(
                full_body=image_set.get('full_body') or image_set.get('output_path'),
                closeup=image_set.get('closeup'),
                product_name=image_set.get('product_name', f"Style #{i+1}"),
                product_code=image_set.get('product_code'),
                page_number=i + 1
            )
        
        # Back cover
        if include_cover:
            self._create_back_cover()
        
        # Save PDF
        self.canvas.save()
        logger.info("Catalog created", path=output_path)
        
        return output_path
    
    def _create_cover_page(self):
        """Create the catalog cover page."""
        c = self.canvas
        w, h = self.style.page_width, self.style.page_height
        
        # Background - clean white with subtle gradient effect
        c.setFillColor(HexColor("#FFFFFF"))
        c.rect(0, 0, w, h, fill=1, stroke=0)
        
        # Optional subtle accent bar at top
        c.setFillColor(HexColor("#1a1a1a"))
        c.rect(0, h - 8, w, 8, fill=1, stroke=0)
        
        # Brand logo (centered, upper portion)
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                logo = ImageReader(self.logo_path)
                logo_w = 180
                logo_h = 90
                c.drawImage(
                    logo,
                    (w - logo_w) / 2,
                    h - 200,
                    width=logo_w,
                    height=logo_h,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except Exception as e:
                logger.warning("Could not load logo", error=str(e))
        
        # Brand name (if no logo or as fallback)
        if not self.logo_path or not os.path.exists(self.logo_path):
            c.setFont(self.style.typography.heading_font, 72)
            c.setFillColor(HexColor("#1a1a1a"))
            text_w = c.stringWidth(self.brand, self.style.typography.heading_font, 72)
            c.drawString((w - text_w) / 2, h - 180, self.brand)
        
        # Tagline
        c.setFont(self.style.typography.accent_font, 18)
        c.setFillColor(HexColor("#666666"))
        tagline = self.config.tagline
        text_w = c.stringWidth(tagline, self.style.typography.accent_font, 18)
        c.drawString((w - text_w) / 2, h - 240, tagline)
        
        # Collection title
        c.setFont(self.style.typography.body_font, 24)
        c.setFillColor(HexColor("#333333"))
        title = self.config.catalog_title
        text_w = c.stringWidth(title, self.style.typography.body_font, 24)
        c.drawString((w - text_w) / 2, h / 2 + 50, title)
        
        # Decorative line
        c.setStrokeColor(HexColor("#e0e0e0"))
        c.setLineWidth(2)
        c.line(w/2 - 100, h/2, w/2 + 100, h/2)
        
        # Category indicator
        c.setFont(self.style.typography.body_font, 14)
        c.setFillColor(HexColor("#888888"))
        category = "TEEN BOYS COLLECTION"
        text_w = c.stringWidth(category, self.style.typography.body_font, 14)
        c.drawString((w - text_w) / 2, 100, category)
        
        c.showPage()
        self.current_page += 1
    
    def _create_product_page(
        self,
        full_body: str,
        closeup: Optional[str],
        product_name: str,
        product_code: Optional[str] = None,
        page_number: int = 1
    ):
        """
        Create a product page with full-body and closeup images.
        
        Args:
            full_body: Path to full-body image
            closeup: Optional path to closeup image
            product_name: Product name/title
            product_code: Optional product code
            page_number: Page number for footer
        """
        c = self.canvas
        w, h = self.style.page_width, self.style.page_height
        margin = self.style.spacing.page_margin
        
        # Background
        c.setFillColor(HexColor("#FAFAFA"))
        c.rect(0, 0, w, h, fill=1, stroke=0)
        
        # Header with brand
        self._draw_page_header()
        
        content_top = h - margin - self.style.spacing.header_height
        content_bottom = margin + self.style.spacing.footer_height
        content_height = content_top - content_bottom
        
        if closeup and os.path.exists(closeup):
            # Two-image layout: 60% full body, 40% closeup
            self._draw_split_layout(
                full_body, closeup,
                margin, content_bottom, w - 2*margin, content_height
            )
        else:
            # Single image layout: centered large image
            self._draw_single_image(
                full_body,
                margin, content_bottom, w - 2*margin, content_height
            )
        
        # Product info
        self._draw_product_info(product_name, product_code)
        
        # Footer with page number
        self._draw_page_footer(page_number)
        
        c.showPage()
        self.current_page += 1
    
    def _draw_page_header(self):
        """Draw the page header with brand logo/name."""
        c = self.canvas
        w = self.style.page_width
        h = self.style.page_height
        margin = self.style.spacing.page_margin
        
        # Small brand logo or name in header
        c.setFont(self.style.typography.heading_font, 14)
        c.setFillColor(HexColor("#333333"))
        c.drawString(margin, h - margin + 5, self.brand)
        
        # Subtle line under header
        c.setStrokeColor(HexColor("#E0E0E0"))
        c.setLineWidth(0.5)
        c.line(margin, h - margin - 10, w - margin, h - margin - 10)
    
    def _draw_single_image(
        self,
        image_path: str,
        x: float,
        y: float,
        width: float,
        height: float
    ):
        """Draw a single centered image."""
        c = self.canvas
        
        if not os.path.exists(image_path):
            logger.warning("Image not found", path=image_path)
            return
        
        try:
            img = ImageReader(image_path)
            
            # Calculate dimensions to fit while maintaining aspect ratio
            img_width, img_height = img.getSize()
            aspect = img_width / img_height
            
            # Fit within bounds
            if width / height > aspect:
                # Height constrained
                draw_height = height * 0.9
                draw_width = draw_height * aspect
            else:
                # Width constrained
                draw_width = width * 0.8
                draw_height = draw_width / aspect
            
            # Center the image
            draw_x = x + (width - draw_width) / 2
            draw_y = y + (height - draw_height) / 2
            
            c.drawImage(
                img,
                draw_x, draw_y,
                width=draw_width,
                height=draw_height,
                preserveAspectRatio=True,
                mask='auto'
            )
            
        except Exception as e:
            logger.error("Failed to draw image", path=image_path, error=str(e))
    
    def _draw_split_layout(
        self,
        full_body_path: str,
        closeup_path: str,
        x: float,
        y: float,
        width: float,
        height: float
    ):
        """Draw two images in a split layout."""
        c = self.canvas
        gap = self.style.spacing.image_gap
        
        # 60/40 split
        left_width = width * 0.58
        right_width = width * 0.38
        
        # Draw full body on left
        self._draw_single_image(full_body_path, x, y, left_width, height)
        
        # Draw closeup on right
        self._draw_single_image(
            closeup_path,
            x + left_width + gap,
            y + height * 0.2,  # Slightly lower for visual balance
            right_width,
            height * 0.6
        )
    
    def _draw_product_info(
        self,
        product_name: str,
        product_code: Optional[str] = None
    ):
        """Draw product information."""
        c = self.canvas
        margin = self.style.spacing.page_margin
        
        # Product name
        c.setFont(self.style.typography.heading_font, 16)
        c.setFillColor(HexColor("#1a1a1a"))
        c.drawString(margin, margin + 30, product_name)
        
        # Product code
        if product_code:
            c.setFont(self.style.typography.body_font, 11)
            c.setFillColor(HexColor("#888888"))
            c.drawString(margin, margin + 12, f"Code: {product_code}")
    
    def _draw_page_footer(self, page_number: int):
        """Draw page footer with page number."""
        c = self.canvas
        w = self.style.page_width
        margin = self.style.spacing.page_margin
        
        if self.config.include_page_numbers:
            c.setFont(self.style.typography.body_font, 10)
            c.setFillColor(HexColor("#999999"))
            page_text = str(page_number)
            text_w = c.stringWidth(page_text, self.style.typography.body_font, 10)
            c.drawString((w - text_w) / 2, margin - 10, page_text)
    
    def _create_back_cover(self):
        """Create the catalog back cover."""
        c = self.canvas
        w, h = self.style.page_width, self.style.page_height
        
        # Background
        c.setFillColor(HexColor("#1a1a1a"))
        c.rect(0, 0, w, h, fill=1, stroke=0)
        
        # Brand logo (white version would be ideal)
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                logo = ImageReader(self.logo_path)
                logo_w = 120
                logo_h = 60
                c.drawImage(
                    logo,
                    (w - logo_w) / 2,
                    h / 2 + 20,
                    width=logo_w,
                    height=logo_h,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except:
                pass
        
        # Brand name
        c.setFont(self.style.typography.heading_font, 36)
        c.setFillColor(HexColor("#FFFFFF"))
        text_w = c.stringWidth(self.brand, self.style.typography.heading_font, 36)
        c.drawString((w - text_w) / 2, h / 2 - 30, self.brand)
        
        # Contact/website placeholder
        c.setFont(self.style.typography.body_font, 12)
        c.setFillColor(HexColor("#888888"))
        contact = "www.bono.com | @bono_official"
        text_w = c.stringWidth(contact, self.style.typography.body_font, 12)
        c.drawString((w - text_w) / 2, 60, contact)
        
        c.showPage()
