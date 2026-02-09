"""
Image processing utilities for Daedalus agent.

This module provides methods for resizing and converting images to WebP format,
optimized for web delivery.
"""

import os
from pathlib import Path
from typing import Tuple, Optional, Union
from PIL import Image
from rembg import remove
from io import BytesIO


class ImageProcessor:
    """
    A class for processing images including resizing and format conversion.
    """

    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.tiff'}

    @staticmethod
    def _get_image_format(file_path: Union[str, Path]) -> Optional[str]:
        """
        Autodetect image format from file extension.

        Args:
            file_path: Path to the image file

        Returns:
            Image format string (e.g., 'PNG', 'JPEG', 'WEBP') or None if unsupported
        """
        extension = Path(file_path).suffix.lower()
        
        format_mapping = {
            '.png': 'PNG',
            '.jpg': 'JPEG',
            '.jpeg': 'JPEG',
            '.webp': 'WEBP',
            '.bmp': 'BMP',
            '.gif': 'GIF',
            '.tiff': 'TIFF',
            '.tif': 'TIFF'
        }
        
        return format_mapping.get(extension)

    @staticmethod
    def _calculate_aspect_ratio_dimensions(
        original_width: int,
        original_height: int,
        max_width: Optional[int],
        max_height: Optional[int]
    ) -> Tuple[int, int]:
        """
        Calculate new dimensions while maintaining aspect ratio.

        Args:
            original_width: Original image width
            original_height: Original image height
            max_width: Maximum width constraint
            max_height: Maximum height constraint

        Returns:
            Tuple of (new_width, new_height)
        """
        aspect_ratio = original_width / original_height
        
        if max_width and max_height:
            # Both constraints provided - fit within both
            width_constrained_height = max_width / aspect_ratio
            height_constrained_width = max_height * aspect_ratio
            
            if width_constrained_height <= max_height:
                return (max_width, int(width_constrained_height))
            else:
                return (int(height_constrained_width), max_height)
        elif max_width:
            # Only width constraint
            return (max_width, int(max_width / aspect_ratio))
        elif max_height:
            # Only height constraint
            return (int(max_height * aspect_ratio), max_height)
        else:
            # No constraints (shouldn't reach here due to validation)
            return (original_width, original_height)

    @classmethod
    def process_image(
        cls,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        # Resize options
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        maintain_aspect_ratio: bool = True,
        # Background removal options
        remove_bg: bool = False,
        alpha_matting: bool = False,
        alpha_matting_foreground_threshold: int = 240,
        alpha_matting_background_threshold: int = 10,
        alpha_matting_erode_size: int = 10,
        # WebP conversion options
        convert_to_webp: bool = False,
        webp_quality: int = 85,
        webp_lossless: bool = False,
        webp_method: int = 4,
        # General options
        quality: int = 95,
        strip_metadata: bool = True
    ) -> Path:
        """
        Unified method to process images with multiple operations.

        This method can perform any combination of:
        - Background removal
        - Resizing (with aspect ratio maintenance)
        - WebP conversion
        - Metadata stripping

        Args:
            input_path: Path to the input image
            output_path: Path for output (optional, auto-generated based on operations)
            
            # Resize options
            max_width: Maximum width in pixels (optional)
            max_height: Maximum height in pixels (optional)
            maintain_aspect_ratio: Whether to maintain aspect ratio (default True)
            
            # Background removal options
            remove_bg: Remove background using AI (default False)
            alpha_matting: Use alpha matting for better edge quality (default False)
            alpha_matting_foreground_threshold: Foreground threshold (default 240)
            alpha_matting_background_threshold: Background threshold (default 10)
            alpha_matting_erode_size: Erosion size (default 10)
            
            # WebP conversion options
            convert_to_webp: Convert to WebP format (default False)
            webp_quality: WebP quality 1-100 (default 85)
            webp_lossless: Use lossless WebP compression (default False)
            webp_method: Compression method 0-6 (default 4)
            
            # General options
            quality: Quality for non-WebP formats 1-100 (default 95)
            strip_metadata: Strip EXIF and metadata (default True)

        Returns:
            Path to the processed image

        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If image format is not supported or invalid parameters
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Autodetect format
        img_format = cls._get_image_format(input_path)
        if not img_format:
            raise ValueError(f"Unsupported image format: {input_path.suffix}")
        
        img = None
        
        # Step 1: Remove background if requested
        if remove_bg:
            with open(input_path, 'rb') as input_file:
                input_data = input_file.read()
            
            output_data = remove(
                input_data,
                alpha_matting=alpha_matting,
                alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
                alpha_matting_background_threshold=alpha_matting_background_threshold,
                alpha_matting_erode_size=alpha_matting_erode_size
            )
            
            img = Image.open(BytesIO(output_data))
            # Ensure RGBA mode for transparency
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
        else:
            # Open image normally
            img = Image.open(input_path)
        
        # Step 2: Convert mode if needed for target format
        target_format = 'WEBP' if convert_to_webp else img_format
        
        if target_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        elif target_format == 'WEBP' and img.mode not in ('RGB', 'RGBA'):
            if img.mode == 'P':
                if 'transparency' in img.info:
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
            elif img.mode in ('LA', 'L'):
                if img.mode == 'LA' or remove_bg:
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
            elif img.mode == 'CMYK':
                img = img.convert('RGB')
            else:
                img = img.convert('RGBA' if remove_bg else 'RGB')
        
        # Step 3: Resize if requested
        if max_width or max_height:
            original_width, original_height = img.size
            
            if maintain_aspect_ratio:
                new_width, new_height = cls._calculate_aspect_ratio_dimensions(
                    original_width, original_height, max_width, max_height
                )
            else:
                new_width = max_width if max_width else original_width
                new_height = max_height if max_height else original_height
            
            if (new_width, new_height) != (original_width, original_height):
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Step 4: Determine output path
        if output_path is None:
            suffix = ""
            if remove_bg:
                suffix += "_nobg"
            if max_width or max_height:
                suffix += "_resized"
            if convert_to_webp:
                suffix += "_compressed"
                output_path = input_path.parent / f"{input_path.stem}{suffix}.webp"
            else:
                output_path = input_path.parent / f"{input_path.stem}{suffix}{input_path.suffix}"
        else:
            output_path = Path(output_path)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Step 5: Save the processed image
        save_kwargs = {'format': target_format}
        
        if convert_to_webp:
            save_kwargs.update({
                'quality': webp_quality,
                'method': webp_method,
                'lossless': webp_lossless
            })
        else:
            save_kwargs['quality'] = quality
            if target_format == 'PNG':
                save_kwargs['optimize'] = True
        
        # Handle metadata
        if strip_metadata:
            save_kwargs['exif'] = b''
        else:
            if 'exif' in img.info:
                save_kwargs['exif'] = img.info['exif']
        
        img.save(output_path, **save_kwargs)
        
        return output_path

    @classmethod
    def resize_image(
        cls,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        quality: int = 95,
        maintain_aspect_ratio: bool = True
    ) -> Path:
        """
        Resize an image while maintaining aspect ratio.
        
        This is a convenience wrapper around process_image().
        """
        return cls.process_image(
            input_path=input_path,
            output_path=output_path,
            max_width=max_width,
            max_height=max_height,
            quality=quality,
            maintain_aspect_ratio=maintain_aspect_ratio
        )

    @classmethod
    def convert_to_webp(
        cls,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        quality: int = 85,
        lossless: bool = False,
        method: int = 4,
        strip_metadata: bool = True
    ) -> Path:
        """
        Convert an image to WebP format with compression.
        
        This is a convenience wrapper around process_image().
        """
        return cls.process_image(
            input_path=input_path,
            output_path=output_path,
            convert_to_webp=True,
            webp_quality=quality,
            webp_lossless=lossless,
            webp_method=method,
            strip_metadata=strip_metadata
        )

    @classmethod
    def resize_and_convert_to_webp(
        cls,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        quality: int = 85,
        lossless: bool = False,
        method: int = 4,
        strip_metadata: bool = True
    ) -> Path:
        """
        Resize and convert an image to WebP in a single operation.
        
        This is a convenience wrapper around process_image().
        """
        return cls.process_image(
            input_path=input_path,
            output_path=output_path,
            max_width=max_width,
            max_height=max_height,
            convert_to_webp=True,
            webp_quality=quality,
            webp_lossless=lossless,
            webp_method=method,
            strip_metadata=strip_metadata
        )

    @classmethod
    def remove_background(
        cls,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        alpha_matting: bool = False,
        alpha_matting_foreground_threshold: int = 240,
        alpha_matting_background_threshold: int = 10,
        alpha_matting_erode_size: int = 10
    ) -> Path:
        """
        Remove background from an image using AI-powered background removal.
        
        This is a convenience wrapper around process_image().
        """
        return cls.process_image(
            input_path=input_path,
            output_path=output_path,
            remove_bg=True,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
            alpha_matting_background_threshold=alpha_matting_background_threshold,
            alpha_matting_erode_size=alpha_matting_erode_size
        )

    @classmethod
    def remove_background_and_convert_to_webp(
        cls,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        quality: int = 85,
        alpha_matting: bool = False,
        strip_metadata: bool = True
    ) -> Path:
        """
        Remove background and convert to WebP with transparency in a single operation.
        
        This is a convenience wrapper around process_image().
        """
        return cls.process_image(
            input_path=input_path,
            output_path=output_path,
            remove_bg=True,
            alpha_matting=alpha_matting,
            convert_to_webp=True,
            webp_quality=quality,
            strip_metadata=strip_metadata
        )


# Convenience functions for direct usage

def process_image(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
    remove_bg: bool = False,
    convert_to_webp: bool = False,
    webp_quality: int = 85,
    quality: int = 95,
    alpha_matting: bool = False,
    strip_metadata: bool = True
) -> Path:
    """
    Unified convenience function to process images with multiple operations.

    Args:
        input_path: Path to the input image
        output_path: Path for output (optional, auto-generated based on operations)
        max_width: Maximum width in pixels (optional)
        max_height: Maximum height in pixels (optional)
        remove_bg: Remove background using AI (default False)
        convert_to_webp: Convert to WebP format (default False)
        webp_quality: WebP quality 1-100 (default 85)
        quality: Quality for non-WebP formats 1-100 (default 95)
        alpha_matting: Use alpha matting for better edge quality (default False)
        strip_metadata: Strip EXIF and metadata (default True)

    Returns:
        Path to the processed image

    Examples:
        # Just resize
        process_image("photo.jpg", max_width=1920)
        
        # Resize + convert to WebP
        process_image("photo.jpg", max_width=1920, convert_to_webp=True)
        
        # Remove background + resize + WebP
        process_image("product.jpg", max_width=800, remove_bg=True, convert_to_webp=True)
        
        # Just remove background
        process_image("photo.jpg", remove_bg=True)
    """
    return ImageProcessor.process_image(
        input_path=input_path,
        output_path=output_path,
        max_width=max_width,
        max_height=max_height,
        remove_bg=remove_bg,
        convert_to_webp=convert_to_webp,
        webp_quality=webp_quality,
        quality=quality,
        alpha_matting=alpha_matting,
        strip_metadata=strip_metadata
    )


def resize_image(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
    quality: int = 95
) -> Path:
    """Convenience function to resize an image while maintaining aspect ratio."""
    return ImageProcessor.resize_image(
        input_path, output_path, max_width, max_height, quality
    )


def convert_to_webp(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    quality: int = 85,
    strip_metadata: bool = True
) -> Path:
    """Convenience function to convert an image to WebP format."""
    return ImageProcessor.convert_to_webp(
        input_path, output_path, quality, strip_metadata=strip_metadata
    )


def resize_and_convert_to_webp(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
    quality: int = 85,
    strip_metadata: bool = True
) -> Path:
    """Convenience function to resize and convert an image to WebP in one operation."""
    return ImageProcessor.resize_and_convert_to_webp(
        input_path, output_path, max_width, max_height, quality, strip_metadata=strip_metadata
    )


def remove_background(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    alpha_matting: bool = False
) -> Path:
    """Convenience function to remove background from an image."""
    return ImageProcessor.remove_background(
        input_path, output_path, alpha_matting=alpha_matting
    )


def remove_background_and_convert_to_webp(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    quality: int = 85,
    alpha_matting: bool = False
) -> Path:
    """Convenience function to remove background and convert to WebP in one operation."""
    return ImageProcessor.remove_background_and_convert_to_webp(
        input_path, output_path, quality, alpha_matting=alpha_matting
    )
