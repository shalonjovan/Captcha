# API reference

The public API is intentionally small:

- [`Captcha`](#captcha_forge.facade.Captcha) — choose a type and render.
- [`CaptchaConfig`](#captcha_forge.config.CaptchaConfig) — shared configuration.
- [`CaptchaResult`](#captcha_forge.result.CaptchaResult) — frames, answer,
  metadata, and assets.
- [`create`](#captcha_forge.facade.create) — one-shot helper.
- [`register`](#captcha_forge.registry.register) — add a custom generator.

Frames are OpenCV-style BGR `uint8` arrays with shape `(height, width, 3)`.
Masks used internally are single-channel `uint8` arrays where `0` is transparent
and `255` is opaque.

## Facade

::: captcha_forge.facade.Captcha

::: captcha_forge.facade.create

## Configuration

::: captcha_forge.config.CaptchaConfig

## Result

::: captcha_forge.result.CaptchaResult

## Registry

::: captcha_forge.registry.register

::: captcha_forge.registry.available_types

::: captcha_forge.registry.resolve_type

::: captcha_forge.registry.get_generator_class

## Exceptions

::: captcha_forge.exceptions.CaptchaError

::: captcha_forge.exceptions.ConfigurationError

::: captcha_forge.exceptions.UnknownCaptchaType

::: captcha_forge.exceptions.ExportError

::: captcha_forge.exceptions.GeneratorError

## Base generator

::: captcha_forge.generators.base.BaseGenerator

## Rendering helpers

These functions are public for plugin authors. They are not required for normal
use of the package.

::: captcha_forge.rendering.new_frame

::: captcha_forge.rendering.blit_mask

::: captcha_forge.rendering.blit_image_mask

::: captcha_forge.rendering.blit_mask_onto

::: captcha_forge.rendering.render_text_mask

::: captcha_forge.rendering.GlyphCache

::: captcha_forge.rendering.rotate_mask

::: captcha_forge.rendering.shear_mask

::: captcha_forge.rendering.apply_wave

::: captcha_forge.rendering.add_noise

::: captcha_forge.rendering.add_blobs

::: captcha_forge.rendering.add_speckles

::: captcha_forge.rendering.add_lines

::: captcha_forge.rendering.make_gradient

::: captcha_forge.rendering.add_vignette

::: captcha_forge.rendering.draw_text

::: captcha_forge.rendering.draw_text_centered

::: captcha_forge.rendering.draw_shape

::: captcha_forge.rendering.shape_points

::: captcha_forge.rendering.outline_mask

::: captcha_forge.rendering.make_puzzle_mask

## Colours and fonts

::: captcha_forge.colors.parse_color

::: captcha_forge.colors.to_bgr

::: captcha_forge.colors.blend

::: captcha_forge.colors.luminance

::: captcha_forge.colors.contrasting_text

::: captcha_forge.fonts.resolve_font_face

::: captcha_forge.fonts.font_name

::: captcha_forge.fonts.measure_text

::: captcha_forge.fonts.fit_font_scale

## Export

::: captcha_forge.export.normalise_format

::: captcha_forge.export.format_for_path

::: captcha_forge.export.save_frames

::: captcha_forge.export.encode_image_bytes

::: captcha_forge.export.encode_animation_bytes
