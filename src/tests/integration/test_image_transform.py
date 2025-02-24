"""
Integration tests for image transformation functionality.
"""
from tests.base_test import BaseTestCase
from PIL import Image
import numpy as np
import math
from IT8951.img_transform import rotate_image, prepare_image_for_display

class TestImageTransform(BaseTestCase):
    """Test cases for image transformation functions."""

    def setUp(self):
        super().setUp()
        # Create test image with recognizable pattern
        self.test_image = Image.new('L', (100, 50))
        # Draw a line from top-left to bottom-right
        for i in range(50):
            self.test_image.putpixel((i*2, i), 0)

    def test_arbitrary_rotation(self):
        """Test rotation by arbitrary angles."""
        test_angles = [0, 30, 45, 60, 90, 120, 180, 270, 315]

        for angle in test_angles:
            with self.subTest(angle=angle):
                # Rotate image
                rotated = rotate_image(self.test_image, angle)

                # Verify dimensions
                if angle in [0, 180]:
                    self.assertEqual(rotated.size, self.test_image.size)
                elif angle in [90, 270]:
                    self.assertEqual(rotated.size, (self.test_image.size[1],
                                                  self.test_image.size[0]))
                else:
                    # For arbitrary angles, verify dimensions are sufficient
                    # to contain rotated content
                    angle_rad = math.radians(angle)
                    expected_width = int(abs(self.test_image.size[0] * math.cos(angle_rad)) +
                                      abs(self.test_image.size[1] * math.sin(angle_rad)))
                    expected_height = int(abs(self.test_image.size[0] * math.sin(angle_rad)) +
                                       abs(self.test_image.size[1] * math.cos(angle_rad)))

                    self.assertGreaterEqual(rotated.size[0], expected_width - 1)
                    self.assertGreaterEqual(rotated.size[1], expected_height - 1)

    def test_background_handling(self):
        """Test background color handling during rotation."""
        # Test with different background colors
        backgrounds = [0, 127, 255]
        angle = 45  # Use angle that will create background

        for bg in backgrounds:
            with self.subTest(background=bg):
                rotated = rotate_image(self.test_image, angle, background=bg)

                # Check corners which should be background
                corners = [
                    (0, 0),
                    (0, rotated.size[1]-1),
                    (rotated.size[0]-1, 0),
                    (rotated.size[0]-1, rotated.size[1]-1)
                ]

                for x, y in corners:
                    self.assertEqual(rotated.getpixel((x, y)), bg)

    def test_content_preservation(self):
        """Test that image content is preserved during rotation."""
        # Create test pattern
        pattern = Image.new('L', (50, 50), 255)
        pattern.putpixel((25, 25), 0)  # Center pixel

        # Test 90-degree rotations where we can exactly verify pixel locations
        angles = [90, 180, 270]

        for angle in angles:
            with self.subTest(angle=angle):
                rotated = rotate_image(pattern, angle)

                # Calculate expected position of center pixel
                if angle == 90:
                    expected_pos = (25, 24)
                elif angle == 180:
                    expected_pos = (24, 24)
                else:  # 270
                    expected_pos = (24, 25)

                # Verify center pixel location
                self.assertEqual(rotated.getpixel(expected_pos), 0)

    def test_multiple_transformations(self):
        """Test multiple transformations via prepare_image_for_display."""
        # Test various combinations
        test_cases = [
            {'angle': 45, 'scale': 1.0},
            {'angle': 90, 'scale': 0.5},
            {'angle': 180, 'scale': 2.0},
            {'angle': 30, 'scale': 1.5}
        ]

        for case in test_cases:
            with self.subTest(**case):
                transformed = prepare_image_for_display(
                    self.test_image,
                    angle=case['angle'],
                    scale=case['scale']
                )

                # Verify scaling
                expected_base_width = int(self.test_image.size[0] * case['scale'])
                expected_base_height = int(self.test_image.size[1] * case['scale'])

                if case['angle'] in [0, 180]:
                    self.assertEqual(transformed.size[0], expected_base_width)
                    self.assertEqual(transformed.size[1], expected_base_height)
                elif case['angle'] in [90, 270]:
                    self.assertEqual(transformed.size[0], expected_base_height)
                    self.assertEqual(transformed.size[1], expected_base_width)

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # Test very small angles
        small_angle = rotate_image(self.test_image, 0.5)
        self.assertIsNotNone(small_angle)

        # Test multiple of 360
        full_rotation = rotate_image(self.test_image, 360)
        self.assertImageEqual(full_rotation, self.test_image)

        # Test negative angles
        negative = rotate_image(self.test_image, -90)
        positive = rotate_image(self.test_image, 270)
        self.assertImageEqual(negative, positive)

    def test_image_quality(self):
        """Test image quality preservation during transformation."""
        # Create high contrast test image
        quality_test = Image.new('L', (100, 100), 255)
        for x in range(10):
            for y in range(10):
                quality_test.putpixel((x*10, y*10), 0)

        # Apply multiple transformations
        transformed = prepare_image_for_display(
            quality_test,
            angle=45,
            scale=1.5
        )

        # Calculate image statistics
        orig_stats = self._get_image_stats(quality_test)
        trans_stats = self._get_image_stats(transformed)

        # Verify statistics are reasonably preserved
        self.assertAlmostEqual(orig_stats['mean'], trans_stats['mean'], delta=10)
        self.assertAlmostEqual(orig_stats['std'], trans_stats['std'], delta=10)

    def _get_image_stats(self, image):
        """Calculate basic image statistics."""
        arr = np.array(image)
        return {
            'mean': np.mean(arr),
            'std': np.std(arr),
            'min': np.min(arr),
            'max': np.max(arr)
        }
